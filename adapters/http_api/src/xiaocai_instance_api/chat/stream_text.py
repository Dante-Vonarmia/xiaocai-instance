from __future__ import annotations

from dataclasses import dataclass, field


TEXT_STREAM_EVENT_TYPES = {"content", "message", "text.delta", "token"}
TERMINAL_EVENT_TYPES = {"complete", "done"}
TEXT_EVENT_FIELDS = ("content", "delta", "chunk", "text", "message")


@dataclass
class StreamTextAccumulator:
    """Normalizes upstream text snapshots before they become chat truth."""

    chunks: list[str] = field(default_factory=list)
    emitted_text: str = ""

    def normalize_chunk(self, event_type: str, chunk: str) -> str:
        if not chunk or event_type in TERMINAL_EVENT_TYPES:
            return ""
        if event_type not in TEXT_STREAM_EVENT_TYPES:
            return chunk
        if chunk == self.emitted_text:
            return ""
        if self.emitted_text and chunk.startswith(self.emitted_text):
            return chunk[len(self.emitted_text):]
        return chunk

    def append(self, delta: str) -> None:
        if not delta:
            return
        self.chunks.append(delta)
        self.emitted_text += delta

    def normalize_event(
        self,
        *,
        event_type: str,
        event: dict,
        chunk: str,
    ) -> tuple[dict, str, bool]:
        delta = self.normalize_chunk(event_type=event_type, chunk=chunk)
        if event_type in TEXT_STREAM_EVENT_TYPES and chunk and not delta:
            return event, "", False
        if delta and delta != chunk:
            return _replace_text_field(event=event, delta=delta), delta, True
        return event, delta, True

    def final_message(self) -> str:
        return "".join(self.chunks).strip()


def _replace_text_field(*, event: dict, delta: str) -> dict:
    next_event = dict(event)
    for field in TEXT_EVENT_FIELDS:
        if isinstance(next_event.get(field), str):
            next_event[field] = delta
            return next_event
    next_event["content"] = delta
    return next_event
