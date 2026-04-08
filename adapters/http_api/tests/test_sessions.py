from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def _auth_token(client: TestClient, user_id: str = "session-user") -> str:
    response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": user_id})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_session_create_and_list(client):
    token = _auth_token(client)
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-s-1"},
    )
    assert bind_response.status_code == 200

    create_response = client.post(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-s-1", "title": "会话A", "function_type": "requirement_canvas"},
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["sessionId"]

    list_response = client.get(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
        params={"project_id": "proj-s-1"},
    )
    assert list_response.status_code == 200
    sessions = list_response.json()["sessions"]
    assert any(item["sessionId"] == session_id for item in sessions)


def test_chat_run_writes_messages(client):
    token = _auth_token(client, user_id="chat-session-user")
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-chat-1"},
    )
    assert bind_response.status_code == 200

    session_response = client.post(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-chat-1", "title": "聊天会话"},
    )
    session_id = session_response.json()["sessionId"]

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "这是助手回复",
            "cards": [],
            "session_id": session_id,
            "metadata": {},
        }
        run_response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "你好",
                "session_id": session_id,
                "context": {"project_id": "proj-chat-1"},
            },
        )
    assert run_response.status_code == 200

    messages_response = client.get(
        f"/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert messages_response.status_code == 200
    messages = messages_response.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_session_list_pagination_and_delete(client):
    token = _auth_token(client, user_id="page-user")
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-page-1"},
    )
    assert bind_response.status_code == 200

    created_ids: list[str] = []
    for idx in range(3):
        response = client.post(
            "/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_id": "proj-page-1", "title": f"会话-{idx}"},
        )
        assert response.status_code == 200
        created_ids.append(response.json()["sessionId"])

    page_1 = client.get(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
        params={"project_id": "proj-page-1", "page": 1, "page_size": 2, "group_by_time": "true"},
    )
    assert page_1.status_code == 200
    body_1 = page_1.json()
    assert len(body_1["sessions"]) == 2
    assert body_1["pagination"]["total"] == 3
    assert body_1["pagination"]["total_pages"] == 2
    assert "today" in body_1["grouped"]

    page_2 = client.get(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
        params={"project_id": "proj-page-1", "page": 2, "page_size": 2},
    )
    assert page_2.status_code == 200
    assert len(page_2.json()["sessions"]) == 1

    delete_response = client.delete(
        f"/sessions/{created_ids[0]}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


def test_session_mode_persistence(client):
    token = _auth_token(client, user_id="mode-persist-user")
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-mode-persist"},
    )
    assert bind_response.status_code == 200

    create_response = client.post(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": "proj-mode-persist",
            "title": "模式会话",
            "mode": "requirement_canvas",
        },
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["sessionId"]
    assert create_response.json()["mode"] == "requirement_canvas"

    get_response = client.get(
        f"/sessions/{session_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["mode"] == "requirement_canvas"
