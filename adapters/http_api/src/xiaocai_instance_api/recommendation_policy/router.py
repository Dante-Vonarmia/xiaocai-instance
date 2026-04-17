"""推荐策略管理路由（无UI，仅配置读写）。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.dependencies import get_current_auth_claims
from xiaocai_instance_api.storage.recommendation_policy_store import get_recommendation_policy_store


router = APIRouter(prefix="/recommendation-policy", tags=["recommendation-policy"])


class RecommendationPolicyUpsertRequest(BaseModel):
    tenant_id: str = Field(default="xiaocai-default")
    overrides: dict[str, Any] = Field(default_factory=dict)


@router.get("")
async def get_recommendation_policy(
    tenant_id: str = "xiaocai-default",
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    _ = claims
    store = get_recommendation_policy_store()
    base_assets = store.load_base_assets()
    profile = await store.get_policy(tenant_id=tenant_id)
    return {
        "tenant_id": profile.tenant_id,
        "base_assets": {
            "shared_root": base_assets["shared_root"],
            "rules_path": base_assets["rules_path"],
            "registry_path": base_assets["registry_path"],
            "audit_schema_path": base_assets["audit_schema_path"],
            "registry": base_assets["registry"],
            "raw": base_assets["raw"],
        },
        "overrides": profile.overrides,
        "updated_at": profile.updated_at,
        "updated_by": profile.updated_by,
    }


@router.put("")
async def upsert_recommendation_policy(
    request: RecommendationPolicyUpsertRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    store = get_recommendation_policy_store()
    profile = await store.upsert_policy(
        tenant_id=request.tenant_id,
        overrides=request.overrides,
        updated_by=claims.user_id,
    )
    return {
        "tenant_id": profile.tenant_id,
        "overrides": profile.overrides,
        "updated_at": profile.updated_at,
        "updated_by": profile.updated_by,
    }
