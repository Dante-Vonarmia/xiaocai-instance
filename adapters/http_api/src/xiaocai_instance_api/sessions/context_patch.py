"""Session context patch merge helpers."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any

from flare_kernel.contracts.context import ContextContract, create_empty_context


def _mapping(value: Any) -> dict[str, Any]:
    match value:
        case dict():
            return value
        case str() if value.strip():
            try:
                loaded = json.loads(value)
            except json.JSONDecodeError:
                return {}
            return loaded if isinstance(loaded, dict) else {}
        case _:
            return {}


def _artifact_id(item: dict[str, Any]) -> str:
    return str(item.get("artifact_id") or "").strip()


def _artifact_rows(value: Any) -> list[dict[str, Any]]:
    match value:
        case list():
            return [dict(item) for item in value if isinstance(item, dict) and _artifact_id(item)]
        case _:
            return []


def normalize_session_context(value: Any) -> dict[str, Any]:
    """Normalize stored session context through FLARE's canonical contract."""
    base = _mapping(value) or create_empty_context().model_dump(mode="python")
    return ContextContract.model_validate(base).model_dump(mode="python")


def merge_session_context_patch(
    context: Any,
    context_patch: Any,
) -> dict[str, Any] | None:
    """Merge supported FLARE context patches into xiaocai session context."""
    patch_artifacts = _artifact_rows(_mapping(context_patch).get("artifact_context"))
    if not patch_artifacts:
        return None

    base = normalize_session_context(context)
    existing_artifacts = _artifact_rows(base.get("artifact_context"))
    merged_by_id = {
        **{_artifact_id(item): item for item in existing_artifacts},
        **{_artifact_id(item): item for item in patch_artifacts},
    }
    return {
        **base,
        "artifact_context": list(merged_by_id.values()),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


__all__ = ["merge_session_context_patch", "normalize_session_context"]
