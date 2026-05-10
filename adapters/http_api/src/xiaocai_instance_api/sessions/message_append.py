"""Session message append routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.authorization import get_authorization_service
from xiaocai_instance_api.security.dependencies import get_current_auth_claims
from xiaocai_instance_api.sessions.title_compat import apply_auto_title_after_exchange
from xiaocai_instance_api.storage.conversation_store import get_conversation_store


router = APIRouter(prefix="/sessions", tags=["sessions"])
chat_compat_router = APIRouter(prefix="/chat", tags=["chat-compat"])


class AppendExchangeRequest(BaseModel):
    user_message: str
    assistant_message: str


class AppendExchangeResponse(BaseModel):
    success: bool


async def append_exchange(
    session_id: str,
    request: AppendExchangeRequest,
    claims: AuthClaims,
) -> AppendExchangeResponse:
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
    await apply_auto_title_after_exchange(
        store=store,
        user_id=claims.user_id,
        session_id=session_id,
        user_message=request.user_message,
        assistant_message=request.assistant_message,
    )
    return AppendExchangeResponse(success=True)


@router.post("/{session_id}/messages/append", response_model=AppendExchangeResponse)
async def append_session_exchange(
    session_id: str,
    request: AppendExchangeRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> AppendExchangeResponse:
    return await append_exchange(
        session_id=session_id,
        request=request,
        claims=claims,
    )


@chat_compat_router.post("/sessions/{session_id}/messages/append", response_model=AppendExchangeResponse)
async def append_chat_exchange(
    session_id: str,
    request: AppendExchangeRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> AppendExchangeResponse:
    return await append_exchange(
        session_id=session_id,
        request=request,
        claims=claims,
    )
