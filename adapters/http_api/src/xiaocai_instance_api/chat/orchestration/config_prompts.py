"""配置中心提示词读取 - xiaocai domain prompt bridge."""

from __future__ import annotations

from typing import Any

from xiaocai_instance_api.config_center.service import get_config_center_service


CONFIG_KEY = "procurement_domain_assets"
CONFIG_SCOPE = "procurement"
ANALYSIS_TERMS = ("需求分析", "分析报告", "RFX", "RFI", "RFQ", "RFP", "RFB", "采购策略", "策略")
SOURCING_TERMS = ("寻源", "供应商", "候选", "找供应商")


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _to_text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _normalize_prompt_template(value: object) -> dict[str, Any] | None:
    record = _as_dict(value)
    key = str(record.get("key") or "").strip()
    instruction = str(record.get("instruction") or "").strip()
    if not key and not instruction:
        return None
    return {
        "key": key,
        "title": str(record.get("title") or "").strip(),
        "stage": str(record.get("stage") or "").strip(),
        "input_fields": _as_list(record.get("inputFields")),
        "output_contract": _as_list(record.get("outputContract")),
        "instruction": instruction,
    }


async def load_domain_prompt_templates() -> list[dict[str, Any]]:
    """Load saved prompt templates without making settings UI authoritative state."""
    try:
        draft = await get_config_center_service().get_draft(
            config_key=CONFIG_KEY,
            scope=CONFIG_SCOPE,
        )
    except Exception:
        return []

    payload = _as_dict((draft or {}).get("payload"))
    prompts = _as_dict(payload.get("prompts"))
    templates = [
        normalized
        for item in _as_list(prompts.get("promptTemplates"))
        if (normalized := _normalize_prompt_template(item))
    ]
    return templates


def _stage_template_keys(active_stage: str, user_message: str | None) -> tuple[str, ...]:
    text = user_message or ""
    if any(term in text for term in SOURCING_TERMS) or active_stage == "sourcing":
        return ("sourcing_strategy", "intent_boundary")
    if any(term in text for term in ANALYSIS_TERMS) or active_stage in {"requirement-analysis", "rfx-strategy"}:
        return ("requirement_analysis", "rfx_document_output")
    return ("requirement_intake_result", "deep_intent_confirmation")


def _select_prompt_template(
    templates: list[dict[str, Any]],
    *,
    active_stage: str,
    user_message: str | None,
) -> dict[str, Any]:
    by_key = {_to_text(item.get("key")): item for item in templates if _to_text(item.get("key"))}
    for key in _stage_template_keys(active_stage, user_message):
        if key in by_key:
            return by_key[key]
    return templates[0] if templates else {}


def _analysis_section_titles(kernel_context: dict[str, Any]) -> list[str]:
    sections = _as_list(_as_dict(kernel_context.get("analysis_template")).get("sections"))
    return [_to_text(_as_dict(item).get("title")) for item in sections if _to_text(_as_dict(item).get("title"))]


def _dedupe_texts(values: list[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _to_text(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _field_value(kernel_context: dict[str, Any], field: str) -> str:
    for source in (
        _as_dict(kernel_context.get("confirmed_fields")),
        _as_dict(kernel_context.get("fields")),
        kernel_context,
        _as_dict(_as_dict(kernel_context.get("domain_prior")).get("message_extracted_fields")),
    ):
        value = _to_text(source.get(field))
        if value:
            return value
    return ""


def _input_field_rows(kernel_context: dict[str, Any], input_fields: list[Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for field in _dedupe_texts(input_fields):
        value = _field_value(kernel_context, field)
        rows.append({"field": field, "value": value, "status": "filled" if value else "missing"})
    return rows


def _template_weights(kernel_context: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = _as_list(
        _as_dict(_as_dict(kernel_context.get("domain_prior")).get("template_recommendation")).get("candidate_pool")
    )
    rows: list[dict[str, Any]] = []
    for item in candidates[:5]:
        record = _as_dict(item)
        rows.append(
            {
                "template_key": _to_text(record.get("template_key")),
                "score": record.get("score"),
                "base_weight": record.get("base_weight"),
                "status": _to_text(record.get("status")),
            }
        )
    return rows


def _source_weights(kernel_context: dict[str, Any]) -> dict[str, Any]:
    weights = _as_dict(_as_dict(kernel_context.get("retrieval_policy")).get("source_weights"))
    return {key: value for key, value in weights.items() if _to_text(key)}


def _prompt_text(
    *,
    active_stage: str,
    template: dict[str, Any],
    input_rows: list[dict[str, str]],
    output_sections: list[str],
    template_weights: list[dict[str, Any]],
    source_weights: dict[str, Any],
) -> str:
    lines = [
        "【xiaocai 系统设置提示词】",
        "以下内容来自系统设置与 domain-pack 契约，优先级高于自由发挥。",
        f"当前阶段：{active_stage}",
        f"优先模板：{_to_text(template.get('title')) or _to_text(template.get('key'))}",
        f"阶段指令：{_to_text(template.get('instruction'))}",
        "输入字段优先级：",
    ]
    lines.extend([f"- {row['field']}：{row['value'] or '待确认'}" for row in input_rows] or ["- 无"])
    lines.append("输出结构必须按以下顺序覆盖：")
    lines.extend([f"{index}. {title}" for index, title in enumerate(output_sections, start=1)] or ["1. 按系统设置输出"])
    if template_weights:
        lines.append("模板权重候选，高分优先：")
        lines.extend(
            f"- {row['template_key']} score={row['score']} base_weight={row['base_weight']} status={row['status']}"
            for row in template_weights
        )
    if source_weights:
        lines.append("资料来源权重，高权重资料优先引用：")
        lines.extend(f"- {key}: {value}" for key, value in source_weights.items())
    lines.extend(
        [
            "输出要求：",
            "- 先使用已确认字段和资料证据；缺失内容标注为待确认，不要伪造。",
            "- 若用户要求需求分析、RFX 或采购策略，正文必须输出上述完整章节。",
            "- 区分事实、合理推断和待确认项。",
        ]
    )
    return "\n".join(line for line in lines if line is not None).strip()


def build_domain_prompt_instructions(
    *,
    kernel_context: dict[str, Any],
    prompt_templates: list[dict[str, Any]],
    user_message: str | None,
) -> dict[str, Any] | None:
    """Compile settings prompts into explicit model-facing procurement instructions."""
    domain_prior = _as_dict(kernel_context.get("domain_prior"))
    active_stage = _to_text(domain_prior.get("active_stage")) or "requirement-analysis"
    template = _select_prompt_template(prompt_templates, active_stage=active_stage, user_message=user_message)
    analysis_sections = _analysis_section_titles(kernel_context)
    output_contract = _as_list(template.get("output_contract"))
    output_sections = _dedupe_texts([*output_contract, *analysis_sections])
    input_rows = _input_field_rows(kernel_context, _as_list(template.get("input_fields")))
    weights = _template_weights(kernel_context)
    sources = _source_weights(kernel_context)
    if not template and not output_sections:
        return None
    prompt_text = _prompt_text(
        active_stage=active_stage,
        template=template,
        input_rows=input_rows,
        output_sections=output_sections,
        template_weights=weights,
        source_weights=sources,
    )
    return {
        "source": "system_settings_and_domain_pack",
        "active_stage": active_stage,
        "active_template": {
            "key": _to_text(template.get("key")),
            "title": _to_text(template.get("title")),
            "stage": _to_text(template.get("stage")),
        },
        "input_fields": input_rows,
        "output_sections": output_sections,
        "template_weights": weights,
        "source_weights": sources,
        "prompt_text": prompt_text,
    }
