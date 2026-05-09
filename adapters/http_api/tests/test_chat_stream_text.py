from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def auth_token(client):
    response = client.post(
        "/auth/exchange",
        json={"mock": True, "mock_user_id": "test-user"},
    )
    return response.json()["access_token"]


def test_chat_stream_deduplicates_repeated_content_snapshots(client, auth_token):
    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {"type": "content", "content": "好的，请补充预算范围。"}
            yield {"type": "content", "content": "好的，请补充预算范围。"}
            yield {"type": "complete"}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "先补关键字段",
                "session_id": "sess-stream-dedupe",
            },
        )

    assert response.status_code == 200
    assert response.text.count("好的，请补充预算范围。") == 2

    messages_response = client.get(
        "/sessions/sess-stream-dedupe/messages",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert messages_response.status_code == 200
    messages = messages_response.json()["messages"]
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "好的，请补充预算范围。"


def test_chat_core_message_writeback_compatibility(client, auth_token):
    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {"type": "content", "content": "已收到。"}
            yield {"type": "complete"}

        mock_stream.return_value = mock_generator()

        stream_response = client.post(
            "/chat/stream",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "command": "send_message",
                "payload": {"message": "测试 core 写回"},
                "session_id": "sess-core-writeback",
            },
        )

    assert stream_response.status_code == 200

    before_writeback = client.get(
        "/chat/sessions/sess-core-writeback/messages",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert before_writeback.status_code == 200
    assert before_writeback.json()["messages"] == []

    writeback_response = client.post(
        "/chat/sessions/sess-core-writeback/messages",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "user_message": "测试 core 写回",
            "assistant_message": "已收到。",
        },
    )
    assert writeback_response.status_code == 200

    messages_response = client.get(
        "/chat/sessions/sess-core-writeback/messages",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    messages = messages_response.json()["messages"]
    assert [item["role"] for item in messages] == ["user", "assistant"]
    assert messages[1]["content"] == "已收到。"
