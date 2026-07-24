from typing import Protocol


class CompanionProvider(Protocol):
    """LLM/TTS/ASR adapters only need to implement this product-level contract."""

    async def answer(self, child_text: str, story_context: str) -> str:
        ...
