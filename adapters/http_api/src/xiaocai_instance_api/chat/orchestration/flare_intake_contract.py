"""FLARE-native intake contract projection for xiaocai procurement context."""

from __future__ import annotations

from typing import Any

from xiaocai_instance_api.chat.orchestration.contract_loader import OrchestrationContracts, load_contracts

INTAKE_MODES = {"requirement_canvas", "requirement_intake"}
FIELD_ACTION_PRIORITY = {
    "ask_in_chat": "required",
    "suggest_not_force": "recommended",
    "defer_to_canvas": "optional",
}
FIELD_ACTION_CRITICALITY = {
    "ask_in_chat": ("important", 0.85),
    "suggest_not_force": ("important", 0.5),
    "defer_to_canvas": ("supplementary", 0.25),
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _is_empty(value: Any) -> bool:
    return value in (None, "", [], {})


def _is_intake_mode(mode: str | None) -> bool:
    normalized = _text(mode)
    return normalized in INTAKE_MODES or normalized.startswith("requirement_intake")


def _dedupe(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = _text(value)
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _option(label: str, value: str | None = None) -> dict[str, str]:
    text = _text(label)
    option_value = _text(value) or text
    return {"key": option_value, "label": text, "text": text, "value": option_value}


def _metadata_for(contracts: OrchestrationContracts, field_key: str) -> dict[str, str]:
    return contracts.field_metadata.get(field_key, {})


def _enum_options_from_format(value: str) -> list[dict[str, str]]:
    raw = _text(value)
    if "/" not in raw:
        return []
    if any(marker in raw for marker in ("描述", "姓名", "地址", "文本", "链接", "格式")):
        return []
    return [_option(item) for item in raw.split("/") if _text(item)]


def _infer_value_type(field_key: str) -> str:
    if field_key == "数量":
        return "quantity"
    if field_key == "预算金额":
        return "money"
    if field_key == "交付时间":
        return "date"
    if field_key in {"预算币种", "一级品类", "二级品类"}:
        return "enum_or_text"
    return "text"


def _relevance_by_field(domain_prior: dict[str, Any]) -> dict[str, str]:
    rows = _list(domain_prior.get("missing_fields_with_relevance"))
    relevance: dict[str, str] = {}
    for row in rows:
        item = _mapping(row)
        field_key = _text(item.get("field_key"))
        action = _text(item.get("action"))
        if field_key and action:
            relevance[field_key] = action
    return relevance


def _field_action(field_key: str, relevance_by_field: dict[str, str]) -> str:
    return relevance_by_field.get(field_key) or "ask_in_chat"


def _field_priority(action: str) -> str:
    return FIELD_ACTION_PRIORITY.get(action, "required")


def _field_options(field_key: str, contracts: OrchestrationContracts) -> list[dict[str, Any]]:
    if field_key == "一级品类":
        return [_option(item) for item in contracts.category_level1_options]
    if field_key == "二级品类":
        return [_option(item) for item in contracts.category_level2_options]
    metadata = _metadata_for(contracts, field_key)
    return _enum_options_from_format(metadata.get("类型_枚举_格式", ""))


def _field_question(field_key: str, contracts: OrchestrationContracts) -> str:
    metadata = _metadata_for(contracts, field_key)
    meaning = _text(metadata.get("业务含义"))
    if meaning:
        return f"请补充{field_key}：{meaning}。"
    return f"请补充{field_key}。"


def _field_semantics(field_key: str, action: str, contracts: OrchestrationContracts) -> dict[str, Any]:
    value_type = _infer_value_type(field_key)
    if _field_options(field_key, contracts) and value_type == "text":
        value_type = "enum_or_text"
    criticality, weight = FIELD_ACTION_CRITICALITY.get(action, ("important", 0.7))
    return {
        "value_type": value_type,
        "criticality": criticality,
        "analyzability_weight": weight,
    }


def _field_definition(field_key: str, action: str, contracts: OrchestrationContracts) -> dict[str, Any]:
    return {
        "key": field_key,
        "label": field_key,
        # priority 在 FLARE 中用于提问优先级；完整度要求仍由 xiaocai required_fields 表达。
        "priority": _field_priority(action),
        "completion_required": True,
        # xiaocai 的采购字段是正式产物完整度要求，不等同于对话硬阻断。
        "blocker": False,
        "question": _field_question(field_key, contracts),
        "options": _field_options(field_key, contracts),
    }


def _merge_known_fields(
    *,
    kernel_context: dict[str, Any],
    required_fields: list[str],
    message_fields: dict[str, Any],
) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for field_key in required_fields:
        value = kernel_context.get(field_key)
        if not _is_empty(value):
            merged[field_key] = value
    for field_key, value in message_fields.items():
        if field_key not in merged and not _is_empty(value):
            merged[field_key] = value
    for source in (_mapping(kernel_context.get("fields")), _mapping(kernel_context.get("confirmed_fields"))):
        for field_key, value in source.items():
            if _text(field_key) and not _is_empty(value):
                merged[_text(field_key)] = value
    return merged


def _candidate(
    *,
    field_key: str,
    value: str,
    confidence: float,
    evidence: str,
) -> dict[str, Any]:
    return {
        "field_key": field_key,
        "raw_field_key": field_key,
        "raw_value": value,
        "normalized_value": value,
        "source": "rule_extracted",
        "confidence": confidence,
        "evidence": evidence,
        "normalization_status": "needs_confirmation",
    }


def _category_candidates(domain_prior: dict[str, Any], fields: dict[str, Any]) -> list[dict[str, Any]]:
    category_prior = _mapping(domain_prior.get("category_prior"))
    confidence = float(category_prior.get("confidence_score") or 0.0)
    evidence = "category_prior.resolved_path"
    candidates: list[dict[str, Any]] = []

    level1 = _text(category_prior.get("resolved_level1_category"))
    if level1 and _is_empty(fields.get("一级品类")):
        candidates.append(_candidate(field_key="一级品类", value=level1, confidence=confidence, evidence=evidence))

    level2 = _text(category_prior.get("resolved_level2_category"))
    if level2 and _is_empty(fields.get("二级品类")):
        candidates.append(_candidate(field_key="二级品类", value=level2, confidence=confidence, evidence=evidence))

    return candidates


def _field_history(
    *,
    kernel_context: dict[str, Any],
    message_fields: dict[str, Any],
    fields: dict[str, Any],
) -> list[dict[str, Any]]:
    history = [dict(item) for item in _list(kernel_context.get("field_history")) if isinstance(item, dict)]
    known = {
        _text(item.get("field_key"))
        for item in history
        if _text(item.get("field_key"))
    }
    for field_key, value in message_fields.items():
        canonical_key = _text(field_key)
        if not canonical_key or canonical_key in known or fields.get(canonical_key) != value:
            continue
        history.append(
            {
                "field_key": canonical_key,
                "source": "rule_extracted",
                "evidence": "message_extracted_fields",
                "normalization_status": "accepted",
            }
        )
        known.add(canonical_key)
    return history


def build_flare_intake_contract(
    *,
    kernel_context: dict[str, Any],
    domain_prior: dict[str, Any],
    mode: str | None,
) -> dict[str, Any]:
    """Project xiaocai procurement context into FLARE's native intake inputs."""

    if not _is_intake_mode(mode):
        return {}

    contracts = load_contracts()
    required_fields = _dedupe(_list(domain_prior.get("required_fields")))
    if not required_fields:
        return {}

    message_fields = _mapping(domain_prior.get("message_extracted_fields"))
    fields = _merge_known_fields(
        kernel_context=kernel_context,
        required_fields=required_fields,
        message_fields=message_fields,
    )
    missing_fields = [field for field in required_fields if _is_empty(fields.get(field))]
    relevance_by_field = _relevance_by_field(domain_prior)
    field_semantics = {
        field: _field_semantics(field, _field_action(field, relevance_by_field), contracts)
        for field in required_fields
    }
    field_semantics.update(_mapping(kernel_context.get("field_semantics")))
    clarification_policy = _mapping(domain_prior.get("clarification_policy"))
    priority_order = _dedupe(_list(clarification_policy.get("priority_order")))
    core_fields = [field for field in priority_order if field in set(required_fields)]
    supplementary_fields = [
        field
        for field in [
            *_dedupe(_list(clarification_policy.get("suggest_not_force"))),
            *_dedupe(_list(clarification_policy.get("defer_to_canvas"))),
        ]
        if field in set(required_fields)
    ]

    result = {
        "field_definitions": [
            _field_definition(field, _field_action(field, relevance_by_field), contracts)
            for field in required_fields
        ],
        "required_fields": required_fields,
        "required_missing": missing_fields,
        "fields": fields,
        "confirmed_fields": fields,
        "candidate_fields": _category_candidates(domain_prior, fields),
        "field_history": _field_history(
            kernel_context=kernel_context,
            message_fields=message_fields,
            fields=fields,
        ),
        "field_semantics": field_semantics,
        "intake_contract_source": "xiaocai_procurement_context",
    }
    if core_fields:
        result["intake_core_fields"] = core_fields
    if supplementary_fields:
        result["intake_supplementary_fields"] = supplementary_fields
    return result


__all__ = ["build_flare_intake_contract"]
