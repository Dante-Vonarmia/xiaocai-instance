"""
FLARE chat-core session lifecycle compatibility route.

Archive/restore requests from the reusable core are mapped to xiaocai's
existing session status transition without moving policy into the route.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.authorization import get_authorization_service
from xiaocai_instance_api.security.dependencies import get_current_auth_claims
from xiaocai_instance_api.storage.conversation_store import get_conversation_store


router = APIRouter(prefix="/chat", tags=["chat-compat"])


class SessionLifecycleRequest(BaseModel):
    action: str = Field(...)


def _status_for_action(action: str) -> str:
    normalized = str(action or "").strip().lower()
    if normalized == "archive":
        return "archived"
    if normalized == "restore":
        return "active"
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid lifecycle action: {action}")


@router.post("/sessions/{session_id}/lifecycle")
async def update_chat_session_lifecycle(
    session_id: str,
    request: SessionLifecycleRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_conversation_write(claims=claims, conversation_id=session_id)

    store = get_conversation_store()
    session = await store.update_session_fields(
        user_id=claims.user_id,
        session_id=session_id,
        status=_status_for_action(request.action),
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {
        "sessionId": session.session_id,
        "project_id": session.project_id,
        "user_id": session.user_id,
        "owner_user_id": session.owner_user_id,
        "visibility": session.visibility,
        "mode": session.mode,
        "function_type": session.function_type,
        "title": session.title,
        "status": session.status,
        "updatedAt": session.updated_at,
        "preview": session.preview,
    }
