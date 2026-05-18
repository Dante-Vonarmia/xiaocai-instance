"""FLARE mode contract normalization for outbound kernel requests."""

from __future__ import annotations

from typing import Any


LEGACY_INTAKE_MODE = "requirement_canvas"
CANONICAL_INTAKE_MODE = "requirement_intake"
MODE_FIELD_KEYS = ("mode", "manual_mode", "current_mode", "target_mode")


def canonicalize_kernel_context(context: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize legacy xiaocai mode aliases before crossing into FLARE."""
    context_dict = dict(context) if isinstance(context, dict) else {}
    for key in MODE_FIELD_KEYS:
        value = context_dict.get(key)
        if isinstance(value, str) and value.strip() == LEGACY_INTAKE_MODE:
            context_dict[key] = CANONICAL_INTAKE_MODE
    return context_dict
