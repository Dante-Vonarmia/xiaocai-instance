from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DomainInjectionMode = Literal["off", "assist", "enforce"]
ConnectorStatusType = Literal["connected", "disconnected", "error"]


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
