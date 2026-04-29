from __future__ import annotations

from typing import Any


def _build_route_steps(ordered_connector_keys: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "step_index": index + 1,
            "connector_key": key,
            "attempt_role": "primary" if index == 0 else "fallback",
        }
        for index, key in enumerate(ordered_connector_keys)
    ]


def _update_attempt_result(
    attempt_results: list[dict[str, Any]],
    *,
    step_index: int,
    status: str,
    success: bool | None = None,
    error: str | None = None,
    latency_ms: int | None = None,
) -> list[dict[str, Any]]:
    updated_results: list[dict[str, Any]] = []
    for item in attempt_results:
        current = dict(item)
        if current.get("step_index") == step_index:
            current["status"] = status
            current["success"] = success
            if error is not None:
                current["error"] = error
            if latency_ms is not None or status == "running":
                current["latency_ms"] = latency_ms
        updated_results.append(current)
    return updated_results


def build_initial_attempt_results(route_plan: dict[str, Any]) -> list[dict[str, Any]]:
    steps = route_plan.get("steps", []) if isinstance(route_plan, dict) else []
    return [
        {
            "step_index": step.get("step_index", index + 1),
            "connector_key": step.get("connector_key", ""),
            "attempt_role": step.get("attempt_role", "fallback"),
            "status": "pending",
            "success": None,
            "error": "",
            "latency_ms": None,
        }
        for index, step in enumerate(steps)
        if isinstance(step, dict)
    ]


def mark_attempt_running(
    attempt_results: list[dict[str, Any]],
    *,
    step_index: int,
) -> list[dict[str, Any]]:
    return _update_attempt_result(
        attempt_results,
        step_index=step_index,
        status="running",
        success=None,
        error="",
        latency_ms=None,
    )


def mark_attempt_success(
    attempt_results: list[dict[str, Any]],
    *,
    step_index: int,
    latency_ms: int | None = None,
) -> list[dict[str, Any]]:
    return _update_attempt_result(
        attempt_results,
        step_index=step_index,
        status="success",
        success=True,
        error="",
        latency_ms=latency_ms,
    )


def mark_attempt_failure(
    attempt_results: list[dict[str, Any]],
    *,
    step_index: int,
    error: str,
    latency_ms: int | None = None,
) -> list[dict[str, Any]]:
    return _update_attempt_result(
        attempt_results,
        step_index=step_index,
        status="failed",
        success=False,
        error=error,
        latency_ms=latency_ms,
    )


def build_simulated_attempt_results(
    route_plan: dict[str, Any],
    *,
    has_hits: bool,
) -> list[dict[str, Any]]:
    results = build_initial_attempt_results(route_plan)
    if not results:
        return results

    results = mark_attempt_running(results, step_index=1)
    if has_hits:
        results = mark_attempt_success(results, step_index=1)
        for index in range(1, len(results)):
            skipped = dict(results[index])
            skipped["status"] = "skipped"
            results[index] = skipped
        return results

    results = mark_attempt_failure(results, step_index=1, error="no_results")
    if len(results) < 2:
        return results

    results = mark_attempt_running(results, step_index=2)
    results = mark_attempt_failure(results, step_index=2, error="fallback_not_executed")
    return results


def build_search_route_plan(search_source_policy: dict[str, Any] | None) -> dict[str, Any]:
    resolved = dict(search_source_policy) if isinstance(search_source_policy, dict) else {}
    default_connector_key = str(resolved.get("default_connector_key") or "").strip()
    allow_fallback = bool(resolved.get("allow_fallback"))
    fallback_connector_keys = [
        item
        for item in resolved.get("fallback_connector_keys", [])
        if isinstance(item, str) and item.strip()
    ]

    ordered_connector_keys: list[str] = []
    if default_connector_key:
        ordered_connector_keys.append(default_connector_key)
    if allow_fallback:
        ordered_connector_keys.extend(
            key for key in fallback_connector_keys if key not in ordered_connector_keys
        )

    steps = _build_route_steps(ordered_connector_keys)
    return {
        "mode": str(resolved.get("mode") or "").strip(),
        "default_connector_key": default_connector_key,
        "allow_fallback": allow_fallback,
        "fallback_connector_keys": fallback_connector_keys,
        "ordered_connector_keys": ordered_connector_keys,
        "steps": steps,
        "routing_rules": resolved.get("routing_rules", []),
    }
