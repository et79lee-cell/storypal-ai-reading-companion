from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .capabilities import dimension_label, normalize_dimensions
from .memory import SessionMemory


@dataclass(frozen=True)
class QuestionPlan:
    question_id: str
    prompt: str
    primary_dimension: str
    dimensions: list[str]
    question_type: str
    learning_goal: str
    trigger_reason: str
    scaffold_prompt: str
    follow_up_policy: str
    selection_reason: str

    def public_dict(self) -> dict[str, Any]:
        item = asdict(self)
        item["dimension_labels"] = [dimension_label(key) for key in self.dimensions]
        return item


class QuestionPlanner:
    """Selects a designed proactive question using session dimension coverage."""

    def plan(self, node: dict[str, Any], memory: SessionMemory) -> QuestionPlan:
        design = node.get("question_design") or {}
        candidates = design.get("candidates") or []
        if not candidates:
            candidates = [{
                "question_id": node.get("id", "proactive-question"),
                "prompt": node.get("prompt", "说说你的想法吧。"),
                "primary_dimension": "expression",
                "dimensions": ["expression"],
                "question_type": "open_expression",
                "learning_goal": "鼓励孩子表达与故事相关的想法。",
                "scaffold_prompt": "可以先说一个你注意到的细节。",
            }]

        coverage = memory.dimension_counts(interaction_module="ai_proactive_question")
        indexed = list(enumerate(candidates))
        _, selected = min(
            indexed,
            key=lambda pair: (
                coverage.get(pair[1].get("primary_dimension", "expression"), 0),
                pair[0],
            ),
        )
        primary = selected.get("primary_dimension", "expression")
        dimensions = normalize_dimensions(selected.get("dimensions") or [primary])
        if primary not in dimensions:
            dimensions.insert(0, primary)
        seen = coverage.get(primary, 0)
        reason = (
            f"优先覆盖本次会话尚未出现的{dimension_label(primary)}维度"
            if seen == 0
            else f"当前节点候选中{dimension_label(primary)}维度的会话覆盖次数较少"
        )
        return QuestionPlan(
            question_id=selected.get("question_id", node.get("id", "proactive-question")),
            prompt=selected.get("prompt", node.get("prompt", "说说你的想法吧。")),
            primary_dimension=primary,
            dimensions=dimensions,
            question_type=selected.get("question_type", "open_expression"),
            learning_goal=selected.get("learning_goal", "支持开放表达。"),
            trigger_reason=design.get("trigger_reason", "剧情自然停顿处"),
            scaffold_prompt=selected.get("scaffold_prompt", "可以先说一个你注意到的细节。"),
            follow_up_policy=design.get("follow_up_policy", "one_scaffold_then_continue"),
            selection_reason=reason,
        )
