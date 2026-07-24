import json
import unittest
from pathlib import Path

from backend.providers import MockCompanionProvider
from backend.story_engine import StorySession, StoryStateError


STORY = json.loads(
    (Path(__file__).parents[1] / "stories" / "lost-starlight.json").read_text(encoding="utf-8")
)


class StorySessionTests(unittest.IsolatedAsyncioTestCase):
    def make_session(self) -> StorySession:
        return StorySession(STORY, MockCompanionProvider(), session_id="test-session")

    async def test_interrupt_answers_and_resumes_same_sentence(self):
        session = self.make_session()
        session.start()
        before = (session.node_index, session.sentence_index)
        self.assertEqual(session.interrupt()[0]["type"], "story_paused")
        answer = await session.submit_message("为什么星星会掉下来？")
        self.assertEqual(answer[0]["type"], "assistant_answer")
        resumed = session.answer_complete()
        self.assertEqual([event["type"] for event in resumed], ["story_resumed", "story_sentence"])
        self.assertEqual((session.node_index, session.sentence_index), before)

    async def test_complete_story_and_report_proactive_questions(self):
        session = self.make_session()
        events = session.start()
        guard = 0
        while events[-1]["type"] != "story_end":
            guard += 1
            self.assertLess(guard, 30)
            event = events[-1]
            if event["type"] == "story_sentence":
                events = session.sentence_complete()
            elif event["type"] == "proactive_question":
                await session.submit_message("可以请朋友一起想办法")
                events = session.answer_complete()
            else:
                self.fail(f"unexpected event {event}")
        report = session.report()
        self.assertEqual(report["status"], "ended")
        self.assertEqual(report["progress"], 100)
        self.assertEqual(report["interaction_count"], 2)
        self.assertEqual(report["module_counts"]["ai_proactive_question"], 2)
        self.assertTrue(report["dimension_coverage"])
        self.assertEqual(report["memory"]["retention_scope"], "session_only")

    def test_rejects_out_of_order_message(self):
        session = self.make_session()
        with self.assertRaises(StoryStateError):
            session.sentence_complete()

    async def test_interrupt_is_recorded_as_separate_module(self):
        session = self.make_session()
        session.start()
        session.interrupt()
        await session.submit_message("为什么星星会掉下来？")
        session.answer_complete()
        report = session.report()
        entry = report["interactions"][0]
        self.assertEqual(entry["interaction_module"], "user_interrupt_question")
        self.assertIn("逻辑思维", entry["dimension_labels"])
        self.assertEqual(report["module_counts"]["user_interrupt_question"], 1)

    def test_proactive_question_can_be_skipped(self):
        session = self.make_session()
        events = session.start()
        while events[-1]["type"] == "story_sentence":
            events = session.sentence_complete()
        self.assertEqual(events[-1]["type"], "proactive_question")
        skipped = session.skip_proactive_question()
        self.assertEqual(skipped[0]["type"], "proactive_question_skipped")
        self.assertEqual(session.report()["skipped_count"], 1)


if __name__ == "__main__":
    unittest.main()
