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


def test_latest_message_window_is_capped_for_initial_load():
    client = TestClient(create_app())
    token = _auth_token(client, user_id="message-window-cap-user")
    create_response = client.post(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "窗口收敛会话", "function_type": "auto"},
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["sessionId"]

    for index in range(1, 6):
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
        params={"limit": 50},
    )
    assert latest_response.status_code == 200
    latest_payload = latest_response.json()
    assert [item["content"] for item in latest_payload["messages"]] == [
        "user-3",
        "assistant-3",
        "user-4",
        "assistant-4",
        "user-5",
        "assistant-5",
    ]
    assert latest_payload["window"]["mode"] == "latest"
    assert latest_payload["window"]["limit"] == 6
    assert latest_payload["window"]["has_older"] is True

    older_response = client.get(
        f"/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 50, "before": latest_payload["window"]["next_before"]},
    )
    assert older_response.status_code == 200
    older_payload = older_response.json()
    assert [item["content"] for item in older_payload["messages"]] == [
        "user-1",
        "assistant-1",
        "user-2",
        "assistant-2",
    ]
    assert older_payload["window"]["mode"] == "before"
    assert older_payload["window"]["limit"] == 50


def test_message_response_keeps_workflow_events_lazy():
    client = TestClient(create_app())
    token = _auth_token(client, user_id="message-window-events-user")
    create_response = client.post(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "事件瘦身会话", "function_type": "auto"},
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["sessionId"]

    append_response = client.post(
        f"/sessions/{session_id}/messages/append",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_message": "生成报告",
            "assistant_message": "已生成",
            "plan_payload": {
                "workflow_projection": {
                    "run_id": "run-1",
                    "phase": "complete",
                    "run_events": [
                        {"sequence": 1, "message": "large event payload 1"},
                        {"sequence": 2, "message": "large event payload 2"},
                    ],
                },
            },
        },
    )
    assert append_response.status_code == 200

    response = client.get(
        f"/chat/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 50},
    )
    assert response.status_code == 200
    assistant = response.json()["messages"][1]
    workflow_projection = assistant["workflow_projection"]
    plan_workflow_projection = assistant["plan_payload"]["workflow_projection"]
    assert workflow_projection["run_id"] == "run-1"
    assert workflow_projection["run_events_count"] == 2
    assert workflow_projection["run_events_lazy"] is True
    assert "run_events" not in workflow_projection
    assert "run_events" not in plan_workflow_projection


def test_large_message_response_uses_gzip():
    client = TestClient(create_app())
    token = _auth_token(client, user_id="message-window-gzip-user")
    create_response = client.post(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "gzip 会话", "function_type": "auto"},
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["sessionId"]

    append_response = client.post(
        f"/sessions/{session_id}/messages/append",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_message": "gzip", "assistant_message": "x" * 2048},
    )
    assert append_response.status_code == 200

    response = client.get(
        f"/sessions/{session_id}/messages",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept-Encoding": "gzip",
        },
        params={"limit": 50},
    )
    assert response.status_code == 200
    assert response.headers.get("content-encoding") == "gzip"
