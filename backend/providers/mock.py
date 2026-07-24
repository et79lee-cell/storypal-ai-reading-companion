from typing import Any

from ..capabilities import dimension_label


class MockCompanionProvider:
    """Deterministic local provider used for demos and tests—no cloud key required."""

    async def answer(
        self,
        child_text: str,
        story_context: str,
        interaction_context: dict[str, Any] | None = None,
    ) -> str:
        text = child_text.strip()
        context = interaction_context or {}
        classification = context.get("classification", "expression")
        dimensions = context.get("dimensions") or ["expression"]
        dimension = dimension_label(dimensions[0])
        if not text:
            return "我在听。你可以再说一次吗？"
        if classification == "unknown" and context.get("scaffold_prompt"):
            return f"没关系，我们把问题变小一点：{context['scaffold_prompt']}"
        if classification == "emotion":
            return f"你注意到了这种感受。结合刚才的情节，{story_context}，人物有这样的心情是说得通的。"
        if classification == "creative":
            return f"这个想法很有画面感：{text}。我们先保留这个脑洞，再看看故事里的角色会怎么做。"
        if classification in {"reasoning", "question"}:
            return f"我们沿着你的问题想一想。刚才的线索是：{story_context}。可以从原因、行动和结果一步步找答案。"
        return f"我听到你的想法了：{text}。这次互动关注的是{dimension}，我们继续看看故事会怎样发展。"
