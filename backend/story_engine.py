from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from .capabilities import classify_child_input, dimension_label
from .memory import SessionMemory
from .providers.base import CompanionProvider
from .question_planner import QuestionPlan, QuestionPlanner


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
    memory: SessionMemory | None = None
    question_planner: QuestionPlanner = field(default_factory=QuestionPlanner)
    active_question_plan: QuestionPlan | None = None

    def __post_init__(self) -> None:
        if self.memory is None:
            self.memory = SessionMemory(session_id=self.session_id)

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
        self.interrupted = False
        self.active_question_plan = self.question_planner.plan(node, self.memory)
        plan = self.active_question_plan
        return {
            "type": "proactive_question",
            "interaction_module": "ai_proactive_question",
            "node_id": node["id"],
            "text": plan.prompt,
            "question_design": plan.public_dict(),
            "dimension_labels": [dimension_label(key) for key in plan.dimensions],
            "skip_allowed": True,
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
        self.active_question_plan = None
        return [{
            "type": "story_paused",
            "interaction_module": "user_interrupt_question",
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
            else self.active_question_plan.prompt
        )
        input_design = classify_child_input(text)
        interaction_module = (
            "user_interrupt_question" if self.interrupted else "ai_proactive_question"
        )
        dimensions = (
            input_design["dimensions"]
            if self.interrupted
            else self.active_question_plan.dimensions
        )
        scaffold_prompt = (
            self.active_question_plan.scaffold_prompt
            if self.active_question_plan
            else "可以先说说你注意到的一个细节。"
        )
        interaction_context = {
            **self.memory.build_context(max_entries=3),
            "interaction_module": interaction_module,
            "classification": input_design["classification"],
            "dimensions": dimensions,
            "scaffold_prompt": scaffold_prompt,
        }
        answer = await self.provider.answer(text, context, interaction_context)
        entry = self.memory.record(
            interaction_module=interaction_module,
            node_id=node["id"],
            child_text=text,
            assistant_text=answer,
            dimensions=dimensions,
            classification=input_design["classification"],
            context_excerpt=context,
        )
        self.state = "answering"
        return [{
            "type": "assistant_answer",
            "text": answer,
            "interaction_module": interaction_module,
            "dimension_labels": entry.public_dict()["dimension_labels"],
        }]

    def skip_proactive_question(self) -> list[dict[str, Any]]:
        if (
            self.state != "awaiting_input"
            or self.interrupted
            or self.current_node["type"] == "story"
            or self.active_question_plan is None
        ):
            raise StoryStateError("skip is only valid for an active proactive question")
        plan = self.active_question_plan
        self.memory.record(
            interaction_module="ai_proactive_question",
            node_id=self.current_node["id"],
            child_text="",
            assistant_text="",
            dimensions=plan.dimensions,
            classification="skipped",
            context_excerpt=plan.prompt,
            status="skipped",
        )
        self.active_question_plan = None
        return [{"type": "proactive_question_skipped"}, *self._advance_node()]

    def answer_complete(self) -> list[dict[str, Any]]:
        if self.state != "answering":
            raise StoryStateError("answer_complete is only valid after an answer")
        if self.interrupted:
            self.interrupted = False
            self.state = "playing"
            return [{"type": "story_resumed", "text": "我们回到刚才那一句。"}, self._event()]
        self.active_question_plan = None
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
        memory_report = self.memory.report()
        return {
            "session_id": self.session_id,
            "story_id": self.story["id"],
            "story_title": self.story["title"],
            "status": self.state,
            "progress": 100 if self.state == "ended" else self.progress,
            "interaction_count": memory_report["interaction_count"],
            "skipped_count": memory_report["skipped_count"],
            "module_counts": memory_report["module_counts"],
            "dimension_coverage": memory_report["dimension_coverage"],
            "interactions": memory_report["interactions"],
            "memory": {
                "retention_scope": memory_report["retention_scope"],
                "entry_count": len(memory_report["interactions"]),
            },
            "privacy_note": memory_report["privacy_note"],
        }
