from __future__ import annotations

from typing import Any


DIMENSIONS: dict[str, dict[str, str]] = {
    "big_chinese": {
        "label": "大语文",
        "guidance": "关注词语、修辞、文学表达或故事主题，帮助孩子把语言说清楚。",
    },
    "knowledge": {
        "label": "百科知识",
        "guidance": "补充一个准确、具体、适合儿童理解的小知识。",
    },
    "cultural_understanding": {
        "label": "文化理解",
        "guidance": "连接神话、历史、传统文化、地域文化或人物典故。",
    },
    "logic": {
        "label": "逻辑思维",
        "guidance": "帮助孩子梳理原因、先后、选择、证据和结果。",
    },
    "emotional_understanding": {
        "label": "情绪理解",
        "guidance": "识别人物感受、理解原因，并练习换位思考。",
    },
    "imagination": {
        "label": "想象力",
        "guidance": "保护孩子的创意，展开一个有画面的可能，再说明故事边界。",
    },
    "expression": {
        "label": "语言表达",
        "guidance": "支持描述、复述和观点表达，帮助孩子组织更清楚的句子。",
    },
}


def dimension_label(key: str) -> str:
    return DIMENSIONS.get(key, {}).get("label", key)


def normalize_dimensions(values: list[str] | None) -> list[str]:
    result: list[str] = []
    labels = {item["label"]: key for key, item in DIMENSIONS.items()}
    for value in values or []:
        key = value if value in DIMENSIONS else labels.get(value, value)
        if key in DIMENSIONS and key not in result:
            result.append(key)
    return result


def classify_child_input(text: str) -> dict[str, Any]:
    clean = text.strip()
    if not clean or any(word in clean for word in ("不知道", "不会", "不懂", "没听清")):
        return {"classification": "unknown", "dimensions": ["expression"]}
    if any(word in clean for word in ("伤心", "难过", "害怕", "生气", "委屈", "开心", "孤单")):
        return {
            "classification": "emotion",
            "dimensions": ["emotional_understanding", "expression"],
        }
    if any(word in clean for word in ("如果", "我想", "像", "变成", "发明", "画", "想象")):
        return {"classification": "creative", "dimensions": ["imagination", "expression"]}
    if any(word in clean for word in ("因为", "所以", "先", "然后", "决定", "选择", "为什么", "怎么")):
        return {"classification": "reasoning", "dimensions": ["logic", "expression"]}
    if any(mark in clean for mark in ("什么", "多少", "哪里", "?", "？")):
        return {"classification": "question", "dimensions": ["knowledge", "expression"]}
    return {"classification": "expression", "dimensions": ["expression"]}
