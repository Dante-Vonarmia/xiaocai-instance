from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from xiaocai_instance_api.chat.orchestration.contract_loader import (
    load_contracts,
    load_pack_mount_snapshot,
)
from xiaocai_instance_api.chat.orchestration.extractor import extract_slots
from xiaocai_instance_api.chat.orchestration.field_prior import (
    build_missing_field_priorities,
)
from xiaocai_instance_api.chat.orchestration.relevance_prior import (
    build_missing_field_relevance,
)
from xiaocai_instance_api.chat.orchestration.taxonomy_prior import (
    build_taxonomy_prior,
)
from xiaocai_instance_api.chat.orchestration.template_prior import (
    build_template_recommendation_prior,
)
from xiaocai_instance_api.chat.orchestration.threshold_prior import (
    build_confidence_policy,
)


@dataclass(frozen=True)
class ProcurementPriorContext:
    analysis_template: dict
    rfx_template: dict
    domain_prior: dict


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _normalize_scalar(value: str) -> str:
    return value.strip().strip("'").strip('"')


def _resolve_analysis_rfx_contract_path() -> Path:
    root = Path(load_pack_mount_snapshot().domain_packs_root)
    return root / "contracts" / "procurement-analysis-rfx-templates.yaml"


def _extract_analysis_template_sections(text: str) -> list[dict]:
    sections: list[dict] = []
    in_sections = False
    current: dict | None = None
    current_list: str | None = None
    list_indent = 0

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped == "rfx_templates:":
            break
        if stripped == "sections:":
            in_sections = True
            continue
        if not in_sections:
            continue

        indent = _line_indent(raw_line)
        if stripped.startswith("- id:"):
            current = {
                "id": _normalize_scalar(stripped.split(":", 1)[1]),
                "title": "",
                "required_fields": [],
                "optional_fields": [],
                "block_on_missing_required": False,
                "draft_allowed_when_missing": True,
            }
            sections.append(current)
            current_list = None
            continue
        if current is None:
            continue
        if stripped in {"required_fields:", "optional_fields:"}:
            current_list = stripped[:-1]
            list_indent = indent
            continue
        if current_list and stripped.startswith("- ") and indent > list_indent:
            current[current_list].append(_normalize_scalar(stripped[2:]))
            continue
        if current_list and indent <= list_indent and not stripped.startswith("- "):
            current_list = None
        if stripped.startswith("title:"):
            current["title"] = _normalize_scalar(stripped.split(":", 1)[1])
            continue
        if stripped.startswith("block_on_missing_required:"):
            current["block_on_missing_required"] = stripped.split(":", 1)[1].strip().lower() == "true"
            continue
        if stripped.startswith("draft_allowed_when_missing:"):
            current["draft_allowed_when_missing"] = stripped.split(":", 1)[1].strip().lower() == "true"

    return sections


def _extract_rfx_templates(text: str) -> dict:
    allowed_types: list[str] = []
    templates: list[dict] = []
    in_allowed_types = False
    in_templates = False
    current: dict | None = None
    current_list: str | None = None
    list_indent = 0
    allowed_indent = 0

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        indent = _line_indent(raw_line)

        if stripped == "allowed_types:":
            in_allowed_types = True
            allowed_indent = indent
            in_templates = False
            continue
        if in_allowed_types and stripped.startswith("- ") and indent > allowed_indent:
            allowed_types.append(_normalize_scalar(stripped[2:]))
            continue
        if in_allowed_types and indent <= allowed_indent and not stripped.startswith("- "):
            in_allowed_types = False

        if stripped == "templates:":
            in_templates = True
            continue
        if not in_templates:
            continue
        if stripped.startswith("output_state_rules:"):
            break
        if stripped.startswith("- type:"):
            current = {
                "type": _normalize_scalar(stripped.split(":", 1)[1]),
                "required_fields": [],
                "optional_fields": [],
            }
            templates.append(current)
            current_list = None
            continue
        if current is None:
            continue
        if stripped in {"required_fields:", "optional_fields:"}:
            current_list = stripped[:-1]
            list_indent = indent
            continue
        if current_list and stripped.startswith("- ") and indent > list_indent:
            current[current_list].append(_normalize_scalar(stripped[2:]))
            continue
        if current_list and indent <= list_indent and not stripped.startswith("- "):
            current_list = None

    return {"allowed_types": allowed_types, "templates": templates}


def _resolve_active_stage(mode: str | None) -> str:
    normalized = (mode or "").strip()
    if normalized == "intelligent_sourcing":
        return "sourcing"
    if normalized == "requirement_canvas" or normalized.startswith("requirement_intake"):
        return "requirement-collection"
    return "requirement-analysis"


def _collect_filled_fields(
    kernel_context: dict,
    required_fields: list[str],
    message_slots: dict[str, str] | None = None,
) -> list[str]:
    filled: list[str] = []
    confirmed_fields = kernel_context.get("confirmed_fields")
    confirmed_map = confirmed_fields if isinstance(confirmed_fields, dict) else {}
    slot_map = message_slots if isinstance(message_slots, dict) else {}
    for field in required_fields:
        direct_value = kernel_context.get(field)
        confirmed_value = confirmed_map.get(field)
        slot_value = slot_map.get(field)
        candidate = confirmed_value if confirmed_value not in (None, "", [], {}) else direct_value
        if candidate in (None, "", [], {}):
            candidate = slot_value
        if candidate not in (None, "", [], {}):
            filled.append(field)
    return filled


def build_procurement_prior_context(
    *,
    kernel_context: dict,
    mode: str | None,
    user_message: str | None = None,
) -> ProcurementPriorContext:
    contracts = load_contracts()
    contract_text = _resolve_analysis_rfx_contract_path().read_text(encoding="utf-8")
    analysis_sections = _extract_analysis_template_sections(contract_text)
    rfx_template = _extract_rfx_templates(contract_text)
    active_stage = _resolve_active_stage(mode)
    message_slots = extract_slots(user_message or "") if user_message else {}
    category_prior = build_taxonomy_prior(
        user_message=user_message,
        kernel_context=kernel_context,
    )

    if active_stage == "sourcing":
        required_fields = list(contracts.sourcing_required_fields)
    else:
        required_fields = list(contracts.stage_required.get(active_stage, []))

    filled_fields = _collect_filled_fields(
        kernel_context,
        required_fields,
        message_slots=message_slots,
    )
    missing_fields = [field for field in required_fields if field not in filled_fields]
    readiness_score = round((len(filled_fields) / len(required_fields)), 4) if required_fields else 0.0
    template_recommendation = build_template_recommendation_prior(
        active_stage=active_stage,
        readiness_score=readiness_score,
        kernel_context=kernel_context,
    )
    missing_fields_with_priority = build_missing_field_priorities(
        required_fields=required_fields,
        missing_fields=missing_fields,
        template_recommendation=template_recommendation,
    )
    relevance_prior = build_missing_field_relevance(
        missing_fields_with_priority=missing_fields_with_priority,
        template_recommendation=template_recommendation,
        category_prior=category_prior,
        readiness_score=readiness_score,
    )

    analysis_template = {
        "output_name": "requirement-analysis-report",
        "sections": analysis_sections,
    }
    clarification_policy = {
        "ask_missing_fields_one_by_one": True,
        "top_missing_field": relevance_prior["ask_in_chat"][0] if relevance_prior["ask_in_chat"] else "",
        "priority_order": relevance_prior["ask_in_chat"],
        "missing_fields_with_priority": missing_fields_with_priority,
        "missing_fields_with_relevance": relevance_prior["missing_fields_with_relevance"],
        "defer_to_canvas": relevance_prior["defer_to_canvas"],
        "suggest_not_force": relevance_prior["suggest_not_force"],
    }
    confidence_policy = build_confidence_policy(
        category_prior=category_prior,
        readiness_score=readiness_score,
        clarification_policy=clarification_policy,
    )
    clarification_policy["ask_missing_fields_one_by_one"] = confidence_policy["should_clarify_before_commit"]
    domain_prior = {
        "domain": "procurement",
        "active_stage": active_stage,
        "required_fields": required_fields,
        "filled_fields": filled_fields,
        "message_extracted_fields": message_slots,
        "missing_fields": missing_fields,
        "missing_fields_with_priority": missing_fields_with_priority,
        "missing_fields_with_relevance": relevance_prior["missing_fields_with_relevance"],
        "readiness_score": readiness_score,
        "preferred_output_template_key": "analysis_template",
        "prefer_template_driven_output": True,
        "category_prior": category_prior,
        "template_recommendation": template_recommendation,
        "clarification_policy": clarification_policy,
        "confidence_policy": confidence_policy,
        "instruction_hints": {
            "prefer_analysis_template_sections": [item.get("title", "") for item in analysis_sections if item.get("title")],
            "ask_for_missing_required_fields_before_finalizing": confidence_policy["should_clarify_before_commit"],
            "defer_missing_fields_to_workbench": bool(missing_fields) and not confidence_policy["should_clarify_before_commit"],
            "prioritize_required_fields_over_freeform_expansion": True,
            "prefer_weighted_template_candidates": bool(template_recommendation.get("candidate_pool")),
            "top_missing_field": clarification_policy["top_missing_field"],
            "preferred_category_path": category_prior.get("resolved_path", []),
            "clarification_action": confidence_policy["action"],
        },
    }
    return ProcurementPriorContext(
        analysis_template=analysis_template,
        rfx_template=rfx_template,
        domain_prior=domain_prior,
    )
