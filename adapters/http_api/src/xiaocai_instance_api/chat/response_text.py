"""Assistant response text normalization for xiaocai chat output."""

from __future__ import annotations

import re
from typing import Any


TEXT_EVENT_FIELDS = ("content", "delta", "chunk", "text", "message")
HTML_BREAK_RE = re.compile(r"(?i)(<br\s*/?>|&lt;br\s*/?&gt;)")


def normalize_assistant_display_text(value: str) -> str:
    """Keep provider HTML artifacts out of user-visible markdown."""
    if not value:
        return ""

    normalized_lines: list[str] = []
    for line in value.splitlines():
        replacement = "；" if "|" in line else "\n"
        normalized_lines.append(HTML_BREAK_RE.sub(replacement, line))
    return "\n".join(normalized_lines)


def replace_event_text(event: dict[str, Any], text: str) -> dict[str, Any]:
    """Replace the first text field used by FLARE stream events."""
    next_event = dict(event)
    for field in TEXT_EVENT_FIELDS:
        if isinstance(next_event.get(field), str):
            next_event[field] = text
            return next_event
    next_event["content"] = text
    return next_event
