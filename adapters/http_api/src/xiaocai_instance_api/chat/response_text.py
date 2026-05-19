"""Assistant response text normalization for xiaocai chat output."""

from __future__ import annotations

import re
from typing import Any


TEXT_EVENT_FIELDS = ("content", "delta", "chunk", "text", "message")
HTML_BREAK_RE = re.compile(r"(?i)(<br\s*/?>|&lt;br\s*/?&gt;)")
UNSUPPORTED_INTERACTION_MARKERS = (
    "这个交互方式目前还没有开发到",
    "暂时不能直接完成",
    "我这边没有拿到完整的可展示结果",
    "你可以继续补充采购目标",
    "如果这是系统异常",
)


def is_unusable_assistant_display_text(value: str) -> bool:
    """Return true for runtime fallback text that should not reach users."""
    return bool(value and any(marker in value for marker in UNSUPPORTED_INTERACTION_MARKERS))


def normalize_assistant_display_text(value: str) -> str:
    """Keep provider HTML artifacts out of user-visible markdown."""
    if not value:
        return ""

    normalized_lines: list[str] = []
    for line in value.splitlines():
        replacement = "；" if "|" in line else "\n"
        normalized_lines.append(HTML_BREAK_RE.sub(replacement, line))
    normalized = "\n".join(normalized_lines)
    if is_unusable_assistant_display_text(normalized):
        return ""
    return normalized


def replace_event_text(event: dict[str, Any], text: str) -> dict[str, Any]:
    """Replace the first text field used by FLARE stream events."""
    next_event = dict(event)
    for field in TEXT_EVENT_FIELDS:
        if isinstance(next_event.get(field), str):
            next_event[field] = text
            return next_event
    next_event["content"] = text
    return next_event
