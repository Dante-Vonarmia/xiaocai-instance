from __future__ import annotations


INTAKE_MODE_ALIAS = "requirement_canvas"
INTAKE_MODE_PREFIX = "requirement_intake"

PROCUREMENT_TERMS = ("采购", "寻购", "询价", "供应商")
INTAKE_TERMS = ("需求梳理", "梳理需求", "采购需求", "需求说明", "需求收集")
DOWNSTREAM_TERMS = ("寻源", "供应商", "报价", "比价", "需求分析", "分析报告", "RFX")


def is_intake_mode(mode: str | None) -> bool:
    if not isinstance(mode, str):
        return False
    normalized = mode.strip()
    return normalized == INTAKE_MODE_ALIAS or normalized.startswith(INTAKE_MODE_PREFIX)


def _clean_mode(mode: str | None) -> str | None:
    return mode.strip() if isinstance(mode, str) and mode.strip() else None


def _looks_like_intake_request(message: str) -> bool:
    text = message.strip()
    if not text:
        return False
    has_intake_term = any(term in text for term in INTAKE_TERMS)
    has_procurement_term = any(term in text for term in PROCUREMENT_TERMS)
    has_downstream_term = any(term in text for term in DOWNSTREAM_TERMS)
    return has_intake_term or (has_procurement_term and not has_downstream_term)


def resolve_effective_mode(
    *,
    request_mode: str | None,
    session_mode: str | None,
    message: str,
) -> str | None:
    """Resolve xiaocai product mode before calling FLARE runtime."""
    normalized_request_mode = _clean_mode(request_mode)
    normalized_session_mode = _clean_mode(session_mode)

    if normalized_request_mode and normalized_request_mode != "auto":
        return normalized_request_mode
    if normalized_request_mode == "auto":
        return "auto"
    if is_intake_mode(normalized_session_mode):
        return normalized_session_mode
    if _looks_like_intake_request(message):
        return INTAKE_MODE_ALIAS
    return normalized_request_mode or normalized_session_mode
