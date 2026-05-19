"""User-visible fallback projection for xiaocai chat responses."""

from __future__ import annotations

from typing import Any

from xiaocai_instance_api.chat.analysis_projection import build_analysis_report_projection
from xiaocai_instance_api.chat.sourcing_projection import build_sourcing_candidates_projection
from xiaocai_instance_api.chat.workbench_projection import build_intake_workbench_projection


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


def _analysis_message(payload: dict[str, Any] | None) -> str:
    payload = _as_dict(payload)
    return _to_text(payload.get("markdown"))


def _intake_message(payload: dict[str, Any] | None) -> str:
    canvas = _as_dict(_as_dict(payload).get("canvas_payload"))
    state = _as_dict(canvas.get("canvas_state"))
    for item in _as_list(state.get("versions")):
        content = _to_text(_as_dict(item).get("content"))
        if content:
            return content
    return ""


def _field_value(rows: list[Any], *labels: str) -> str:
    for row in rows:
        record = _as_dict(row)
        label = _to_text(record.get("label")) or _to_text(record.get("field_key"))
        if label in labels:
            value = _to_text(record.get("value"))
            if value:
                return value
    return "待补充"


def _sourcing_message(payload: dict[str, Any] | None) -> str:
    payload = _as_dict(payload)
    if not payload:
        return ""
    collected = _as_list(payload.get("base_collected"))
    candidates = _as_list(payload.get("candidates"))
    region = _field_value(collected, "交付地点", "供应商区域")
    product = _field_value(collected, "产品/服务", "二级品类", "一级品类")
    candidate_lines = []
    for item in candidates[:5]:
        record = _as_dict(item)
        title = _to_text(record.get("supplier_name")) or _to_text(record.get("title"))
        source_type = _to_text(record.get("source_type")) or "待核验"
        confidence = _to_text(record.get("confidence")) or "low"
        summary = _to_text(record.get("summary"))
        reasons = [
            _to_text(reason)
            for reason in _as_list(record.get("match_reasons"))
            if _to_text(reason)
        ]
        unresolved = [
            _to_text(check)
            for check in _as_list(record.get("unresolved_checks"))
            if _to_text(check)
        ]
        if title:
            candidate_lines.append(f"- {title}｜数据来源：{source_type}｜可信度：{confidence}")
            candidate_lines.append(f"  - 适配说明：{summary or '需结合真实检索结果核验主营品类、交付能力和服务覆盖。'}")
            candidate_lines.append(f"  - 匹配理由：{'；'.join(reasons) if reasons else '根据当前采购字段生成待核验候选线索。'}")
            candidate_lines.append(f"  - 待核验事项：{'；'.join(unresolved) if unresolved else '主体资质、历史案例、报价口径、交付排期、售后质保。'}")
    if not candidate_lines:
        candidate_lines.append("- 暂无可确认企业；需接入真实检索结果后补齐候选公司。")
    return "\n".join(
        [
            "# 智能寻源候选初筛",
            "",
            "## 寻源口径",
            f"- 产品/服务：{product}",
            f"- 供应商区域：{region}",
            f"- 查询口径：{_to_text(payload.get('query')) or product}",
            "",
            "## 准入门槛",
            "- 主营品类与采购需求匹配",
            "- 具备合法经营资质、同类历史案例、基础质量/环保/材质证明",
            "- 可承诺交付排期、安装服务、售后质保和发票要求",
            "",
            "## 优选指标",
            "- 履约能力、项目经验、专业人员、企业信用、售后响应、交付稳定性",
            "",
            "## 候选清单字段",
            "- 公司名称、主营品类、所在地、详细地址、联系人、联系电话、数据来源、可信度、待核验事项",
            "",
            "## 候选清单",
            *candidate_lines,
            "",
            "## 数据来源和可信度说明",
            "- 当前占位候选不代表真实推荐结果；只有接入供应商库、项目资料或外部检索并完成核验后，才能进入可确认候选。",
            "- 可信度 low：仅可作为检索入口；可信度 medium/high：需具备资料来源、匹配理由和可复核证据。",
            "- 下一步建议：补充真实供应商库或联网检索结果后，按资质、案例、交付、价格、售后进行评分。",
        ]
    )


def build_chat_run_display_projection(
    *,
    kernel_context: dict[str, Any],
    mode: str | None,
    session_id: str,
    user_message: str,
    assistant_message: str = "",
) -> tuple[str, dict[str, Any]]:
    """Build a visible response only when FLARE returns no usable text."""
    sourcing_payload = build_sourcing_candidates_projection(
        kernel_context=kernel_context,
        mode=mode,
        session_id=session_id,
        user_message=user_message,
    )
    sourcing_text = _sourcing_message(sourcing_payload)
    if sourcing_text:
        return sourcing_text, {"sourcing_candidates": sourcing_payload}

    analysis_payload = build_analysis_report_projection(
        kernel_context=kernel_context,
        mode=mode,
        user_message=user_message,
        assistant_message=assistant_message,
    )
    analysis_text = _analysis_message(analysis_payload)
    if analysis_text:
        return analysis_text, {"analysis_payload": analysis_payload}

    intake_payload = build_intake_workbench_projection(
        pending_contract=None,
        mode=mode,
        session_id=session_id,
        user_message=user_message,
        candidate_context=kernel_context,
    )
    intake_text = _intake_message(intake_payload)
    if intake_text:
        return intake_text, {"canvas_state": _as_dict(intake_payload).get("canvas_payload")}

    return "", {}
