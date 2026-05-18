import pytest

from xiaocai_instance_api.chat.stream_turn import (
    STREAM_BUSY_MESSAGE,
    StreamTurnRegistry,
    build_stream_busy_events,
)


@pytest.mark.asyncio
async def test_stream_turn_registry_rejects_same_active_session():
    registry = StreamTurnRegistry()

    first = await registry.try_acquire("session-1")
    second = await registry.try_acquire("session-1")
    await registry.release("session-1")
    third = await registry.try_acquire("session-1")

    assert first.accepted is True
    assert second.accepted is False
    assert third.accepted is True


def test_stream_busy_events_are_transient():
    events = build_stream_busy_events("session-1")

    assert events[0][0] == "content"
    assert events[0][1]["content"] == STREAM_BUSY_MESSAGE
    assert events[0][1]["transient"] is True
    assert events[1][0] == "complete"
    assert events[1][1]["status"] == "busy"
    assert events[1][1]["transient"] is True
