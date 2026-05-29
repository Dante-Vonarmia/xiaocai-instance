"""FLARE kernel request body assembly for xiaocai instance API."""

from __future__ import annotations

from typing import Any

from xiaocai_instance_api.chat.mode_contract import canonicalize_kernel_context
from xiaocai_instance_api.contracts.chat_contract import FLARE_PAYLOAD_EXTRA_CONTEXT_KEY


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _default_text(value: Any, fallback: str) -> str:
    resolved = _clean_text(value)
    return resolved or fallback


def build_kernel_request_body(
    *,
    user_id: str,
    message: str,
    session_id: str,
    context: dict[str, Any] | None,
    default_instance_id: str = "xiaocai",
    default_domain_pack_domain: str = "xiaocai",
    default_domain_pack_version: str = "default",
) -> dict[str, Any]:
    """Build the request body passed from instance API to FLARE kernel."""

    context_dict = canonicalize_kernel_context(context)
    payload_extra = context_dict.get(FLARE_PAYLOAD_EXTRA_CONTEXT_KEY)
    payload_extra_dict = dict(payload_extra) if isinstance(payload_extra, dict) else {}
    kernel_context = {
        key: value
        for key, value in context_dict.items()
        if key != FLARE_PAYLOAD_EXTRA_CONTEXT_KEY
    }
    instance_id = _default_text(context_dict.get("instance_id"), _default_text(default_instance_id, "xiaocai"))
    domain_pack_version = _default_text(
        context_dict.get("domain_pack_version"),
        _default_text(default_domain_pack_version, "default"),
    )
    domain_pack_domain = _default_text(
        context_dict.get("domain_pack_domain") or context_dict.get("domain"),
        _default_text(default_domain_pack_domain, "xiaocai"),
    )

    payload = {**kernel_context, **payload_extra_dict}
    payload.setdefault("instance_id", instance_id)
    payload.setdefault("domain_pack_version", domain_pack_version)
    payload.setdefault("domain_pack_domain", domain_pack_domain)
    payload["message"] = message

    request_body: dict[str, Any] = {
        "user_id": user_id,
        "message": message,
        "session_id": session_id,
        "context": kernel_context,
        "payload": payload,
    }

    for field in (
        "tenant_id",
        "instance_id",
        "domain_pack_version",
        "intent",
        "intent_override",
        "mode",
        "manual_mode",
        "current_mode",
        "project_id",
        "action_key",
        "target_mode",
        "action_status",
        "action_reason",
        "trace_id",
        "command",
        "run_id",
        "client_request_id",
        "question_id",
        "field_key",
        "field_value",
    ):
        value = payload.get(field, kernel_context.get(field))
        if value is not None:
            request_body[field] = value

    request_body.setdefault("instance_id", instance_id)
    request_body.setdefault("domain_pack_version", domain_pack_version)

    if "intent" not in request_body and isinstance(kernel_context.get("function_type"), str):
        request_body["intent"] = kernel_context.get("function_type")

    return request_body


__all__ = ["build_kernel_request_body"]
