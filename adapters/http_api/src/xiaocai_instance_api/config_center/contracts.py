from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ConfigDraftStatus = Literal["draft"]


class ConfigDraftContract(BaseModel):
    config_key: str
    scope: str
    payload: dict[str, Any] = Field(default_factory=dict)
    base_version: str = ""
    status: ConfigDraftStatus = "draft"
    updated_at: str
    updated_by: str


class ConfigDraftLookupResponse(BaseModel):
    draft: ConfigDraftContract | None = None


class ConfigDraftDeleteResponse(BaseModel):
    deleted: bool


class ConfigDraftUpsertRequest(BaseModel):
    scope: str = "default"
    payload: dict[str, Any] = Field(default_factory=dict)
    base_version: str = ""
