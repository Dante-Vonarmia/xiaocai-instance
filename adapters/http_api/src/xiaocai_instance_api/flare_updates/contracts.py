from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


FlareUpdateAggregateStatus = Literal["aligned", "updates_available", "attention_required", "unknown"]


class FlarePackageStatus(BaseModel):
    registry: Literal["pypi"] = "pypi"
    package: str
    current: str | None = None
    latest: str | None = None
    source: str = "runtime"
    update_available: bool = False


class FlareRuntimeGateStatus(BaseModel):
    passed: bool
    reason: str | None = None
    current_question_projected: bool = False
    question_decision_projected: bool = False
    composer_chooser_projected: bool = False
    open_canvas_panel: bool | None = None
    error: str | None = None


class FlareUpdateStatusResponse(BaseModel):
    status: FlareUpdateAggregateStatus
    update_count: int
    packages: list[FlarePackageStatus]
    runtime_gate: FlareRuntimeGateStatus
