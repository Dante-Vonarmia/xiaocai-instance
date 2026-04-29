from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DomainInjectionMode = Literal["off", "assist", "enforce"]
ConnectorStatusType = Literal["connected", "disconnected", "error"]
ConnectorType = Literal["database", "knowledge", "search", "mcp"]


class ConnectorStatusContract(BaseModel):
    key: str
    name: str
    enabled: bool
    status: ConnectorStatusType
    health: str
    latency_ms: int | None = None
    last_success_at: str | None = None
    last_error: str = ""
    scope: str
    updated_at: str
    updated_by: str


class SettingsIntegrationsResponse(BaseModel):
    domain_injection_mode: DomainInjectionMode
    connectors: list[ConnectorStatusContract] = Field(default_factory=list)


class DomainInjectionModePatchRequest(BaseModel):
    domain_injection_mode: DomainInjectionMode


class ConnectorEnabledPatchRequest(BaseModel):
    enabled: bool


class ConnectorRegistryItemContract(BaseModel):
    connector_id: str
    key: str
    name: str
    connector_type: ConnectorType
    driver: str
    enabled: bool
    priority: int
    scope: str
    config_json: dict = Field(default_factory=dict)
    tags_json: list[str] = Field(default_factory=list)
    status: ConnectorStatusType
    health: str
    latency_ms: int | None = None
    last_success_at: str | None = None
    last_error: str = ""
    updated_at: str
    updated_by: str


class ConnectorRegistryListResponse(BaseModel):
    connectors: list[ConnectorRegistryItemContract] = Field(default_factory=list)


class ConnectorRegistryCreateRequest(BaseModel):
    key: str
    name: str
    connector_type: ConnectorType
    driver: str
    enabled: bool = True
    priority: int = 100
    scope: str = "read"
    config_json: dict = Field(default_factory=dict)
    tags_json: list[str] = Field(default_factory=list)


class ConnectorRegistryPatchRequest(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    priority: int | None = None
    scope: str | None = None
    config_json: dict | None = None
    tags_json: list[str] | None = None


class ConnectorRegistryReorderRequest(BaseModel):
    ordered_connector_ids: list[str] = Field(default_factory=list)


class SearchSourcePolicyContract(BaseModel):
    policy_id: str
    mode: str
    default_connector_key: str
    allow_fallback: bool
    fallback_connector_keys: list[str] = Field(default_factory=list)
    routing_rules: list[dict] = Field(default_factory=list)
    updated_at: str
    updated_by: str


class SearchSourcePoliciesResponse(BaseModel):
    policies: list[SearchSourcePolicyContract] = Field(default_factory=list)


class SearchSourcePolicyUpsertRequest(BaseModel):
    mode: str
    default_connector_key: str
    allow_fallback: bool = True
    fallback_connector_keys: list[str] = Field(default_factory=list)
    routing_rules: list[dict] = Field(default_factory=list)


class IntegrationStatusSummaryItem(BaseModel):
    key: str
    enabled: bool
    status: ConnectorStatusType
    health: str
    latency_ms: int | None = None
    updated_at: str


class IntegrationStatusSummaryResponse(BaseModel):
    connectors: list[IntegrationStatusSummaryItem] = Field(default_factory=list)
    generated_at: str
