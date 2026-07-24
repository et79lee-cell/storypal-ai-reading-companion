from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from .capabilities import dimension_label, normalize_dimensions


@dataclass(frozen=True)
class MemoryEntry:
    interaction_id: str
    interaction_module: str
    node_id: str
    child_text: str
    assistant_text: str
    dimensions: list[str]
    classification: str
    context_excerpt: str
    status: str = "answered"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def public_dict(self) -> dict[str, Any]:
        item = asdict(self)
        item["dimension_labels"] = [dimension_label(key) for key in self.dimensions]
        item["dimensions_text"] = " × ".join(item["dimension_labels"])
        return item


@dataclass
class SessionMemory:
    """Consent-safe demo memory: session-scoped, in-process, and evidence based."""

    session_id: str
    retention_scope: str = "session_only"
    entries: list[MemoryEntry] = field(default_factory=list)

    def record(
        self,
        *,
        interaction_module: str,
        node_id: str,
        child_text: str,
        assistant_text: str,
        dimensions: list[str],
        classification: str,
        context_excerpt: str,
        status: str = "answered",
    ) -> MemoryEntry:
        entry = MemoryEntry(
            interaction_id=uuid4().hex,
            interaction_module=interaction_module,
            node_id=node_id,
            child_text=child_text.strip()[:240],
            assistant_text=assistant_text.strip()[:500],
            dimensions=normalize_dimensions(dimensions),
            classification=classification,
            context_excerpt=context_excerpt.strip()[:180],
            status=status,
        )
        self.entries.append(entry)
        return entry

    def dimension_counts(self, *, interaction_module: str | None = None) -> Counter[str]:
        counts: Counter[str] = Counter()
        for entry in self.entries:
            if entry.status != "answered":
                continue
            if interaction_module and entry.interaction_module != interaction_module:
                continue
            counts.update(entry.dimensions)
        return counts

    def build_context(self, *, max_entries: int = 3) -> dict[str, Any]:
        recent = [
            {
                "interaction_module": entry.interaction_module,
                "child_text": entry.child_text,
                "dimensions": entry.dimensions,
                "classification": entry.classification,
            }
            for entry in self.entries[-max_entries:]
            if entry.status == "answered"
        ]
        return {
            "retention_scope": self.retention_scope,
            "recent_interactions": recent,
            "dimension_counts": dict(self.dimension_counts()),
            "safety_note": "Only observable interaction evidence; no diagnosis or ability score.",
        }

    def report(self) -> dict[str, Any]:
        module_counts = Counter(entry.interaction_module for entry in self.entries)
        dimensions = self.dimension_counts()
        answered_count = sum(1 for entry in self.entries if entry.status == "answered")
        skipped_count = sum(1 for entry in self.entries if entry.status == "skipped")
        return {
            "retention_scope": self.retention_scope,
            "interaction_count": answered_count,
            "skipped_count": skipped_count,
            "module_counts": dict(module_counts),
            "dimension_coverage": [
                {"key": key, "label": dimension_label(key), "evidence_count": count}
                for key, count in dimensions.most_common()
            ],
            "interactions": [entry.public_dict() for entry in self.entries],
            "privacy_note": "只保存本次会话中的可观察互动事实；不生成儿童能力或心理诊断。",
        }


class MemoryRepository(Protocol):
    def create_session(self, session_id: str) -> SessionMemory:
        ...

    def get_session(self, session_id: str) -> SessionMemory | None:
        ...

    def delete_session(self, session_id: str) -> None:
        ...


class InMemoryMemoryRepository:
    """Public demo repository. Deliberately has no cross-session persistence."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionMemory] = {}

    def create_session(self, session_id: str) -> SessionMemory:
        memory = SessionMemory(session_id=session_id)
        self._sessions[session_id] = memory
        return memory

    def get_session(self, session_id: str) -> SessionMemory | None:
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
