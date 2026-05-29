"""FLARE kernel action adapter for chat-core compatibility."""

from __future__ import annotations

from typing import Any

import httpx

from xiaocai_instance_api.chat.kernel_request_body import build_kernel_request_body
from xiaocai_instance_api.chat.replay.hooks import (
    append_kernel_capture,
    begin_kernel_capture,
    finish_kernel_capture,
)
from xiaocai_instance_api.settings import get_settings


def _kernel_action_url() -> str:
    settings = get_settings()
    return f"{settings.kernel_base_url}{settings.kernel_action_path}"


def _artifact_payload(result: dict[str, Any], result_payload: dict[str, Any]) -> dict[str, Any]:
    preserved: dict[str, Any] = {}
    for key in (
        "canvas_state",
        "analysis_payload",
        "canvas_analysis_payload",
        "workflow_projection",
        "plan_payload",
        "track_result",
        "mode_events",
    ):
        value = result.get(key) if key in result else result_payload.get(key)
        if value is not None:
            preserved[key] = value
    return preserved


def _normalize_action_result(result: dict[str, Any], session_id: str) -> dict[str, Any]:
    payload = result.get("result")
    result_payload = payload if isinstance(payload, dict) else {}
    message = (
        result.get("message")
        or result.get("reply")
        or result_payload.get("message")
        or result_payload.get("content_text")
        or ""
    )
    return {
        **result,
        **_artifact_payload(result, result_payload),
        "message": message,
        "session_id": result.get("session_id") or result_payload.get("session_id") or session_id,
    }


async def call_kernel_action(
    *,
    user_id: str,
    message: str,
    session_id: str,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    """Forward a chat-core action to FLARE kernel without route-side provider logic."""
    settings = get_settings()
    kernel_url = _kernel_action_url()
    request_body = build_kernel_request_body(
        user_id=user_id,
        message=message,
        session_id=session_id,
        context=context,
        default_instance_id=settings.flare_instance_id,
        default_domain_pack_domain=settings.flare_domain_pack_default_domain,
        default_domain_pack_version=settings.flare_domain_pack_version,
    )
    replay = begin_kernel_capture(
        kind="action",
        user_id=user_id,
        session_id=session_id,
        kernel_url=kernel_url,
        request_body=request_body,
    )
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(kernel_url, json=request_body, timeout=30.0)
            response.raise_for_status()
            result = response.json()
    except Exception as exc:
        append_kernel_capture(replay, "kernel.error", {"message": str(exc)})
        finish_kernel_capture(replay, status="error", error=str(exc))
        raise
    append_kernel_capture(replay, "kernel.response.raw", result)
    if not isinstance(result, dict):
        finish_kernel_capture(replay, status="error", error="Kernel response must be a JSON object")
        raise ValueError("Kernel response must be a JSON object")
    normalized = _normalize_action_result(result, session_id)
    append_kernel_capture(replay, "kernel.response.normalized", normalized)
    finish_kernel_capture(replay, status="ok")
    return normalized


__all__ = ["call_kernel_action"]
