from __future__ import annotations

from typing import Any

from xiaocai_instance_api.chat.local_orchestration import build_local_orchestration_response
from xiaocai_instance_api.contracts.chat_contract import ChatRunResponse


def build_chat_run_fallback_response(
    *,
    message: str,
    session_id: str,
    mode: str | None,
    empty_message: str,
) -> ChatRunResponse:
    result = build_local_orchestration_response(
        user_message=message,
        mode=mode,
        history_user_messages=None,
    )
    response_message = result.message.strip() if isinstance(result.message, str) else ""
    if not response_message:
        response_message = empty_message
    metadata = dict(result.metadata) if isinstance(result.metadata, dict) else {}
    if result.pending_contract:
        metadata["pending_contract"] = result.pending_contract
    return ChatRunResponse(
        message=response_message,
        session_id=session_id,
        cards=list(result.cards or []),
        metadata=metadata,
    )


def build_chat_stream_fallback_done_event(
    *,
    message: str,
    session_id: str,
    mode: str | None,
    empty_message: str,
) -> dict[str, Any]:
    response = build_chat_run_fallback_response(
        message=message,
        session_id=session_id,
        mode=mode,
        empty_message=empty_message,
    )
    return {
        "type": "done",
        "message": response.message,
        "session_id": response.session_id,
        "cards": response.cards,
        "metadata": response.metadata,
    }
