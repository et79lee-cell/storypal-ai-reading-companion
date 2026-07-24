import unittest

from backend.memory import InMemoryMemoryRepository, SessionMemory
from backend.question_planner import QuestionPlanner


NODE = {
    "id": "question-node",
    "type": "proactive_question",
    "question_design": {
        "trigger_reason": "剧情自然停顿处",
        "follow_up_policy": "one_scaffold_then_continue",
        "candidates": [
            {
                "question_id": "logic-question",
                "prompt": "为什么大家要一起帮忙？",
                "primary_dimension": "logic",
                "dimensions": ["logic", "expression"],
                "question_type": "cause_and_effect",
                "learning_goal": "梳理因果关系。",
                "scaffold_prompt": "先说说每个人做了什么。",
            },
            {
                "question_id": "emotion-question",
                "prompt": "小星星现在可能是什么心情？",
                "primary_dimension": "emotional_understanding",
                "dimensions": ["emotional_understanding", "expression"],
                "question_type": "emotion_and_reason",
                "learning_goal": "理解角色情绪。",
                "scaffold_prompt": "可以从害怕或着急里选一个。",
            },
        ],
    },
}


class MemoryAndPlannerTests(unittest.TestCase):
    def test_planner_uses_memory_to_avoid_repeating_dimension(self):
        memory = SessionMemory("session-1")
        memory.record(
            interaction_module="ai_proactive_question",
            node_id="previous",
            child_text="因为大家会的事情不同",
            assistant_text="你梳理出了原因。",
            dimensions=["logic"],
            classification="reasoning",
            context_excerpt="大家一起帮忙。",
        )
        plan = QuestionPlanner().plan(NODE, memory)
        self.assertEqual(plan.primary_dimension, "emotional_understanding")
        self.assertIn("尚未出现", plan.selection_reason)

    def test_memory_context_contains_recent_evidence_without_score(self):
        memory = SessionMemory("session-2")
        memory.record(
            interaction_module="user_interrupt_question",
            node_id="forest",
            child_text="星星为什么会掉下来？",
            assistant_text="我们沿着线索想一想。",
            dimensions=["logic", "expression"],
            classification="reasoning",
            context_excerpt="风把星星吹离了轨道。",
        )
        context = memory.build_context()
        self.assertEqual(
            context["recent_interactions"][0]["child_text"],
            "星星为什么会掉下来？",
        )
        self.assertNotIn("score", context)
        self.assertEqual(context["retention_scope"], "session_only")

    def test_repository_supports_immediate_deletion(self):
        repository = InMemoryMemoryRepository()
        repository.create_session("session-3")
        self.assertIsNotNone(repository.get_session("session-3"))
        repository.delete_session("session-3")
        self.assertIsNone(repository.get_session("session-3"))


if __name__ == "__main__":
    unittest.main()
