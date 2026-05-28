from __future__ import annotations


INTAKE_MODE_ALIAS = "requirement_canvas"
INTAKE_MODE_PREFIX = "requirement_intake"


def is_intake_mode(mode: str | None) -> bool:
    if not isinstance(mode, str):
        return False
    normalized = mode.strip()
    return normalized == INTAKE_MODE_ALIAS or normalized.startswith(INTAKE_MODE_PREFIX)


def _clean_mode(mode: str | None) -> str | None:
    return mode.strip() if isinstance(mode, str) and mode.strip() else None


def resolve_effective_mode(
    *,
    request_mode: str | None,
    session_mode: str | None,
    message: str,
) -> str | None:
    """Resolve xiaocai product mode before calling FLARE runtime.

    Message text is intentionally ignored: product modes must be explicit.
    """
    _ = message
    normalized_request_mode = _clean_mode(request_mode)
    normalized_session_mode = _clean_mode(session_mode)

    if normalized_request_mode and normalized_request_mode != "auto":
        return normalized_request_mode
    if normalized_request_mode == "auto":
        return "auto"
    if is_intake_mode(normalized_session_mode):
        return None
    return normalized_request_mode or normalized_session_mode
