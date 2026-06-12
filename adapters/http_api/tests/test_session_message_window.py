from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app


def _auth_token(client: TestClient, user_id: str = "message-window-user") -> str:
    response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": user_id})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_message_window_loads_latest_and_older_messages():
    client = TestClient(create_app())
    token = _auth_token(client)
    create_response = client.post(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "窗口会话", "function_type": "auto"},
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["sessionId"]

    for index in range(1, 4):
        append_response = client.post(
            f"/sessions/{session_id}/messages/append",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_message": f"user-{index}",
                "assistant_message": f"assistant-{index}",
            },
        )
        assert append_response.status_code == 200

    latest_response = client.get(
        f"/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 2},
    )
    assert latest_response.status_code == 200
    latest_payload = latest_response.json()
    assert [item["content"] for item in latest_payload["messages"]] == ["user-3", "assistant-3"]
    assert latest_payload["window"]["mode"] == "latest"
    assert latest_payload["window"]["has_older"] is True
    assert latest_payload["window"]["next_before"]

    older_response = client.get(
        f"/chat/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 2, "before": latest_payload["window"]["next_before"]},
    )
    assert older_response.status_code == 200
    older_payload = older_response.json()
    assert [item["content"] for item in older_payload["messages"]] == ["user-2", "assistant-2"]
    assert older_payload["window"]["mode"] == "before"
