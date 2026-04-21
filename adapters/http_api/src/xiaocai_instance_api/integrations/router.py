from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from xiaocai_instance_api.integrations.contracts import (
    ConnectorEnabledPatchRequest,
    ConnectorStatusContract,
    DomainInjectionModePatchRequest,
    IntegrationStatusSummaryResponse,
    SettingsIntegrationsResponse,
)
from xiaocai_instance_api.integrations.service import get_integration_service
from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.dependencies import get_current_auth_claims


router = APIRouter(tags=["integrations"])


@router.get("/settings/integrations", response_model=SettingsIntegrationsResponse)
async def get_settings_integrations(
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> SettingsIntegrationsResponse:
    _ = claims
    service = get_integration_service()
    payload = await service.get_integrations()
    return SettingsIntegrationsResponse(**payload)


@router.patch("/settings/domain-injection-mode", response_model=SettingsIntegrationsResponse)
async def patch_domain_injection_mode(
    request: DomainInjectionModePatchRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> SettingsIntegrationsResponse:
    service = get_integration_service()
    try:
        await service.set_domain_injection_mode(request.domain_injection_mode, updated_by=claims.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    payload = await service.get_integrations()
    return SettingsIntegrationsResponse(**payload)


@router.patch("/settings/connectors/{key}", response_model=ConnectorStatusContract)
async def patch_connector_enabled(
    key: str,
    request: ConnectorEnabledPatchRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> ConnectorStatusContract:
    service = get_integration_service()
    connector = await service.set_connector_enabled(key=key, enabled=request.enabled, updated_by=claims.user_id)
    if connector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="connector not found")
    return ConnectorStatusContract(**connector)


@router.post("/settings/connectors/{key}/test", response_model=ConnectorStatusContract)
async def test_connector(
    key: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> ConnectorStatusContract:
    service = get_integration_service()
    connector = await service.test_connector(key=key, updated_by=claims.user_id)
    if connector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="connector not found")
    return ConnectorStatusContract(**connector)


@router.get("/instance/integration-status", response_model=IntegrationStatusSummaryResponse)
async def get_instance_integration_status() -> IntegrationStatusSummaryResponse:
    service = get_integration_service()
    payload = await service.get_integration_status_summary()
    return IntegrationStatusSummaryResponse(**payload)
