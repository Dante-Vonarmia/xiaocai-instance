"""Session turn admission for xiaocai chat streaming."""

import asyncio
import json
from dataclasses import dataclass


STREAM_BUSY_MESSAGE = "上一条消息仍在处理中，请等回复完成后再发送。"


@dataclass(frozen=True)
class StreamTurnAdmission:
    session_id: str
    accepted: bool


class StreamTurnRegistry:
    """Owns API-local stream admission before requests enter FLARE kernel."""

    def __init__(self) -> None:
        self._active_session_ids: set[str] = set()
        self._lock = asyncio.Lock()

    async def try_acquire(self, session_id: str) -> StreamTurnAdmission:
        normalized_session_id = session_id.strip()
        if not normalized_session_id:
            return StreamTurnAdmission(session_id="", accepted=True)
        async with self._lock:
            if normalized_session_id in self._active_session_ids:
                return StreamTurnAdmission(session_id=normalized_session_id, accepted=False)
            self._active_session_ids.add(normalized_session_id)
            return StreamTurnAdmission(session_id=normalized_session_id, accepted=True)

    async def release(self, session_id: str) -> None:
        normalized_session_id = session_id.strip()
        if not normalized_session_id:
            return
        async with self._lock:
            self._active_session_ids.discard(normalized_session_id)


_registry = StreamTurnRegistry()


def get_stream_turn_registry() -> StreamTurnRegistry:
    return _registry


def build_stream_busy_events(session_id: str) -> list[tuple[str, dict]]:
    return [
        (
            "content",
            {
                "type": "content",
                "channel": "assistant",
                "content": STREAM_BUSY_MESSAGE,
                "session_id": session_id,
                "transient": True,
            },
        ),
        (
            "complete",
            {
                "type": "complete",
                "status": "busy",
                "message": STREAM_BUSY_MESSAGE,
                "session_id": session_id,
                "transient": True,
            },
        ),
    ]


def serialize_sse_event(event_type: str, payload: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
