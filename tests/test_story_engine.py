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

    async def test_complete_story_and_report_guided_interactions(self):
        session = self.make_session()
        events = session.start()
        guard = 0
        while events[-1]["type"] != "story_end":
            guard += 1
            self.assertLess(guard, 30)
            event = events[-1]
            if event["type"] == "story_sentence":
                events = session.sentence_complete()
            elif event["type"] == "interaction_prompt":
                await session.submit_message("可以请朋友一起想办法")
                events = session.answer_complete()
            else:
                self.fail(f"unexpected event {event}")
        report = session.report()
        self.assertEqual(report["status"], "ended")
        self.assertEqual(report["progress"], 100)
        self.assertEqual(report["interaction_count"], 2)

    def test_rejects_out_of_order_message(self):
        session = self.make_session()
        with self.assertRaises(StoryStateError):
            session.sentence_complete()


if __name__ == "__main__":
    unittest.main()
