from __future__ import annotations

from pathlib import Path

from xiaocai_instance_api.chat.orchestration.contract_loader import load_pack_mount_snapshot


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _normalize_scalar(value: str) -> str:
    return value.strip().strip("'").strip('"')


def _resolve_template_recommendation_rules_path() -> Path:
    root = Path(load_pack_mount_snapshot().domain_packs_root)
    return root / "shared" / "rules" / "template_recommendation_rules.yaml"


def _extract_template_recommendation_rules(text: str) -> list[dict]:
    rules: list[dict] = []
    current_rule: dict | None = None
    current_block: str | None = None
    current_list: str | None = None
    list_indent = 0
    current_candidate: dict | None = None
    current_disable: dict | None = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = _line_indent(raw_line)

        if stripped == "rules:":
            continue
        if stripped.startswith("- rule_id:"):
            current_rule = {
                "rule_id": _normalize_scalar(stripped.split(":", 1)[1]),
                "scenario": "",
                "stage": "",
                "trigger_conditions": {
                    "readiness_score_gte": None,
                    "required_fields_present": [],
                    "block_if_missing_any": [],
                },
                "weighted_candidates": [],
                "disable_conditions": [],
                "fallback_template": "",
            }
            rules.append(current_rule)
            current_block = None
            current_list = None
            current_candidate = None
            current_disable = None
            continue
        if current_rule is None:
            continue
        if stripped in {"trigger_conditions:", "weighted_candidates:", "disable_conditions:"}:
            current_block = stripped[:-1]
            current_list = None
            current_candidate = None
            current_disable = None
            continue
        if stripped.startswith("scenario:"):
            current_rule["scenario"] = _normalize_scalar(stripped.split(":", 1)[1])
            continue
        if stripped.startswith("stage:"):
            current_rule["stage"] = _normalize_scalar(stripped.split(":", 1)[1])
            continue
        if stripped.startswith("fallback_template:"):
            current_rule["fallback_template"] = _normalize_scalar(stripped.split(":", 1)[1])
            continue

        if current_block == "trigger_conditions":
            if stripped in {"required_fields_present:", "block_if_missing_any:"}:
                current_list = stripped[:-1]
                list_indent = indent
                continue
            if stripped.startswith("readiness_score_gte:"):
                raw_value = _normalize_scalar(stripped.split(":", 1)[1])
                current_rule["trigger_conditions"]["readiness_score_gte"] = float(raw_value)
                continue
            if current_list and stripped.startswith("- ") and indent > list_indent:
                current_rule["trigger_conditions"][current_list].append(_normalize_scalar(stripped[2:]))
                continue
            if current_list and indent <= list_indent and not stripped.startswith("- "):
                current_list = None

        if current_block == "weighted_candidates":
            if stripped.startswith("- template_key:"):
                current_candidate = {
                    "template_key": _normalize_scalar(stripped.split(":", 1)[1]),
                    "weight": 0.0,
                }
                current_rule["weighted_candidates"].append(current_candidate)
                continue
            if current_candidate is not None and stripped.startswith("weight:"):
                current_candidate["weight"] = float(_normalize_scalar(stripped.split(":", 1)[1]))
                continue

        if current_block == "disable_conditions":
            if stripped.startswith("- condition:"):
                current_disable = {
                    "condition": _normalize_scalar(stripped.split(":", 1)[1]),
                    "reason": "",
                }
                current_rule["disable_conditions"].append(current_disable)
                continue
            if current_disable is not None and stripped.startswith("reason:"):
                current_disable["reason"] = _normalize_scalar(stripped.split(":", 1)[1])

    return rules


def _collect_known_keys(kernel_context: dict) -> set[str]:
    keys = {key for key in kernel_context.keys() if isinstance(key, str) and key.strip()}
    confirmed_fields = kernel_context.get("confirmed_fields")
    if isinstance(confirmed_fields, dict):
        keys.update(key for key in confirmed_fields.keys() if isinstance(key, str) and key.strip())
    return keys


def _round_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def build_template_recommendation_prior(
    *,
    active_stage: str,
    readiness_score: float,
    kernel_context: dict,
) -> dict:
    normalized_stage = active_stage.replace("-", "_")
    rules_text = _resolve_template_recommendation_rules_path().read_text(encoding="utf-8")
    parsed_rules = _extract_template_recommendation_rules(rules_text)
    matched_rules = [rule for rule in parsed_rules if rule.get("stage") == normalized_stage]
    known_keys = _collect_known_keys(kernel_context)

    candidate_pool: list[dict] = []
    for rule in matched_rules:
        trigger_conditions = rule.get("trigger_conditions", {})
        readiness_threshold = float(trigger_conditions.get("readiness_score_gte") or 0.0)
        required_fields_present = list(trigger_conditions.get("required_fields_present", []))
        block_if_missing_any = list(trigger_conditions.get("block_if_missing_any", []))
        present_required = [field for field in required_fields_present if field in known_keys]
        missing_required = [field for field in required_fields_present if field not in known_keys]
        missing_blocking = [field for field in block_if_missing_any if field not in known_keys]

        if readiness_threshold > 0:
            readiness_factor = min(1.0, readiness_score / readiness_threshold)
        else:
            readiness_factor = readiness_score

        trigger_factor = 1.0
        if required_fields_present:
            if present_required:
                trigger_factor = max(0.5, len(present_required) / len(required_fields_present))
            else:
                trigger_factor = 0.7

        blocking_penalty = 0.0
        if block_if_missing_any:
            blocking_penalty = 0.15 * (len(missing_blocking) / len(block_if_missing_any))

        rule_status = "candidate"
        if readiness_threshold and readiness_score < readiness_threshold:
            rule_status = "needs_more_context"
        elif missing_blocking:
            rule_status = "needs_more_context"

        for candidate in rule.get("weighted_candidates", []):
            base_weight = float(candidate.get("weight") or 0.0)
            score = base_weight * (0.6 + 0.4 * readiness_factor) * trigger_factor - blocking_penalty
            candidate_pool.append(
                {
                    "rule_id": rule.get("rule_id", ""),
                    "scenario": rule.get("scenario", ""),
                    "template_key": candidate.get("template_key", ""),
                    "base_weight": _round_score(base_weight),
                    "readiness_threshold": _round_score(readiness_threshold),
                    "readiness_score": _round_score(readiness_score),
                    "readiness_factor": _round_score(readiness_factor),
                    "trigger_factor": _round_score(trigger_factor),
                    "blocking_penalty": _round_score(blocking_penalty),
                    "score": _round_score(score),
                    "status": rule_status,
                    "present_required_fields": present_required,
                    "missing_required_fields": missing_required,
                    "missing_blocking_fields": missing_blocking,
                    "fallback_template": rule.get("fallback_template", ""),
                }
            )

    candidate_pool.sort(
        key=lambda item: (item.get("score", 0.0), item.get("base_weight", 0.0)),
        reverse=True,
    )
    return {
        "stage": normalized_stage,
        "matched_rules": matched_rules,
        "candidate_pool": candidate_pool,
    }
