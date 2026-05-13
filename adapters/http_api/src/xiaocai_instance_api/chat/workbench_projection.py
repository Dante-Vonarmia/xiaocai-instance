"""梳理工作台投影 - FLARE chat-core canvas contract."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from xiaocai_instance_api.chat.orchestration.contract_loader import load_contracts
from xiaocai_instance_api.chat.orchestration.extractor import extract_slots


INTAKE_MODE_KEY = "requirement_intake"
DEFAULT_REQUIRED_FIELDS = ["采购目的", "使用场景", "一级品类", "二级品类", "交付地点"]


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _to_text(value: object) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = _to_text(item)
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


@lru_cache(maxsize=1)
def _required_fields() -> list[str]:
    try:
        fields = load_contracts().stage_required.get("requirement-collection", [])
    except Exception:
        fields = []
    return _dedupe([*(fields or []), *DEFAULT_REQUIRED_FIELDS])


def _field_item(field_key: str, value: str = "", status: str = "missing") -> dict[str, object]:
    return {
        "field_key": field_key,
        "field_label": field_key,
        "value": value,
        "status": status,
    }


def _current_question(pending_contract: dict[str, Any], missing_fields: list[str]) -> dict[str, object]:
    question = _as_dict(pending_contract.get("current_question")) or _as_dict(pending_contract.get("question"))
    field_key = _to_text(question.get("field_key"))
    if field_key and field_key in missing_fields:
        return {
            "field_key": field_key,
            "field_label": _to_text(question.get("field_label")) or field_key,
            "question_text": _to_text(question.get("question_text")) or f"请补充字段：{field_key}",
            "options": _as_list(question.get("options")),
        }
    if missing_fields:
        field = missing_fields[0]
        return {
            "field_key": field,
            "field_label": field,
            "question_text": f"请补充字段：{field}",
            "options": [],
        }
    return {}


def _markdown(collected: list[dict[str, object]], missing_fields: list[str]) -> str:
    lines = ["# 需求梳理草稿", "", "## 已识别信息"]
    if collected:
        lines.extend(f"- {item['field_label']}: {item['value']}" for item in collected)
    else:
        lines.append("- 暂未识别到结构化字段")
    lines.extend(["", "## 待补充信息"])
    if missing_fields:
        lines.extend(f"- {field}" for field in missing_fields)
    else:
        lines.append("- 暂无")
    return "\n".join(lines)


def projection_key(payload: dict[str, object]) -> str:
    """Stable key for de-duplicating repeated stream projection events."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


def build_intake_workbench_projection(
    *,
    pending_contract: dict[str, Any] | None,
    mode: str | None,
    session_id: str,
    user_message: str,
) -> dict[str, object] | None:
    if mode != INTAKE_MODE_KEY and mode != "requirement_canvas":
        return None

    pending = dict(pending_contract or {})
    slots = extract_slots(user_message)
    required = _required_fields()
    collected = [
        _field_item(field, slots[field], "collected")
        for field in required
        if _to_text(slots.get(field))
    ]
    collected_keys = {str(item["field_key"]) for item in collected}
    pending_missing = [_to_text(item) for item in _as_list(pending.get("missing_fields"))]
    missing_fields = _dedupe([
        *(field for field in pending_missing if field not in collected_keys),
        *(field for field in required if field not in collected_keys),
    ])
    missing = [_field_item(field) for field in missing_fields]
    current_question = _current_question(pending, missing_fields)
    progress = len(collected) / max(1, len(required))
    next_actions = _as_list(pending.get("next_actions"))
    mode_state = _to_text(pending.get("current_stage")) or "collecting"

    enriched_pending = {
        **pending,
        "mode_key": INTAKE_MODE_KEY,
        "mode_state": mode_state,
        "missing_fields": missing_fields,
        "current_question": current_question,
        "question": current_question,
        "next_actions": next_actions,
        "required_coverage": progress,
        "total_coverage": progress,
        "active_collecting": bool(missing_fields),
        "ready_for_submit": not missing_fields,
        "has_active_question": bool(current_question),
    }

    canvas_state = {
        "session_id": session_id,
        "mode_key": INTAKE_MODE_KEY,
        "mode_state": mode_state,
        "progress": progress,
        "collected": collected,
        "missing": missing,
        "current_question": current_question,
        "readiness": {
            "required_coverage": progress,
            "total_coverage": progress,
            "ready_for_submit": not missing_fields,
            "missing_fields": missing_fields,
        },
        "next_actions": next_actions,
        "versions": [{"content": _markdown(collected, missing_fields)}],
    }

    return {
        "pending_contract": enriched_pending,
        "plan_payload": enriched_pending,
        "canvas_payload": {
            "type": "canvas_state",
            "mode_key": INTAKE_MODE_KEY,
            "mode_state": mode_state,
            "ui_signal": {"active_tab": "requirement", "open_canvas_panel": True},
            "canvas_state": canvas_state,
        },
    }
