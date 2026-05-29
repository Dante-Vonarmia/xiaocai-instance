"""Normalize chat-core writeback artifacts into existing storage columns."""

from __future__ import annotations

from typing import Any


_TEXT_WRITEBACK_FIELDS = ("user_message", "assistant_message", "thinking_trace")
_ARTIFACT_WRITEBACK_FIELDS = (
    "attachments",
    "context_refs",
    "knowledge_refs",
    "agent_status",
    "execution_trace",
    "knowledge_search",
    "sourcing_candidates",
    "knowledge_citation",
    "canvas_state",
    "analysis_payload",
    "context_usage",
    "provider_trace",
    "context_authority",
    "plan_payload",
    "workflow_projection",
    "track_result",
    "artifact_edit_request",
    "artifacts",
)


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _has_value(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return value is not None


def _content_from_edit_request(edit_request: dict[str, Any]) -> str:
    for key in ("content", "canvas_content", "markdown", "text"):
        value = edit_request.get(key)
        if isinstance(value, str) and value.strip():
            return value
    patch = _as_dict(edit_request.get("patch"))
    value = patch.get("content")
    return value if isinstance(value, str) and value.strip() else ""


def normalize_writeback_projection(payload: dict[str, Any]) -> dict[str, Any]:
    """Map FLARE projection/edit payloads onto xiaocai's current columns."""
    normalized = dict(payload)
    plan_payload = dict(_as_dict(normalized.get("plan_payload")))
    workflow_projection = _as_dict(normalized.get("workflow_projection"))
    track_result = _as_dict(normalized.get("track_result"))
    if workflow_projection:
        plan_payload["workflow_projection"] = workflow_projection
    if track_result:
        plan_payload["track_result"] = track_result
    if plan_payload:
        normalized["plan_payload"] = plan_payload

    edit_request = _as_dict(normalized.get("artifact_edit_request"))
    if not edit_request:
        return normalized

    canvas_state = dict(_as_dict(normalized.get("canvas_state")))
    canvas_state["artifact_edit_request"] = edit_request
    content = _content_from_edit_request(edit_request)
    if content and not canvas_state.get("versions"):
        canvas_state["versions"] = [{"content": content}]
    normalized["canvas_state"] = canvas_state
    return normalized


def has_writeback_content(payload: dict[str, Any]) -> bool:
    """Reject no-op chat-core writebacks before they create blank turns."""
    return any(_has_value(payload.get(field)) for field in _TEXT_WRITEBACK_FIELDS) or any(
        _has_value(payload.get(field)) for field in _ARTIFACT_WRITEBACK_FIELDS
    )


__all__ = ["has_writeback_content", "normalize_writeback_projection"]
