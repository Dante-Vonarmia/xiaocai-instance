"""
FLARE chat-core message writeback compatibility routes.

The core package posts completed rounds to /chat/sessions/{id}/messages.
Keep this bridge separate from the main sessions router so the transport
compatibility concern does not enlarge the session route module.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.authorization import get_authorization_service
from xiaocai_instance_api.security.dependencies import get_current_auth_claims
from xiaocai_instance_api.storage.conversation_store import get_conversation_store


router = APIRouter(prefix="/chat", tags=["chat-compat"])


class ChatMessageWritebackRequest(BaseModel):
    user_message: str = Field(default="")
    assistant_message: str = Field(default="")
    artifacts: dict[str, Any] | None = None


@router.post("/sessions/{session_id}/messages")
async def append_chat_core_messages(
    session_id: str,
    request: ChatMessageWritebackRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_conversation_write(claims=claims, conversation_id=session_id)

    store = get_conversation_store()
    success = await store.append_exchange(
        user_id=claims.user_id,
        session_id=session_id,
        user_message=request.user_message,
        assistant_message=request.assistant_message,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"success": True}
