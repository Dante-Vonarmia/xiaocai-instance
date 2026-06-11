"""Session message append routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.authorization import get_authorization_service
from xiaocai_instance_api.security.dependencies import get_current_auth_claims
from xiaocai_instance_api.sessions.title_compat import apply_auto_title_after_exchange
from xiaocai_instance_api.sessions.writeback_projection import (
    has_writeback_content,
    normalize_writeback_projection,
)
from xiaocai_instance_api.storage.conversation_store import get_conversation_store


router = APIRouter(prefix="/sessions", tags=["sessions"])
chat_compat_router = APIRouter(prefix="/chat", tags=["chat-compat"])


class AppendExchangeRequest(BaseModel):
    user_message: str
    assistant_message: str
    run_id: str = ""
    attachments: list[Any] = Field(default_factory=list)
    context_refs: list[Any] = Field(default_factory=list)
    knowledge_refs: list[Any] = Field(default_factory=list)
    agent_status: dict[str, Any] | None = None
    thinking_trace: str = ""
    execution_trace: dict[str, Any] | None = None
    knowledge_search: dict[str, Any] | None = None
    sourcing_candidates: dict[str, Any] | None = None
    knowledge_citation: dict[str, Any] | None = None
    canvas_state: dict[str, Any] | None = None
    analysis_payload: dict[str, Any] | None = None
    context_usage: dict[str, Any] | None = None
    provider_trace: dict[str, Any] | None = None
    context_authority: dict[str, Any] | None = None
    context_patch: dict[str, Any] | None = None
    plan_payload: dict[str, Any] | None = None
    workflow_projection: dict[str, Any] | None = None
    track_result: dict[str, Any] | None = None
    artifact_edit_request: dict[str, Any] | None = None


class AppendExchangeResponse(BaseModel):
    success: bool


async def append_exchange(
    session_id: str,
    request: AppendExchangeRequest,
    claims: AuthClaims,
) -> AppendExchangeResponse:
    authz = get_authorization_service()
    await authz.require_conversation_write(claims=claims, conversation_id=session_id)
    artifact_payload = normalize_writeback_projection(request.model_dump())
    if not has_writeback_content(artifact_payload):
        return AppendExchangeResponse(success=True)

    store = get_conversation_store()
    success = await store.append_exchange(
        user_id=claims.user_id,
        session_id=session_id,
        user_message=request.user_message,
        assistant_message=request.assistant_message,
        artifact_payload=artifact_payload,
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
