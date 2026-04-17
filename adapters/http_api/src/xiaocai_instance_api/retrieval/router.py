"""
检索路由（权限范围先行）
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.dependencies import get_current_auth_claims
from xiaocai_instance_api.security.authorization import get_authorization_service
from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.source_policy import build_retrieval_policy_signal
from xiaocai_instance_api.storage.source_store import get_source_store


router = APIRouter(prefix="/retrieval", tags=["retrieval"])


class RetrievalSearchRequest(BaseModel):
    project_id: str = Field(...)
    query: str = Field(default="")
    limit: int = Field(default=10, ge=1, le=100)


@router.post("/search")
async def retrieval_search(
    request: RetrievalSearchRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    scope = await authz.build_retrieval_scope(claims=claims, project_id=request.project_id)
    settings = get_settings()
    store = get_source_store(upload_root=settings.upload_root)
    records = await store.list_project_sources(
        user_id=claims.user_id,
        project_id=request.project_id,
        query=request.query.strip() or None,
    )
    hits = records[: request.limit]
    retrieval_policy = build_retrieval_policy_signal(records, limit=request.limit)
    return {
        "scope": scope.to_dict(),
        "retrieval_policy": retrieval_policy,
        "hits": [
            {
                "source_id": item.source_id,
                "project_id": item.project_id,
                "owner_user_id": item.owner_user_id,
                "visibility": item.visibility,
                "file_name": item.file_name,
                "folder_name": item.folder_name,
                "score": 1.0,
                "snippet": item.file_name,
            }
            for item in hits
        ],
    }


@router.get("/policy")
async def retrieval_policy(
    project_id: str,
    limit: int = 20,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_project_access(claims=claims, project_id=project_id)
    settings = get_settings()
    store = get_source_store(upload_root=settings.upload_root)
    records = await store.list_project_sources(
        user_id=claims.user_id,
        project_id=project_id,
        query=None,
    )
    return {
        "project_id": project_id,
        "policy": build_retrieval_policy_signal(records, limit=limit),
    }
