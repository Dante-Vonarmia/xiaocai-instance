from __future__ import annotations

import json
import logging
import time
import urllib.request
from importlib import metadata
from typing import Any

from xiaocai_instance_api.flare_updates.contracts import (
    FlarePackageStatus,
    FlareRuntimeGateStatus,
    FlareUpdateStatusResponse,
)

PYPI_PACKAGES = [
    "flare-engines",
    "flare-kernel",
    "flare-kernel-client-py",
    "flare-storage-adapters",
]
INLINE_REASON = "candidate_options_inlined_to_main_chain"
PROBE_MESSAGE = (
    "我需要在上海开展一个端午招商活动，用于和我负责的园区的客户进行客户维系，"
    "预计50人左右，帮我分别做室内室外的方案需求"
)
CACHE_TTL_SECONDS = 300

_CACHE: tuple[float, FlareUpdateStatusResponse] | None = None


def installed_version(package: str) -> str | None:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def latest_pypi_version(package: str) -> str | None:
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        with urllib.request.urlopen(url, timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    return str(payload.get("info", {}).get("version") or "").strip() or None


def resolve_package_statuses() -> list[FlarePackageStatus]:
    statuses: list[FlarePackageStatus] = []
    for package in PYPI_PACKAGES:
        current = installed_version(package)
        latest = latest_pypi_version(package)
        statuses.append(
            FlarePackageStatus(
                package=package,
                current=current,
                latest=latest,
                update_available=bool(current and latest and current != latest),
            )
        )
    return statuses


def _projected(value: Any) -> bool:
    return value not in (None, {})


def run_runtime_gate_probe() -> FlareRuntimeGateStatus:
    try:
        logging.getLogger("flare_kernel").setLevel(logging.WARNING)
        from flare_kernel.runtime.orchestration.mode.runtime import build_kernel_runtime

        runtime = build_kernel_runtime(
            trace_id="xiaocai-flare-update-status",
            tenant_id="tenant-xiaocai-flare-update-status",
            instance_id="xiaocai",
            domain_pack_version="default",
            session_id="session-xiaocai-flare-update-status",
            intent="auto",
            payload={"domain": "xiaocai", "message": PROBE_MESSAGE},
            instance_profile=None,
        )
    except Exception as exc:
        return FlareRuntimeGateStatus(passed=False, error=str(exc))

    payload = runtime.get("payload") or {}
    gate = runtime.get("boundary_intent_gate") or {}
    next_action = gate.get("next_action") or {}
    pre_workspace_gate = gate.get("pre_workspace_gate") or {}
    current_question_projected = _projected(payload.get("current_question"))
    question_decision_projected = _projected(payload.get("question_decision"))
    composer_chooser_projected = _projected(payload.get("composer_chooser_policy"))
    open_canvas_panel = pre_workspace_gate.get("open_canvas_panel")
    reason = next_action.get("reason")
    passed = (
        not current_question_projected
        and not question_decision_projected
        and not composer_chooser_projected
        and reason == INLINE_REASON
        and open_canvas_panel is False
    )
    return FlareRuntimeGateStatus(
        passed=passed,
        reason=reason if isinstance(reason, str) else None,
        current_question_projected=current_question_projected,
        question_decision_projected=question_decision_projected,
        composer_chooser_projected=composer_chooser_projected,
        open_canvas_panel=open_canvas_panel if isinstance(open_canvas_panel, bool) else None,
    )


def _aggregate_status(
    packages: list[FlarePackageStatus],
    runtime_gate: FlareRuntimeGateStatus,
) -> str:
    if not runtime_gate.passed:
        return "attention_required"
    if any(package.update_available for package in packages):
        return "updates_available"
    if any(package.latest is None for package in packages):
        return "unknown"
    return "aligned"


def get_flare_update_status() -> FlareUpdateStatusResponse:
    global _CACHE
    now = time.time()
    if _CACHE and now - _CACHE[0] < CACHE_TTL_SECONDS:
        return _CACHE[1]

    packages = resolve_package_statuses()
    runtime_gate = run_runtime_gate_probe()
    response = FlareUpdateStatusResponse(
        status=_aggregate_status(packages, runtime_gate),
        update_count=sum(1 for package in packages if package.update_available),
        packages=packages,
        runtime_gate=runtime_gate,
    )
    _CACHE = (now, response)
    return response
