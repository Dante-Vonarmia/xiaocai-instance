"""
统一权限服务
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.storage.ownership_store import get_ownership_store
from xiaocai_instance_api.storage.conversation_store import get_conversation_store
from xiaocai_instance_api.storage.source_store import get_source_store
from xiaocai_instance_api.storage.artifact_store import get_artifact_store
from xiaocai_instance_api.settings import get_settings


@dataclass(frozen=True)
class RetrievalScope:
    user_id: str
    tenant_id: str | None
    org_id: str | None
    project_id: str | None
    allow_private: bool
    allow_project_shared: bool

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "org_id": self.org_id,
            "project_id": self.project_id,
            "allow_private": self.allow_private,
            "allow_project_shared": self.allow_project_shared,
            "visibility_filter": {
                "owner_user_id": self.user_id,
                "project_shared_requires_membership": self.allow_project_shared,
            },
        }


class AuthorizationService:
    async def can_access_project(self, claims: AuthClaims, project_id: str) -> bool:
        if claims.has_role("admin"):
            return True
        store = get_ownership_store()
        return await store.check_project_access(user_id=claims.user_id, project_id=project_id)

    async def require_project_access(self, claims: AuthClaims, project_id: str) -> None:
        if await self.can_access_project(claims=claims, project_id=project_id):
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Project access denied: {project_id}",
        )

    async def can_access_conversation(self, claims: AuthClaims, conversation_id: str) -> bool:
        if claims.has_role("admin"):
            return True
        store = get_conversation_store()
        session = await store.get_session_for_user(user_id=claims.user_id, session_id=conversation_id)
        return session is not None

    async def require_conversation_access(self, claims: AuthClaims, conversation_id: str) -> None:
        if await self.can_access_conversation(claims=claims, conversation_id=conversation_id):
            return
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    async def can_write_conversation(self, claims: AuthClaims, conversation_id: str) -> bool:
        if claims.has_role("admin"):
            return True
        store = get_conversation_store()
        return await store.can_write_session(user_id=claims.user_id, session_id=conversation_id)

    async def require_conversation_write(self, claims: AuthClaims, conversation_id: str) -> None:
        if await self.can_write_conversation(claims=claims, conversation_id=conversation_id):
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conversation write denied")

    async def can_access_file(self, claims: AuthClaims, source_id: str) -> bool:
        if claims.has_role("admin"):
            return True
        settings = get_settings()
        store = get_source_store(upload_root=settings.upload_root)
        source = await store.get_source_for_user(user_id=claims.user_id, source_id=source_id)
        return source is not None

    async def require_file_access(self, claims: AuthClaims, source_id: str) -> None:
        if await self.can_access_file(claims=claims, source_id=source_id):
            return
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    async def can_write_file(self, claims: AuthClaims, source_id: str) -> bool:
        if claims.has_role("admin"):
            return True
        settings = get_settings()
        store = get_source_store(upload_root=settings.upload_root)
        return await store.can_write_source(user_id=claims.user_id, source_id=source_id)

    async def require_file_write(self, claims: AuthClaims, source_id: str) -> None:
        if await self.can_write_file(claims=claims, source_id=source_id):
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Source write denied")

    async def can_access_artifact(self, claims: AuthClaims, artifact_id: str) -> bool:
        if claims.has_role("admin"):
            return True
        store = get_artifact_store()
        record = await store.get_artifact_for_user(user_id=claims.user_id, artifact_id=artifact_id)
        return record is not None

    async def require_artifact_access(self, claims: AuthClaims, artifact_id: str) -> None:
        if await self.can_access_artifact(claims=claims, artifact_id=artifact_id):
            return
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    async def can_write_artifact(self, claims: AuthClaims, artifact_id: str) -> bool:
        if claims.has_role("admin"):
            return True
        store = get_artifact_store()
        return await store.can_write_artifact(user_id=claims.user_id, artifact_id=artifact_id)

    async def require_artifact_write(self, claims: AuthClaims, artifact_id: str) -> None:
        if await self.can_write_artifact(claims=claims, artifact_id=artifact_id):
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Artifact write denied")

    async def build_retrieval_scope(self, claims: AuthClaims, project_id: str | None) -> RetrievalScope:
        allow_project_shared = False
        if project_id:
            await self.require_project_access(claims=claims, project_id=project_id)
            allow_project_shared = True
        return RetrievalScope(
            user_id=claims.user_id,
            tenant_id=claims.tenant_id,
            org_id=claims.org_id,
            project_id=project_id,
            allow_private=True,
            allow_project_shared=allow_project_shared,
        )


_service = AuthorizationService()


def get_authorization_service() -> AuthorizationService:
    return _service
