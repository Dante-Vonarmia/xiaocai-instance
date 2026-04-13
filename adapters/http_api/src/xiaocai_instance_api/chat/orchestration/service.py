from __future__ import annotations

from typing import List

from .contract_loader import OrchestrationContracts, load_contracts
from .constants import DEFAULT_FALLBACK_STAGE_ORDER
from .extractor import detect_intent, extract_slots
from .flows import (
    build_analysis_result,
    build_collection_result,
    build_rfx_result,
    build_sourcing_result,
)
from .types import LocalOrchestrationResult


def _fallback_contracts() -> OrchestrationContracts:
    return OrchestrationContracts(
        stage_order=list(DEFAULT_FALLBACK_STAGE_ORDER),
        stage_required={
            "requirement-collection": ["采购目的", "使用场景", "一级品类", "二级品类", "交付地点"],
            "requirement-analysis": ["采购目的", "产品/服务", "质量标准", "验收口径"],
            "rfx-strategy": ["项目名称", "产品/服务", "RFX类型"],
        },
        sourcing_required_fields=["一级品类", "二级品类", "产品/服务", "交付地点"],
        rfx_allowed_types=["RFI", "RFQ", "RFP", "RFB"],
        rfx_template_required={},
    )


def build_local_orchestration_response(
    user_message: str,
    mode: str | None,
    history_user_messages: List[str] | None = None,
) -> LocalOrchestrationResult:
    try:
        contracts = load_contracts()
    except Exception:
        contracts = _fallback_contracts()

    history = history_user_messages or []
    merged = "\n".join([*history, user_message])
    slots = extract_slots(merged)
    intent = detect_intent(user_message, mode=mode)
    if intent == "analysis":
        return build_analysis_result(slots=slots, mode=mode, contracts=contracts)
    if intent == "rfx":
        return build_rfx_result(message=user_message, slots=slots, mode=mode, contracts=contracts)
    if intent == "sourcing":
        return build_sourcing_result(slots=slots, mode=mode, contracts=contracts)
    return build_collection_result(slots=slots, mode=mode, contracts=contracts)
