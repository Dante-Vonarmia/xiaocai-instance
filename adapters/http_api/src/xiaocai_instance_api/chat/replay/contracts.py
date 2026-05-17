from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ReplayKind = Literal["run", "stream"]
ReplayStatus = Literal["started", "ok", "error"]


class ReplayManifest(BaseModel):
    """Stable metadata for one kernel-boundary replay capture."""

    schema_version: str = Field(default="xiaocai.chat_replay.v1")
    capture_id: str
    kind: ReplayKind
    status: ReplayStatus = "started"
    created_at: str
    finished_at: str | None = None
    user_id: str
    session_id: str
    kernel_url: str
    request_body: dict[str, Any]
    event_count: int = 0
    error: str | None = None


class ReplayEvent(BaseModel):
    """One append-only event in a replay JSONL log."""

    ts: str
    event_type: str
    payload: Any


class ReplaySummary(BaseModel):
    capture_id: str
    kind: ReplayKind
    status: ReplayStatus
    created_at: str
    finished_at: str | None = None
    user_id: str
    session_id: str
    event_count: int = 0
    error: str | None = None


class ReplayExport(BaseModel):
    manifest: ReplayManifest
    events_jsonl: str
    replay_mjs: str
