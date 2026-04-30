from __future__ import annotations

from pathlib import Path

from xiaocai_instance_api.chat.orchestration.contract_loader import load_pack_mount_snapshot


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _normalize_scalar(value: str) -> str:
    return value.strip().strip("'").strip('"')


def _resolve_shared_rules_path() -> Path:
    root = Path(load_pack_mount_snapshot().domain_packs_root)
    return root / "shared" / "rules" / "clarification_relevance_rules.yaml"


def _resolve_activity_rules_path() -> Path:
    root = Path(load_pack_mount_snapshot().domain_packs_root)
    return root / "activity_procurement" / "clarification_relevance.yaml"


def _parse_shared_rules(text: str) -> dict:
    data = {
        "defaults": {},
        "field_roles": {
            "universal": [],
            "canvas_preferred": [],
            "template_conditional": [],
        },
    }
    current_section = ""
    current_list = ""
    list_indent = 0

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = _line_indent(raw_line)
        if stripped == "defaults:":
            current_section = "defaults"
            current_list = ""
            continue
        if stripped == "field_roles:":
            current_section = "field_roles"
            current_list = ""
            continue
        if current_section == "defaults" and ":" in stripped and not stripped.startswith("- "):
            key, value = stripped.split(":", 1)
            data["defaults"][key.strip()] = _normalize_scalar(value)
            continue
        if current_section == "field_roles" and stripped.endswith(":") and not stripped.startswith("- "):
            current_list = stripped[:-1]
            list_indent = indent
            continue
        if current_section == "field_roles" and current_list and stripped.startswith("- ") and indent > list_indent:
            data["field_roles"].setdefault(current_list, []).append(_normalize_scalar(stripped[2:]))

    return data


def _parse_activity_rules(text: str) -> dict:
    data = {"match": {}, "conditional_fields": []}
    current_item: dict | None = None
    current_block = ""

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "match:":
            current_block = "match"
            continue
        if stripped == "conditional_fields:":
            current_block = "conditional_fields"
            continue
        if current_block == "match" and ":" in stripped and not stripped.startswith("- "):
            key, value = stripped.split(":", 1)
            data["match"][key.strip()] = _normalize_scalar(value)
            continue
        if current_block == "conditional_fields" and stripped.startswith("- field_key:"):
            current_item = {
                "field_key": _normalize_scalar(stripped.split(":", 1)[1]),
                "ask_when": {},
                "action_when_relevant": "ask_in_chat",
                "otherwise": "defer_to_canvas",
            }
            data["conditional_fields"].append(current_item)
            continue
        if current_item is None:
            continue
        if stripped == "ask_when:":
            current_block = "ask_when"
            continue
        if current_block == "ask_when" and ":" in stripped and not stripped.startswith("- "):
            key, value = stripped.split(":", 1)
            current_item["ask_when"][key.strip()] = _normalize_scalar(value)
            continue
        if stripped.startswith("action_when_relevant:"):
            current_item["action_when_relevant"] = _normalize_scalar(stripped.split(":", 1)[1])
            current_block = "conditional_fields"
            continue
        if stripped.startswith("otherwise:"):
            current_item["otherwise"] = _normalize_scalar(stripped.split(":", 1)[1])
            current_block = "conditional_fields"

    return data


def _round_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def _collect_candidate_missing_fields(template_recommendation: dict) -> dict[str, float]:
    field_scores: dict[str, float] = {}
    for candidate in template_recommendation.get("candidate_pool", []):
        candidate_score = float(candidate.get("score") or 0.0)
        for field in candidate.get("missing_required_fields", []):
            field_scores[field] = max(field_scores.get(field, 0.0), candidate_score * 0.7)
        for field in candidate.get("missing_blocking_fields", []):
            field_scores[field] = max(field_scores.get(field, 0.0), candidate_score)
    return field_scores


def _conditions_match(rule: dict, *, category_prior: dict, readiness_score: float) -> bool:
    ask_when = rule.get("ask_when", {})
    matched_level1 = str(ask_when.get("matched_level1_category") or "")
    if matched_level1 and category_prior.get("resolved_level1_category") != matched_level1:
        return False
    category_confidence_gte = ask_when.get("category_confidence_gte")
    if category_confidence_gte is not None:
        if float(category_prior.get("confidence_score") or 0.0) < float(category_confidence_gte):
            return False
    readiness_score_gte = ask_when.get("readiness_score_gte")
    if readiness_score_gte is not None:
        if readiness_score < float(readiness_score_gte):
            return False
    return True


def build_missing_field_relevance(
    *,
    missing_fields_with_priority: list[dict],
    template_recommendation: dict,
    category_prior: dict,
    readiness_score: float,
) -> dict:
    shared_rules = _parse_shared_rules(_resolve_shared_rules_path().read_text(encoding="utf-8"))
    activity_rules = _parse_activity_rules(_resolve_activity_rules_path().read_text(encoding="utf-8"))
    field_scores = _collect_candidate_missing_fields(template_recommendation)
    by_field = {item["field_key"]: dict(item) for item in missing_fields_with_priority}

    for field_key, template_score in field_scores.items():
        by_field.setdefault(
            field_key,
            {
                "field_key": field_key,
                "priority_score": _round_score(template_score),
                "stage_priority": 0.0,
                "template_score": _round_score(template_score),
                "blocking_hits": 0,
                "influencing_templates": [],
            },
        )

    universal = set(shared_rules["field_roles"].get("universal", []))
    canvas_preferred = set(shared_rules["field_roles"].get("canvas_preferred", []))
    template_conditional = set(shared_rules["field_roles"].get("template_conditional", []))
    defaults = shared_rules.get("defaults", {})
    maybe_relevant_action = str(defaults.get("maybe_relevant_action") or "suggest_not_force")
    low_relevance_action = str(defaults.get("low_relevance_action") or "defer_to_canvas")
    conditional_map = {
        item.get("field_key", ""): item for item in activity_rules.get("conditional_fields", [])
    }

    rows: list[dict] = []
    for field_key, base in by_field.items():
        relevance = "relevant"
        action = "ask_in_chat"
        reason = "required_field"

        if field_key in canvas_preferred:
            relevance = "maybe_relevant"
            action = "defer_to_canvas"
            reason = "canvas_preferred"
        elif field_key in universal:
            relevance = "relevant"
            action = "ask_in_chat"
            reason = "universal_field"
        elif field_key in conditional_map:
            rule = conditional_map[field_key]
            if _conditions_match(rule, category_prior=category_prior, readiness_score=readiness_score):
                relevance = "relevant"
                action = str(rule.get("action_when_relevant") or "ask_in_chat")
                reason = "conditional_match"
            else:
                relevance = "not_relevant"
                action = str(rule.get("otherwise") or low_relevance_action)
                reason = "conditional_not_met"
        elif field_key in template_conditional:
            relevance = "maybe_relevant"
            action = maybe_relevant_action
            reason = "template_conditional"

        rows.append(
            {
                **base,
                "relevance": relevance,
                "action": action,
                "reason": reason,
            }
        )

    rows.sort(key=lambda item: item.get("priority_score", 0.0), reverse=True)
    ask_in_chat = [item["field_key"] for item in rows if item.get("action") == "ask_in_chat"]
    defer_to_canvas = [item["field_key"] for item in rows if item.get("action") == "defer_to_canvas"]
    suggest_not_force = [item["field_key"] for item in rows if item.get("action") == "suggest_not_force"]
    return {
        "missing_fields_with_relevance": rows,
        "ask_in_chat": ask_in_chat,
        "defer_to_canvas": defer_to_canvas,
        "suggest_not_force": suggest_not_force,
    }
