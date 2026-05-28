from __future__ import annotations

from typing import Any

from xiaocai_instance_api.chat.orchestration.contract_loader import load_contracts


CANDIDATE_LIST_KEYS = (
    "candidate_fields",
    "field_candidates",
    "extracted_fields",
    "structured_fields",
)
CANDIDATE_NESTED_KEYS = ("intake_result", "result", "payload", "metadata", "canvas_state")
def _to_text(value: object) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _candidate_items(payload: object) -> list[Any]:
    data = _as_dict(payload)
    if not data:
        return []

    items: list[Any] = []
    for key in CANDIDATE_LIST_KEYS:
        items.extend(_as_list(data.get(key)))
    for key in CANDIDATE_NESTED_KEYS:
        nested = data.get(key)
        if isinstance(nested, dict) and nested is not data:
            items.extend(_candidate_items(nested))
    return items


def _raw_field_key(item: dict[str, Any]) -> str:
    for key in ("field_key", "key", "field", "name", "raw_field_key"):
        value = _to_text(item.get(key))
        if value:
            return value
    return ""


def _raw_value(item: dict[str, Any]) -> str:
    for key in ("normalized_value", "value", "raw_value", "text"):
        value = _to_text(item.get(key))
        if value:
            return value
    return ""


def _canonical_field_key(raw_key: str) -> tuple[str, str]:
    contracts = load_contracts()
    if raw_key in contracts.field_metadata:
        return raw_key, "canonical"

    alias = contracts.field_aliases.get(raw_key)
    canonical_fields = _as_list((alias or {}).get("canonical_fields"))
    if len(canonical_fields) == 1:
        canonical = _to_text(canonical_fields[0])
        if canonical in contracts.field_metadata:
            return canonical, "alias"
    if len(canonical_fields) > 1:
        return "", "multi_field_alias_requires_split"
    return "", "unknown_field"


def _candidate_status(item: dict[str, Any]) -> str:
    status = _to_text(item.get("status")) or _to_text(item.get("normalization_status"))
    return "rejected" if status == "rejected" else "needs_confirmation"


def _candidate_source(item: dict[str, Any]) -> str:
    return _to_text(item.get("source")) or _to_text(item.get("origin")) or "model_inferred"


def _normalize_candidate(item: object) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    data = _as_dict(item)
    if not data:
        return None, None

    raw_key = _raw_field_key(data)
    value = _raw_value(data)
    field_key, key_status = _canonical_field_key(raw_key)
    rejection_reason = "" if field_key else key_status
    if field_key and not value:
        rejection_reason = "empty_value"

    base = {
        "field_key": field_key or raw_key,
        "raw_field_key": raw_key,
        "value": value,
        "source": _candidate_source(data),
        "confidence": data.get("confidence"),
        "evidence": data.get("evidence"),
        "normalization_status": "rejected" if rejection_reason else _candidate_status(data),
    }
    if key_status == "alias":
        base["canonicalization"] = "alias"

    if rejection_reason:
        return None, {**base, "rejection_reason": rejection_reason}
    return base, None


def normalize_candidate_payload(payload: object) -> dict[str, list[dict[str, Any]]]:
    """Normalize model/FLARE field candidates before projection or state usage."""
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for item in _candidate_items(payload):
        candidate, rejection = _normalize_candidate(item)
        row = candidate or rejection
        if not row:
            continue
        dedupe_key = (
            _to_text(row.get("field_key")),
            _to_text(row.get("value")),
            _to_text(row.get("source")),
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        if candidate:
            candidates.append(candidate)
        elif rejection:
            rejected.append(rejection)

    return {
        "candidate_fields": candidates,
        "rejected_candidates": rejected,
    }
