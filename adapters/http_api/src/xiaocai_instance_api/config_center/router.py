from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from xiaocai_instance_api.config_center.contracts import (
    ConfigDraftDeleteResponse,
    ConfigDraftContract,
    ConfigDraftLookupResponse,
    ConfigDraftUpsertRequest,
)
from xiaocai_instance_api.config_center.service import get_config_center_service
from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.dependencies import get_current_auth_claims


router = APIRouter(prefix="/settings/config-drafts", tags=["config-center"])


@router.get("/{config_key}", response_model=ConfigDraftLookupResponse)
async def get_config_draft(
    config_key: str,
    scope: str = Query(default="default"),
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> ConfigDraftLookupResponse:
    _ = claims
    service = get_config_center_service()
    try:
        payload = await service.get_draft(config_key=config_key, scope=scope)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    draft = ConfigDraftContract(**payload) if payload else None
    return ConfigDraftLookupResponse(draft=draft)


@router.put("/{config_key}", response_model=ConfigDraftContract)
async def upsert_config_draft(
    config_key: str,
    request: ConfigDraftUpsertRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> ConfigDraftContract:
    service = get_config_center_service()
    try:
        payload = await service.upsert_draft(
            config_key=config_key,
            scope=request.scope,
            payload=request.payload,
            base_version=request.base_version,
            updated_by=claims.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ConfigDraftContract(**payload)


@router.delete("/{config_key}", response_model=ConfigDraftDeleteResponse)
async def delete_config_draft(
    config_key: str,
    scope: str = Query(default="default"),
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> ConfigDraftDeleteResponse:
    _ = claims
    service = get_config_center_service()
    try:
        deleted = await service.delete_draft(config_key=config_key, scope=scope)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ConfigDraftDeleteResponse(deleted=deleted)
