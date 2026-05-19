"""需求分析报告投影 - xiaocai procurement analysis contract."""

from __future__ import annotations

from typing import Any

from xiaocai_instance_api.chat.analysis_content import compose_document_sections
from xiaocai_instance_api.chat.analysis_visibility import sanitize_analysis_payload
from xiaocai_instance_api.chat.orchestration.extractor import extract_slots
from xiaocai_instance_api.chat.orchestration.mode_resolution import is_intake_mode


ANALYSIS_TERMS = ("需求分析", "分析报告", "风险分析", "采购策略", "RFX", "RFI", "RFQ", "RFP", "RFB", "策略", "报价", "比价")


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _to_text(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return ""


def _should_project_analysis(
    *,
    mode: str | None,
    user_message: str,
    assistant_message: str = "",
    force: bool = False,
) -> bool:
    if force:
        return True
    normalized_mode = (mode or "").strip()
    if normalized_mode in {"requirement-analysis", "requirement_analysis", "rfx-strategy", "rfx_strategy"}:
        return True
    text = user_message.strip()
    has_analysis_intent = bool(text and any(term in text for term in ANALYSIS_TERMS))
    assistant_text = assistant_message.strip()
    has_analysis_output = bool(assistant_text and any(term in assistant_text for term in (*ANALYSIS_TERMS, "报告", "草案")))
    if is_intake_mode(normalized_mode):
        return has_analysis_intent or has_analysis_output
    return has_analysis_intent or has_analysis_output


def _rfx_type(user_message: str, field_values: dict[str, str]) -> str:
    explicit = _to_text(field_values.get("RFX类型")).upper()
    if explicit in {"RFI", "RFQ", "RFP", "RFB"}:
        return explicit
    upper_text = user_message.upper()
    if "RFI" in upper_text:
        return "RFI"
    if "RFP" in upper_text or "方案" in user_message:
        return "RFP"
    if "RFB" in upper_text or "招标" in user_message:
        return "RFB"
    return "RFQ"


def _collect_field_values(kernel_context: dict[str, Any], user_message: str) -> dict[str, str]:
    values: dict[str, str] = {}
    domain_prior = _as_dict(kernel_context.get("domain_prior"))

    for source in (
        _as_dict(kernel_context.get("confirmed_fields")),
        kernel_context,
        _as_dict(domain_prior.get("message_extracted_fields")),
        extract_slots(user_message),
    ):
        for key, value in source.items():
            text = _to_text(value)
            if text and key not in values:
                values[str(key)] = text

    category_path = _as_list(_as_dict(domain_prior.get("category_prior")).get("resolved_path"))
    if category_path:
        values.setdefault("一级品类", _to_text(category_path[0]))
    if len(category_path) > 1:
        values.setdefault("二级品类", _to_text(category_path[1]))
    if "预算金额" in values:
        values.setdefault("预算币种", "CNY")
    if "采购目的" not in values and "采购" in user_message:
        values["采购目的"] = user_message[:120]
    return values


def _template_sections(kernel_context: dict[str, Any]) -> list[dict[str, Any]]:
    sections = _as_list(_as_dict(kernel_context.get("analysis_template")).get("sections"))
    normalized = [item for item in sections if isinstance(item, dict)]
    if not normalized:
        return []
    prompt_titles: list[str] = []
    for item in _as_list(kernel_context.get("domain_prompt_templates")):
        record = _as_dict(item)
        if _to_text(record.get("key")) != "requirement_analysis":
            continue
        prompt_titles = [_to_text(title) for title in _as_list(record.get("output_contract")) if _to_text(title)]
        break
    if not prompt_titles:
        return normalized
    by_title = {_to_text(_as_dict(item).get("title")): item for item in normalized}
    ordered = [by_title[title] for title in prompt_titles if title in by_title]
    seen_ids = {_to_text(_as_dict(item).get("id")) for item in ordered}
    for item in normalized:
        section_id = _to_text(_as_dict(item).get("id"))
        if section_id not in seen_ids:
            ordered.append(item)
    return ordered


def _analysis_prompt_instruction(kernel_context: dict[str, Any]) -> str:
    for item in _as_list(kernel_context.get("domain_prompt_templates")):
        record = _as_dict(item)
        if _to_text(record.get("key")) == "requirement_analysis":
            return _to_text(record.get("instruction"))
    return ""


def _evidence_refs(kernel_context: dict[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for index, item in enumerate(_as_list(kernel_context.get("context_refs"))):
        ref = _as_dict(item)
        title = _to_text(ref.get("file_name")) or _to_text(ref.get("title"))
        source_id = _to_text(ref.get("source_id")) or f"evidence_{index + 1}"
        if not title and not source_id:
            continue
        refs.append(
            {
                "id": source_id,
                "title": title or source_id,
                "source_type": _to_text(ref.get("source_type")),
                "source": title or source_id,
                "score": ref.get("weight_score"),
            }
        )
    return refs


def has_structured_analysis_content(payload: dict[str, Any]) -> bool:
    """Return true only when native payload already carries structured content."""
    document = _as_dict(payload.get("document")) or payload
    sections = _as_list(document.get("sections"))
    for section in sections:
        record = _as_dict(section)
        if _to_text(record.get("content")):
            return True
        if _as_list(record.get("items")) or _as_list(record.get("rows")):
            return True
    return False


def _markdown(title: str, sections: list[dict[str, Any]]) -> str:
    lines = [f"# {title}"]
    for section in sections:
        lines.extend(["", f"## {section['title']}", _to_text(section.get("content"))])
    return "\n".join(lines).strip()


def _analysis_toolbar_actions() -> list[dict[str, str]]:
    """Declare report actions through the Canvas capability contract."""
    return [
        {"key": "copy", "icon": "copy", "label": "复制"},
        {"key": "export_markdown", "icon": "download", "label": "导出"},
        {"key": "edit", "icon": "edit", "label": "编辑"},
        {"key": "fullscreen", "icon": "fullscreen", "label": "全屏"},
    ]


def build_analysis_report_projection(
    *,
    kernel_context: dict[str, Any],
    mode: str | None,
    user_message: str,
    assistant_message: str = "",
    force: bool = False,
) -> dict[str, Any] | None:
    """Build display projection from xiaocai domain-pack sections, not FLARE state."""
    if not _should_project_analysis(
        mode=mode,
        user_message=user_message,
        assistant_message=assistant_message,
        force=force,
    ):
        return None
    template_sections = _template_sections(kernel_context)
    if not template_sections:
        return None

    field_values = _collect_field_values(kernel_context, user_message)
    evidence_refs = _evidence_refs(kernel_context)
    prompt_instruction = _analysis_prompt_instruction(kernel_context)
    rfx_type = _rfx_type(user_message, field_values)
    sections = compose_document_sections(
        template_sections=template_sections,
        field_values=field_values,
        user_message=user_message,
        evidence_refs=evidence_refs,
        assistant_message=assistant_message,
        rfx_type=rfx_type,
    )
    title = "需求分析与 RFX 策略报告"
    payload = {
        "markdown": _markdown(title, sections),
        "workspace_capabilities": {
            "toolbar_actions": _analysis_toolbar_actions(),
        },
        "document": {
            "analysis_schema_version": "v1",
            "title": title,
            "summary": {
                "problem": "将采购需求转换为可执行的分析报告和 RFX 策略输入。",
                "judgement": "已按 domain-pack 分析模板生成结构化初稿。",
                "recommendation": "先复核待确认字段，再进入供应商初筛和 RFX 文件编制。",
                "rationale": prompt_instruction
                or "来源于 xiaocai procurement domain-pack 的分析章节、字段契约和当前上下文。",
            },
            "sections": sections,
            "evidence_refs": evidence_refs,
            "next_steps": [
                {"label": "复核待确认字段", "status": "available"},
                {"label": "生成 RFX 文件结构", "status": "available"},
            ],
        },
        "rfx_strategy": {
            "recommended_type": rfx_type,
            "allowed_types": ["RFI", "RFQ", "RFP", "RFB"],
            "scorecard": [
                {"dimension": name, "weight": weight}
                for name, weight in (("价格", 40), ("质量", 25), ("交付", 20), ("服务", 10), ("风险", 5))
            ],
            "output_plan": ["供应商响应要求", "报价口径", "评分表", "澄清问题清单"],
        },
    }
    return sanitize_analysis_payload(payload)
