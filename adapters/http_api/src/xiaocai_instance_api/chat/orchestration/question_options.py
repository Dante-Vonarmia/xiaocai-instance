from __future__ import annotations

from typing import Any


def _to_text(value: object) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def normalize_question_options(options: object) -> list[dict[str, Any]]:
    """Normalize chooser options into the object shape consumed by chat-core."""
    if not isinstance(options, list):
        return []

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, option in enumerate(options):
        if isinstance(option, str):
            label = _to_text(option)
            item: dict[str, Any] = {}
        elif isinstance(option, dict):
            item = dict(option)
            label = (
                _to_text(item.get("label"))
                or _to_text(item.get("text"))
                or _to_text(item.get("value"))
                or _to_text(item.get("key"))
            )
        else:
            continue

        if not label:
            continue
        value = _to_text(item.get("value")) or label
        key = _to_text(item.get("key")) or value or f"option_{index + 1}"
        dedupe_key = f"{key}:{label}:{value}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        normalized.append({**item, "key": key, "label": label, "text": label, "value": value})
    return normalized


def normalize_question_payload(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    normalized = dict(payload)
    normalized["options"] = normalize_question_options(normalized.get("options"))
    return normalized
