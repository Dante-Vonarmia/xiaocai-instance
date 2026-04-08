from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.settings import get_settings


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def _token_for(client: TestClient, user_id: str) -> str:
    response = client.post(
        "/auth/exchange",
        json={"mock": True, "mock_user_id": user_id},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_project_bind_and_list(client):
    token = _token_for(client, "user-a")
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-123"},
    )
    assert bind_response.status_code == 200

    mine_response = client.get(
        "/projects/mine",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert mine_response.status_code == 200
    assert "proj-123" in mine_response.json()["project_ids"]


def test_chat_requires_project_ownership(client):
    owner_token = _token_for(client, "owner-user")
    stranger_token = _token_for(client, "stranger-user")

    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"project_id": "proj-abc"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "ok",
            "cards": [],
            "session_id": "session-1",
            "metadata": {},
        }

        owner_chat_response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "message": "owner request",
                "session_id": "session-1",
                "context": {"project_id": "proj-abc"},
            },
        )
        assert owner_chat_response.status_code == 200

        stranger_chat_response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {stranger_token}"},
            json={
                "message": "stranger request",
                "session_id": "session-2",
                "context": {"project_id": "proj-abc"},
            },
        )
        assert stranger_chat_response.status_code == 403


def test_project_usage_summary(client, monkeypatch):
    monkeypatch.setenv("DAILY_MESSAGE_LIMIT", "5")
    monkeypatch.setenv("DAILY_PROJECT_MESSAGE_LIMIT", "3")
    get_settings.cache_clear()

    token = _token_for(client, "usage-user")
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-usage"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "ok",
            "cards": [],
            "session_id": "sess-usage",
            "metadata": {},
        }
        for idx in range(2):
            response = client.post(
                "/chat/run",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "message": f"msg-{idx}",
                    "session_id": "sess-usage",
                    "context": {"project_id": "proj-usage"},
                },
            )
            assert response.status_code == 200

    usage_response = client.get(
        "/projects/usage",
        headers={"Authorization": f"Bearer {token}"},
        params={"project_id": "proj-usage"},
    )
    assert usage_response.status_code == 200
    body = usage_response.json()
    assert body["daily_message_limit"] == 5
    assert body["daily_message_used"] == 2
    assert body["daily_message_remaining"] == 3
    assert body["daily_project_message_limit"] == 3
    assert body["daily_project_message_used"] == 2
    assert body["daily_project_message_remaining"] == 1

    get_settings.cache_clear()
