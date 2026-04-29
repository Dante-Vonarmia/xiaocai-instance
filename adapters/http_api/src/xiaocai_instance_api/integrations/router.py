from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from xiaocai_instance_api.integrations.contracts import (
    ConnectorEnabledPatchRequest,
    ConnectorRegistryCreateRequest,
    ConnectorRegistryItemContract,
    ConnectorRegistryListResponse,
    ConnectorRegistryPatchRequest,
    ConnectorRegistryReorderRequest,
    ConnectorStatusContract,
    DomainInjectionModePatchRequest,
    IntegrationStatusSummaryResponse,
    SearchSourcePoliciesResponse,
    SearchSourcePolicyContract,
    SearchSourcePolicyUpsertRequest,
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


@router.get("/settings/connector-registry", response_model=ConnectorRegistryListResponse)
async def get_connector_registry(
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> ConnectorRegistryListResponse:
    _ = claims
    service = get_integration_service()
    payload = await service.get_connector_registry()
    return ConnectorRegistryListResponse(connectors=[ConnectorRegistryItemContract(**item) for item in payload])


@router.post("/settings/connector-registry", response_model=ConnectorRegistryItemContract)
async def create_connector_registry_item(
    request: ConnectorRegistryCreateRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> ConnectorRegistryItemContract:
    service = get_integration_service()
    try:
        payload = await service.create_connector_registry_item(
            key=request.key,
            name=request.name,
            connector_type=request.connector_type,
            driver=request.driver,
            enabled=request.enabled,
            priority=request.priority,
            scope=request.scope,
            config_json=request.config_json,
            tags_json=request.tags_json,
            updated_by=claims.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ConnectorRegistryItemContract(**payload)


@router.patch("/settings/connector-registry/{connector_id}", response_model=ConnectorRegistryItemContract)
async def patch_connector_registry_item(
    connector_id: str,
    request: ConnectorRegistryPatchRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> ConnectorRegistryItemContract:
    service = get_integration_service()
    payload = await service.update_connector_registry_item(
        connector_id,
        name=request.name,
        enabled=request.enabled,
        priority=request.priority,
        scope=request.scope,
        config_json=request.config_json,
        tags_json=request.tags_json,
        updated_by=claims.user_id,
    )
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="connector not found")
    return ConnectorRegistryItemContract(**payload)


@router.put("/settings/connector-registry/order", response_model=ConnectorRegistryListResponse)
async def reorder_connector_registry(
    request: ConnectorRegistryReorderRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> ConnectorRegistryListResponse:
    service = get_integration_service()
    try:
        payload = await service.reorder_connector_registry_items(
            request.ordered_connector_ids,
            updated_by=claims.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ConnectorRegistryListResponse(connectors=[ConnectorRegistryItemContract(**item) for item in payload])


@router.post("/settings/connector-registry/{connector_id}/test", response_model=ConnectorRegistryItemContract)
async def test_connector_registry_item(
    connector_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> ConnectorRegistryItemContract:
    service = get_integration_service()
    payload = await service.test_connector_registry_item(connector_id, updated_by=claims.user_id)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="connector not found")
    return ConnectorRegistryItemContract(**payload)


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


@router.get("/settings/search-sources", response_model=SearchSourcePoliciesResponse)
async def get_search_source_policies(
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> SearchSourcePoliciesResponse:
    _ = claims
    service = get_integration_service()
    payload = await service.get_search_source_policies()
    return SearchSourcePoliciesResponse(policies=[SearchSourcePolicyContract(**item) for item in payload["policies"]])


@router.put("/settings/search-sources", response_model=SearchSourcePolicyContract)
async def upsert_search_source_policy(
    request: SearchSourcePolicyUpsertRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> SearchSourcePolicyContract:
    service = get_integration_service()
    try:
        payload = await service.upsert_search_source_policy(
            mode=request.mode,
            default_connector_key=request.default_connector_key,
            allow_fallback=request.allow_fallback,
            fallback_connector_keys=request.fallback_connector_keys,
            routing_rules=request.routing_rules,
            updated_by=claims.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return SearchSourcePolicyContract(**payload)


@router.get("/instance/integration-status", response_model=IntegrationStatusSummaryResponse)
async def get_instance_integration_status() -> IntegrationStatusSummaryResponse:
    service = get_integration_service()
    payload = await service.get_integration_status_summary()
    return IntegrationStatusSummaryResponse(**payload)
