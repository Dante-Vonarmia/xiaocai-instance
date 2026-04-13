from __future__ import annotations

from typing import Dict, List

from .contract_loader import OrchestrationContracts
from .extractor import contains_any
from .types import LocalOrchestrationResult


def missing(required_fields: List[str], slots: Dict[str, str]) -> List[str]:
    return [field for field in required_fields if not slots.get(field)]


def build_pending_contract(missing_fields: List[str], mode: str | None) -> Dict[str, object] | None:
    if not missing_fields:
        return None
    first_missing = missing_fields[0]
    question_text = f"请补充字段：{first_missing}"
    return {
        "current_stage": "collecting",
        "command_type": "continue_collection",
        "missing_fields": missing_fields,
        "current_question": {
            "field_key": first_missing,
            "field_label": first_missing,
            "question_text": question_text,
            "options": [],
        },
        "question": {"field_key": first_missing, "question_text": question_text, "options": []},
        "chooser": {},
        "interaction_node": {"id": first_missing, "field_key": first_missing, "title": question_text},
        "next_actions": [{
            "action_key": "continue_collection",
            "label": "继续补充",
            "status": "available",
            "target_mode": mode or "requirement_canvas",
        }],
        "gate": {"status": "blocked", "reason": "missing_required_fields"},
        "summary_confirmed": False,
    }


def format_summary_lines(slots: Dict[str, str], fields: List[str]) -> List[str]:
    return [f"- {field}: {slots.get(field, '（未补充）')}" for field in fields]


def build_collection_result(
    slots: Dict[str, str],
    mode: str | None,
    contracts: OrchestrationContracts,
) -> LocalOrchestrationResult:
    required = contracts.stage_required.get("requirement-collection", [])
    missing_fields = missing(required, slots)
    pending_contract = build_pending_contract(missing_fields, mode=mode)
    if missing_fields:
        message = "\n".join(["已进入需求梳理。", "当前缺失字段如下：", *[f"- {field}" for field in missing_fields], "", f"请补充字段：{missing_fields[0]}"])
    else:
        message = "\n".join(["需求梳理已达到可分析状态。", "结构化需求摘要：", *format_summary_lines(slots, required), "", "下一步可执行：需求分析 / 智能寻源 / RFX策略。"])
    return LocalOrchestrationResult(
        message=message,
        cards=[{"type": "requirement_collection_summary", "required_fields": required, "missing_fields": missing_fields, "filled_fields": {k: v for k, v in slots.items() if k in required}}],
        metadata={"orchestration_source": "xiaocai_local_fallback", "intent": "collection"},
        pending_contract=pending_contract,
    )


def build_analysis_result(
    slots: Dict[str, str],
    mode: str | None,
    contracts: OrchestrationContracts,
) -> LocalOrchestrationResult:
    required = contracts.stage_required.get("requirement-analysis", [])
    missing_fields = missing(required, slots)
    pending_contract = build_pending_contract(missing_fields, mode=mode)
    lines = [
        "需求分析（会话内编排）",
        "基于需求分析必填集进行完整性校验。",
        "当前字段摘要：",
        *format_summary_lines(slots, required),
        "",
        "分析缺口字段：",
    ]
    lines.extend([f"- {field}" for field in missing_fields] if missing_fields else ["- 无"])
    return LocalOrchestrationResult(
        message="\n".join(lines),
        cards=[{"type": "requirement_analysis_summary", "required_fields": required, "missing_fields": missing_fields, "filled_fields": {k: v for k, v in slots.items() if k in required}}],
        metadata={"orchestration_source": "xiaocai_local_fallback", "intent": "analysis"},
        pending_contract=pending_contract,
    )


def suggest_rfx_type(message: str, contracts: OrchestrationContracts) -> str:
    allowed = contracts.rfx_allowed_types or ["RFP"]
    if contains_any(message, ["信息收集", "调研", "摸底"]) and "RFI" in allowed:
        return "RFI"
    if contains_any(message, ["报价", "比价", "询价"]) and "RFQ" in allowed:
        return "RFQ"
    if contains_any(message, ["投标", "竞标"]) and "RFB" in allowed:
        return "RFB"
    if "RFP" in allowed:
        return "RFP"
    return allowed[0]


def build_rfx_result(
    message: str,
    slots: Dict[str, str],
    mode: str | None,
    contracts: OrchestrationContracts,
) -> LocalOrchestrationResult:
    rfx_type = suggest_rfx_type(message, contracts=contracts)
    required = contracts.rfx_template_required.get(rfx_type) or contracts.stage_required.get("rfx-strategy", [])
    missing_fields = missing(required, slots)
    pending_contract = build_pending_contract(missing_fields, mode=mode)
    lines = [
        "RFX策略（会话内编排）",
        f"- 建议RFX类型: {rfx_type}",
        "- 依据: domain-pack/contracts/procurement-analysis-rfx-templates.yaml",
        "- 当前字段摘要：",
        *format_summary_lines(slots, required),
        "- RFX缺口字段：",
    ]
    lines.extend([f"- {field}" for field in missing_fields] if missing_fields else ["- 无"])
    return LocalOrchestrationResult(
        message="\n".join(lines),
        cards=[{"type": "rfx_strategy_summary", "rfx_type": rfx_type, "required_fields": required, "missing_fields": missing_fields}],
        metadata={"orchestration_source": "xiaocai_local_fallback", "intent": "rfx", "rfx_type": rfx_type},
        pending_contract=pending_contract,
    )


def build_sourcing_result(
    slots: Dict[str, str],
    mode: str | None,
    contracts: OrchestrationContracts,
) -> LocalOrchestrationResult:
    required = contracts.sourcing_required_fields
    missing_fields = missing(required, slots)
    pending_contract = build_pending_contract(missing_fields, mode=mode or "intelligent_sourcing")
    if missing_fields:
        message = "\n".join(["智能寻源前置字段不足，先补齐以下字段：", *[f"- {field}" for field in missing_fields], "", f"请补充字段：{missing_fields[0]}"])
    else:
        message = "\n".join(["智能寻源（会话内编排）", "已满足寻源前置字段。", "字段摘要：", *format_summary_lines(slots, required)])
    return LocalOrchestrationResult(
        message=message,
        cards=[{"type": "sourcing_strategy_summary", "required_fields": required, "missing_fields": missing_fields}],
        metadata={"orchestration_source": "xiaocai_local_fallback", "intent": "sourcing"},
        pending_contract=pending_contract,
    )
