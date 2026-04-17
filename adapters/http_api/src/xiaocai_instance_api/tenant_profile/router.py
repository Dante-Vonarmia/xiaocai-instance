"""tenant profile 路由（无UI，仅配置读写）。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.dependencies import get_current_auth_claims
from xiaocai_instance_api.storage.tenant_profile_store import get_tenant_profile_store


router = APIRouter(prefix="/tenant-profile", tags=["tenant-profile"])


class TenantProfileUpsertRequest(BaseModel):
    tenant_id: str = Field(default="xiaocai-default")
    product_name: str = Field(default="xiaocai")
    logo_url: str = Field(default="")
    theme_primary: str = Field(default="#2563EB")
    theme_secondary: str = Field(default="#0EA5E9")
    feature_flags: dict[str, Any] = Field(default_factory=dict)


@router.get("")
async def get_tenant_profile(
    tenant_id: str = "xiaocai-default",
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    _ = claims
    store = get_tenant_profile_store()
    profile = await store.get_profile(tenant_id=tenant_id)
    return {
        "tenant_id": profile.tenant_id,
        "product_name": profile.product_name,
        "logo_url": profile.logo_url,
        "theme_primary": profile.theme_primary,
        "theme_secondary": profile.theme_secondary,
        "feature_flags": profile.feature_flags,
        "updated_at": profile.updated_at,
        "updated_by": profile.updated_by,
    }


@router.put("")
async def upsert_tenant_profile(
    request: TenantProfileUpsertRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    store = get_tenant_profile_store()
    profile = await store.upsert_profile(
        tenant_id=request.tenant_id,
        product_name=request.product_name,
        logo_url=request.logo_url,
        theme_primary=request.theme_primary,
        theme_secondary=request.theme_secondary,
        feature_flags=request.feature_flags,
        updated_by=claims.user_id,
    )
    return {
        "tenant_id": profile.tenant_id,
        "product_name": profile.product_name,
        "logo_url": profile.logo_url,
        "theme_primary": profile.theme_primary,
        "theme_secondary": profile.theme_secondary,
        "feature_flags": profile.feature_flags,
        "updated_at": profile.updated_at,
        "updated_by": profile.updated_by,
    }
