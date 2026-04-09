"""
分析产物路由
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.dependencies import get_current_auth_claims
from xiaocai_instance_api.security.authorization import get_authorization_service
from xiaocai_instance_api.storage.artifact_store import get_artifact_store
from xiaocai_instance_api.storage.conversation_store import get_conversation_store


router = APIRouter(prefix="/artifacts", tags=["artifacts"])


class ArtifactCreateRequest(BaseModel):
    artifact_type: str = Field(...)
    content: dict = Field(default_factory=dict)
    visibility: str = Field(default="private")


@router.get("")
async def list_artifacts(
    project_id: str | None = None,
    conversation_id: str | None = None,
    artifact_type: str | None = None,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    if project_id:
        await authz.require_project_access(claims=claims, project_id=project_id)
    if conversation_id:
        await authz.require_conversation_access(claims=claims, conversation_id=conversation_id)
    store = get_artifact_store()
    records = await store.list_artifacts(
        user_id=claims.user_id,
        project_id=project_id,
        conversation_id=conversation_id,
        artifact_type=artifact_type,
    )
    return {
        "artifacts": [
            {
                "id": item.artifact_id,
                "project_id": item.project_id,
                "conversation_id": item.conversation_id,
                "owner_user_id": item.owner_user_id,
                "visibility": item.visibility,
                "artifact_type": item.artifact_type,
                "content": item.content,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            for item in records
        ]
    }


@router.post("/conversations/{conversation_id}")
async def create_conversation_artifact(
    conversation_id: str,
    request: ArtifactCreateRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_conversation_write(claims=claims, conversation_id=conversation_id)
    conversation_store = get_conversation_store()
    session = await conversation_store.get_session_for_user(
        user_id=claims.user_id,
        session_id=conversation_id,
    )
    if session is None or not session.project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conversation project_id required")
    await authz.require_project_access(claims=claims, project_id=session.project_id)

    store = get_artifact_store()
    record = await store.create_artifact(
        user_id=claims.user_id,
        project_id=session.project_id,
        conversation_id=conversation_id,
        artifact_type=request.artifact_type,
        content=request.content,
        visibility="private" if request.visibility != "project_shared" else "project_shared",
    )
    return {
        "id": record.artifact_id,
        "project_id": record.project_id,
        "conversation_id": record.conversation_id,
        "owner_user_id": record.owner_user_id,
        "visibility": record.visibility,
        "artifact_type": record.artifact_type,
        "content": record.content,
        "created_at": record.created_at,
    }


@router.get("/{artifact_id}")
async def get_artifact_detail(
    artifact_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_artifact_access(claims=claims, artifact_id=artifact_id)
    store = get_artifact_store()
    record = await store.get_artifact_for_user(user_id=claims.user_id, artifact_id=artifact_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return {
        "id": record.artifact_id,
        "project_id": record.project_id,
        "conversation_id": record.conversation_id,
        "owner_user_id": record.owner_user_id,
        "visibility": record.visibility,
        "artifact_type": record.artifact_type,
        "content": record.content,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


@router.get("/{artifact_id}/export")
async def export_artifact(
    artifact_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_artifact_access(claims=claims, artifact_id=artifact_id)
    store = get_artifact_store()
    record = await store.get_artifact_for_user(user_id=claims.user_id, artifact_id=artifact_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return {
        "artifact_id": record.artifact_id,
        "artifact_type": record.artifact_type,
        "exported_at": record.updated_at,
        "content": record.content,
    }


@router.delete("/{artifact_id}")
async def delete_artifact(
    artifact_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_artifact_write(claims=claims, artifact_id=artifact_id)
    store = get_artifact_store()
    deleted = await store.delete_artifact(user_id=claims.user_id, artifact_id=artifact_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return {"deleted": True}
