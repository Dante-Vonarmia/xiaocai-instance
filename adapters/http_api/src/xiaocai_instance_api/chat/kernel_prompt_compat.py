"""FLARE prompt compatibility projection for xiaocai domain instructions."""

from __future__ import annotations

from typing import Any


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _to_text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _section_rows(section_titles: list[str]) -> list[dict[str, str]]:
    return [
        {
            "key": f"section_{index}",
            "label": title,
        }
        for index, title in enumerate(section_titles, start=1)
    ]


def _field_names(input_fields: list[Any]) -> list[str]:
    names: list[str] = []
    for item in input_fields:
        field_name = _to_text(_as_dict(item).get("field")) or _to_text(item)
        if field_name and field_name not in names:
            names.append(field_name)
    return names


def _active_template(instructions: dict[str, Any]) -> dict[str, str]:
    template = _as_dict(instructions.get("active_template"))
    return {
        "key": _to_text(template.get("key")) or _to_text(instructions.get("active_stage")) or "domain_prompt",
        "title": _to_text(template.get("title")) or "xiaocai domain prompt",
        "stage": _to_text(template.get("stage")) or _to_text(instructions.get("active_stage")),
    }


def _template_payload(
    *,
    instructions: dict[str, Any],
    prompt_text: str,
) -> dict[str, Any]:
    template = _active_template(instructions)
    output_sections = [_to_text(item) for item in _as_list(instructions.get("output_sections")) if _to_text(item)]
    input_fields = _field_names(_as_list(instructions.get("input_fields")))
    return {
        "is_template": True,
        "template_key": template["key"],
        "title": template["title"],
        "stage": template["stage"],
        "template_sections": output_sections,
        "required_output_fields": input_fields,
        "instruction": prompt_text,
    }


def _artifact_template_result(instructions: dict[str, Any], prompt_text: str) -> dict[str, Any]:
    template = _template_payload(instructions=instructions, prompt_text=prompt_text)
    return {
        "status": "matched",
        "source": "xiaocai_domain_prompt_instructions",
        "template_key": template["template_key"],
        "template": template,
        "sections": _section_rows(template["template_sections"]),
        "weighted_candidates": _as_list(instructions.get("template_weights")),
    }


def _response_strategy_result(instructions: dict[str, Any], prompt_text: str) -> dict[str, Any]:
    template = _active_template(instructions)
    section_titles = [
        _to_text(item)
        for item in _as_list(instructions.get("output_sections"))
        if _to_text(item)
    ]
    sections = _section_rows(section_titles)
    return {
        "strategy_key": "xiaocai_domain_prompt",
        "response_intent": "document_draft_output",
        "response_shape": "structured_report",
        "tone": "professional",
        "response_plan": {
            "guidance": prompt_text,
            "sections": sections,
        },
        "sections": sections,
        "template_key": template["key"],
    }


def _user_template(instructions: dict[str, Any], prompt_text: str) -> dict[str, Any]:
    template = _template_payload(instructions=instructions, prompt_text=prompt_text)
    return {
        "document_kind": "template",
        "source_id": "xiaocai.domain_prompt",
        "title": template["title"],
        "template": template,
        "sections": _section_rows(template["template_sections"]),
    }


def _module_prompt_entry(instructions: dict[str, Any], prompt_text: str) -> dict[str, Any]:
    template = _active_template(instructions)
    return {
        "module_key": template["key"],
        "key": template["key"],
        "label": template["title"],
        "target_mode": _to_text(instructions.get("active_stage")),
        "prompt_instruction": prompt_text,
        "runtime_instruction": prompt_text,
        "priority": 100,
    }


def _merge_module_prompt_registry(
    existing: object,
    entry: dict[str, Any],
) -> list[dict[str, Any]]:
    registry = [item for item in _as_list(existing) if isinstance(item, dict)]
    key = _to_text(entry.get("module_key"))
    if key and any(_to_text(item.get("module_key") or item.get("key")) == key for item in registry):
        return registry
    return [entry, *registry]


def project_domain_prompt_for_flare(payload: dict[str, Any]) -> dict[str, Any]:
    """Map xiaocai prompt instructions onto FLARE-supported prompt contracts."""
    instructions = _as_dict(payload.get("domain_prompt_instructions"))
    prompt_text = _to_text(payload.get("domain_system_prompt")) or _to_text(instructions.get("prompt_text"))
    if not prompt_text:
        return payload

    compatible = dict(payload)
    if not _as_dict(compatible.get("artifact_template_result")):
        compatible["artifact_template_result"] = _artifact_template_result(instructions, prompt_text)
    if not _as_dict(compatible.get("response_strategy_result")):
        compatible["response_strategy_result"] = _response_strategy_result(instructions, prompt_text)
    if not _as_dict(compatible.get("user_template")):
        compatible["user_template"] = _user_template(instructions, prompt_text)
    compatible["module_prompt_registry"] = _merge_module_prompt_registry(
        compatible.get("module_prompt_registry"),
        _module_prompt_entry(instructions, prompt_text),
    )
    return compatible
