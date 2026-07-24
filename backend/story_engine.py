from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .providers.base import CompanionProvider


class StoryStateError(ValueError):
    pass


@dataclass
class StorySession:
    story: dict[str, Any]
    provider: CompanionProvider
    session_id: str = field(default_factory=lambda: uuid4().hex)
    node_index: int = 0
    sentence_index: int = 0
    state: str = "idle"
    interrupted: bool = False
    interactions: list[dict[str, Any]] = field(default_factory=list)

    @property
    def current_node(self) -> dict[str, Any]:
        return self.story["nodes"][self.node_index]

    def _event(self) -> dict[str, Any]:
        node = self.current_node
        if node["type"] == "story":
            return {
                "type": "story_sentence",
                "node_id": node["id"],
                "sentence_index": self.sentence_index,
                "text": node["sentences"][self.sentence_index],
                "progress": self.progress,
            }
        self.state = "awaiting_input"
        return {
            "type": "interaction_prompt",
            "node_id": node["id"],
            "text": node["prompt"],
            "progress": self.progress,
        }

    @property
    def progress(self) -> int:
        total = sum(max(1, len(n.get("sentences", []))) for n in self.story["nodes"])
        done = sum(max(1, len(n.get("sentences", []))) for n in self.story["nodes"][: self.node_index])
        done += self.sentence_index
        return min(100, round(done / total * 100))

    def start(self) -> list[dict[str, Any]]:
        if self.state != "idle":
            raise StoryStateError("session already started")
        self.state = "playing"
        return [
            {"type": "session_started", "session_id": self.session_id, "story": self.story["title"]},
            self._event(),
        ]

    def sentence_complete(self) -> list[dict[str, Any]]:
        if self.state != "playing":
            raise StoryStateError("sentence_complete is only valid while playing")
        node = self.current_node
        if node["type"] != "story":
            raise StoryStateError("current node is not a story node")
        if self.sentence_index + 1 < len(node["sentences"]):
            self.sentence_index += 1
            return [self._event()]
        return self._advance_node()

    def interrupt(self) -> list[dict[str, Any]]:
        if self.state != "playing" or self.current_node["type"] != "story":
            raise StoryStateError("interrupt is only valid during story playback")
        self.state = "awaiting_input"
        self.interrupted = True
        return [{
            "type": "story_paused",
            "node_id": self.current_node["id"],
            "sentence_index": self.sentence_index,
            "text": "故事暂停了，我在听。",
        }]

    async def submit_message(self, text: str) -> list[dict[str, Any]]:
        if self.state != "awaiting_input":
            raise StoryStateError("user_message is only valid while awaiting input")
        node = self.current_node
        context = (
            node["sentences"][self.sentence_index]
            if node["type"] == "story"
            else node["prompt"]
        )
        answer = await self.provider.answer(text, context)
        self.interactions.append({
            "kind": "interrupt" if self.interrupted else "guided",
            "node_id": node["id"],
            "child_text": text,
            "assistant_text": answer,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        self.state = "answering"
        return [{"type": "assistant_answer", "text": answer}]

    def answer_complete(self) -> list[dict[str, Any]]:
        if self.state != "answering":
            raise StoryStateError("answer_complete is only valid after an answer")
        if self.interrupted:
            self.interrupted = False
            self.state = "playing"
            return [{"type": "story_resumed", "text": "我们回到刚才那一句。"}, self._event()]
        return self._advance_node()

    def _advance_node(self) -> list[dict[str, Any]]:
        self.node_index += 1
        self.sentence_index = 0
        if self.node_index >= len(self.story["nodes"]):
            self.state = "ended"
            return [{"type": "story_end", "session_id": self.session_id, "progress": 100}]
        self.state = "playing"
        return [self._event()]

    def report(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "story_id": self.story["id"],
            "story_title": self.story["title"],
            "status": self.state,
            "progress": 100 if self.state == "ended" else self.progress,
            "interaction_count": len(self.interactions),
            "interactions": self.interactions,
            "privacy_note": "公开演示模式仅在进程内保存会话，服务重启后清空。",
        }
