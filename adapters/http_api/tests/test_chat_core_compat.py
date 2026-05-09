from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app


def _token(client: TestClient, user_id: str = "compat-user") -> str:
    response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": user_id})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_chat_core_lifecycle_archive_compat():
    client = TestClient(create_app())
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/chat/sessions",
        headers=headers,
        json={"function_type": "auto", "title": "Compat session"},
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["sessionId"]

    lifecycle_response = client.post(
        f"/chat/sessions/{session_id}/lifecycle",
        headers=headers,
        json={"action": "archive"},
    )
    assert lifecycle_response.status_code == 200
    assert lifecycle_response.json()["status"] == "archived"


def test_chat_core_list_events_compat_returns_sse():
    client = TestClient(create_app())
    token = _token(client)

    response = client.get(
        "/chat/list-events",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    assert "polling fallback" in response.text
