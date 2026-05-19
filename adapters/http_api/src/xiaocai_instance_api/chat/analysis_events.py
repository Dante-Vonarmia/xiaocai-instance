"""SSE analysis payload helpers for xiaocai chat projection."""

from __future__ import annotations

from typing import Any


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def extract_analysis_payload(event: dict[str, Any]) -> dict[str, Any]:
    """Read analysis payload from direct or FLARE terminal-event shapes."""
    payload = _as_dict(event.get("payload"))
    for candidate in (
        event.get("analysis_payload"),
        payload.get("analysis_payload"),
        event.get("canvas_analysis_payload"),
        payload.get("canvas_analysis_payload"),
    ):
        if isinstance(candidate, dict):
            return candidate
    if event.get("type") == "analysis_payload":
        return event
    return {}


def with_analysis_payload(event: dict[str, Any], analysis_payload: dict[str, Any]) -> dict[str, Any]:
    """Attach structured analysis to the shape the current event already uses."""
    next_event = dict(event)
    payload = _as_dict(next_event.get("payload"))
    if "analysis_payload" in payload or (payload and "analysis_payload" not in next_event):
        next_event["payload"] = {**payload, "analysis_payload": analysis_payload}
        return next_event
    next_event["analysis_payload"] = analysis_payload
    return next_event
