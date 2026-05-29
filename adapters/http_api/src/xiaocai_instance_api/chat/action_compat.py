"""FLARE chat-core action compatibility route."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from xiaocai_instance_api.chat.kernel_action_client import call_kernel_action
from xiaocai_instance_api.contracts.chat_contract import ChatActionRequest
from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.authorization import get_authorization_service
from xiaocai_instance_api.security.dependencies import get_current_auth_claims


router = APIRouter(prefix="/chat", tags=["chat-compat"])


def _session_id(request: ChatActionRequest) -> str:
    resolved = str(request.session_id or "").strip()
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required for chat action",
        )
    return resolved


@router.post("/action")
async def chat_action(
    request: ChatActionRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    """Bridge chat-core `/chat/action` calls to FLARE kernel `/kernel/action`."""
    session_id = _session_id(request)
    authz = get_authorization_service()
    await authz.require_conversation_write(claims=claims, conversation_id=session_id)
    return await call_kernel_action(
        user_id=claims.user_id,
        message=request.message,
        session_id=session_id,
        context=request.context,
    )


__all__ = ["router"]
