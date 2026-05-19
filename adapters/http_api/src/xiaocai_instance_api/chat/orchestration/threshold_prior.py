from __future__ import annotations

from pathlib import Path

from xiaocai_instance_api.chat.orchestration.contract_loader import load_pack_mount_snapshot


def _normalize_scalar(value: str) -> str:
    return value.strip().strip("'").strip('"')


def _resolve_threshold_rules_path() -> Path:
    root = Path(load_pack_mount_snapshot().domain_packs_root)
    return root / "shared" / "rules" / "confidence_threshold_rules.yaml"


def _parse_threshold_rules(text: str) -> dict:
    data = {"thresholds": {}, "policies": {}}
    current_section = ""
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "thresholds:":
            current_section = "thresholds"
            continue
        if stripped == "policies:":
            current_section = "policies"
            continue
        if ":" not in stripped or stripped.startswith("- "):
            continue
        key, value = stripped.split(":", 1)
        if current_section == "thresholds":
            data["thresholds"][key.strip()] = float(_normalize_scalar(value))
        elif current_section == "policies":
            data["policies"][key.strip()] = _normalize_scalar(value)
    return data


def _round_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def build_confidence_policy(
    *,
    category_prior: dict,
    readiness_score: float,
    clarification_policy: dict,
    message_intent_signals: dict | None = None,
) -> dict:
    rules = _parse_threshold_rules(_resolve_threshold_rules_path().read_text(encoding="utf-8"))
    thresholds = rules.get("thresholds", {})
    policies = rules.get("policies", {})

    category_confidence = float(category_prior.get("confidence_score") or 0.0)
    ask_in_chat = clarification_policy.get("priority_order", [])
    defer_to_canvas = clarification_policy.get("defer_to_canvas", [])
    intent_signals = message_intent_signals if isinstance(message_intent_signals, dict) else {}

    action = "proceed"
    should_clarify_before_commit = False
    should_defer_detail_fields_to_canvas = False
    rationale = "thresholds_passed"

    if intent_signals.get("wants_direct_plan"):
        action = str(policies.get("when_direct_plan_requested") or "provide_draft_plan_with_missing_checklist")
        rationale = "direct_plan_requested"
    elif category_confidence < float(thresholds.get("category_confidence_lt_for_category_clarification", 0.0)):
        action = str(policies.get("when_low_category_confidence") or "clarify_category_first")
        should_clarify_before_commit = True
        rationale = "low_category_confidence"
    elif readiness_score < float(thresholds.get("readiness_score_lt_for_requirement_clarification", 0.0)) and ask_in_chat:
        action = str(policies.get("when_low_readiness_score") or "clarify_requirement_first")
        should_clarify_before_commit = True
        rationale = "low_readiness_score"
    elif not ask_in_chat and defer_to_canvas:
        action = str(policies.get("when_no_relevant_chat_fields") or "defer_to_canvas")
        should_defer_detail_fields_to_canvas = True
        rationale = "no_relevant_chat_fields"

    allow_direct_commit = (
        category_confidence >= float(thresholds.get("category_confidence_gte_for_direct_commit", 1.0))
        and readiness_score >= float(thresholds.get("readiness_score_gte_for_direct_commit", 1.0))
        and not should_clarify_before_commit
    )
    return {
        "category_confidence": _round_score(category_confidence),
        "readiness_score": _round_score(readiness_score),
        "allow_direct_commit": allow_direct_commit,
        "should_clarify_before_commit": should_clarify_before_commit,
        "should_defer_detail_fields_to_canvas": should_defer_detail_fields_to_canvas,
        "action": action,
        "rationale": rationale,
        "top_missing_field": clarification_policy.get("top_missing_field", ""),
    }
