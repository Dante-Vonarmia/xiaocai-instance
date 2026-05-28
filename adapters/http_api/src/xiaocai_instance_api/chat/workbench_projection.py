"""Intake workbench projection for FLARE-native pending contracts."""

from __future__ import annotations

import json
from typing import Any

from xiaocai_instance_api.chat.orchestration.field_candidates import normalize_candidate_payload
from xiaocai_instance_api.chat.orchestration.question_options import normalize_question_options


INTAKE_MODE_KEY = "requirement_intake"


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


def _field_item(field_key: str, value: str = "", status: str = "missing") -> dict[str, object]:
    return {
        "field_key": field_key,
        "field_label": field_key,
        "value": value,
        "status": status,
    }


def _current_question(pending_contract: dict[str, Any]) -> dict[str, object]:
    question = _as_dict(pending_contract.get("current_question")) or _as_dict(pending_contract.get("question"))
    field_key = _to_text(question.get("field_key"))
    question_text = _to_text(question.get("question_text"))
    if not field_key or not question_text:
        return {}
    return {
        "field_key": field_key,
        "field_label": _to_text(question.get("field_label")) or field_key,
        "question_text": question_text,
        "options": normalize_question_options(question.get("options")),
    }


def _merge_candidate_payloads(*payloads: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()

    for payload in payloads:
        normalized = normalize_candidate_payload(payload)
        for status_key, target in (("candidate_fields", candidates), ("rejected_candidates", rejected)):
            for item in normalized[status_key]:
                dedupe_key = (
                    status_key,
                    _to_text(item.get("field_key")),
                    _to_text(item.get("value")),
                    _to_text(item.get("source")),
                )
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                target.append(item)

    return {
        "candidate_fields": candidates,
        "rejected_candidates": rejected,
    }


def _collected_fields(pending: dict[str, Any]) -> list[dict[str, object]]:
    collected: list[dict[str, object]] = []
    seen: set[str] = set()

    for item in _as_list(pending.get("collected")):
        data = _as_dict(item)
        field_key = _to_text(data.get("field_key")) or _to_text(data.get("field")) or _to_text(data.get("key"))
        value = _to_text(data.get("value"))
        if field_key and value and field_key not in seen:
            seen.add(field_key)
            collected.append(_field_item(field_key, value, _to_text(data.get("status")) or "collected"))

    for source_key in ("confirmed_fields", "fields"):
        for field_key, raw_value in _as_dict(pending.get(source_key)).items():
            value = _to_text(raw_value)
            if field_key and value and field_key not in seen:
                seen.add(str(field_key))
                collected.append(_field_item(str(field_key), value, "collected"))

    return collected


def _coverage(pending: dict[str, Any], collected_count: int, missing_count: int) -> float:
    for key in ("required_coverage", "total_coverage", "progress"):
        value = pending.get(key)
        if isinstance(value, (int, float)):
            return max(0.0, min(1.0, float(value)))
    total = collected_count + missing_count
    return collected_count / total if total else 0.0


def _markdown(
    collected: list[dict[str, object]],
    missing_fields: list[str],
    candidates: list[dict[str, Any]],
) -> str:
    lines = ["# 需求梳理草稿", "", "## 已确认信息"]
    if collected:
        lines.extend(f"- {item['field_label']}: {item['value']}" for item in collected)
    else:
        lines.append("- 暂无")
    if candidates:
        lines.extend(["", "## 候选信息（待确认）"])
        lines.extend(
            f"- {item['field_key']}: {item['value']}"
            for item in candidates
            if _to_text(item.get("field_key")) and _to_text(item.get("value"))
        )
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
    candidate_context: dict[str, Any] | None = None,
) -> dict[str, object] | None:
    _ = user_message, candidate_context
    if mode != INTAKE_MODE_KEY and mode != "requirement_canvas":
        return None
    if pending_contract is None:
        return None

    pending = dict(pending_contract)
    candidate_payload = _merge_candidate_payloads(pending)
    candidate_fields = candidate_payload["candidate_fields"]
    rejected_candidates = candidate_payload["rejected_candidates"]
    collected = _collected_fields(pending)
    collected_keys = {str(item["field_key"]) for item in collected}
    missing_fields = _dedupe([
        field
        for field in (_to_text(item) for item in _as_list(pending.get("missing_fields")))
        if field and field not in collected_keys
    ])
    missing = [_field_item(field) for field in missing_fields]
    current_question = _current_question(pending)
    next_actions = _as_list(pending.get("next_actions"))
    mode_state = _to_text(pending.get("mode_state")) or _to_text(pending.get("current_stage")) or "pending"
    progress = _coverage(pending, len(collected), len(missing_fields))
    ready_for_submit = bool(pending.get("ready_for_submit")) if "ready_for_submit" in pending else not missing_fields

    enriched_pending = {
        **pending,
        "mode_key": INTAKE_MODE_KEY,
        "mode_state": mode_state,
        "missing_fields": missing_fields,
        "current_question": current_question,
        "question": current_question,
        "next_actions": next_actions,
        "candidate_fields": candidate_fields,
        "rejected_candidates": rejected_candidates,
        "required_coverage": progress,
        "total_coverage": progress,
        "active_collecting": bool(missing_fields),
        "ready_for_submit": ready_for_submit,
        "has_active_question": bool(current_question),
    }

    canvas_state = {
        "session_id": session_id,
        "mode_key": INTAKE_MODE_KEY,
        "mode_state": mode_state,
        "progress": progress,
        "collected": collected,
        "candidates": candidate_fields,
        "candidate_fields": candidate_fields,
        "rejected_candidates": rejected_candidates,
        "missing": missing,
        "current_question": current_question,
        "readiness": {
            "required_coverage": progress,
            "total_coverage": progress,
            "ready_for_submit": ready_for_submit,
            "missing_fields": missing_fields,
        },
        "next_actions": next_actions,
        "versions": [{"content": _markdown(collected, missing_fields, candidate_fields)}],
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
