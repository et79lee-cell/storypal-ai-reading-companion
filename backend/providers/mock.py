class MockCompanionProvider:
    """Deterministic local provider used for demos and tests—no cloud key required."""

    async def answer(self, child_text: str, story_context: str) -> str:
        text = child_text.strip()
        if not text:
            return "我在听。你可以再说一次吗？"
        if any(word in text for word in ("为什么", "怎么", "什么")):
            return f"这是个很好的问题。结合刚才的故事，我想：{story_context}。你也可以说说自己的猜想。"
        return f"我听到你的想法了：{text}。这个发现很有意思，我们继续看看故事里会发生什么。"
