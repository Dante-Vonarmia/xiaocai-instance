from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.chat.kernel_client import KernelClient
from xiaocai_instance_api.contracts.chat_contract import ChatStreamRequest


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


def test_chat_core_message_writeback_updates_default_session_title():
    client = TestClient(create_app())
    token = _token(client, user_id="compat-title-user")
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/chat/sessions",
        headers=headers,
        json={"function_type": "auto", "title": "新会话"},
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["sessionId"]

    append_response = client.post(
        f"/chat/sessions/{session_id}/messages",
        headers=headers,
        json={
            "user_message": "需要采购办公椅",
            "assistant_message": "已收到，我会继续梳理需求。",
        },
    )
    assert append_response.status_code == 200

    get_response = client.get(f"/chat/sessions/{session_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "需要采购办公椅"


def test_chat_core_payload_normalizes_mode_into_context():
    request = ChatStreamRequest.model_validate({
        "session_id": "sess-compat-mode",
        "mode": "requirement_intake",
        "manual_mode": "requirement_intake",
        "payload": {
            "message": "帮我梳理采购需求",
            "mode": "requirement_intake",
            "target_mode": "requirement_intake",
            "action_key": "activate_intake_mode",
            "project_id": "project-1",
            "user_id": "user-1",
        },
    })

    assert request.message == "帮我梳理采购需求"
    assert request.context["mode"] == "requirement_intake"
    assert request.context["manual_mode"] == "requirement_intake"
    assert request.context["target_mode"] == "requirement_intake"
    assert request.context["action_key"] == "activate_intake_mode"


def test_kernel_request_body_canonicalizes_legacy_intake_mode_alias():
    request_body = KernelClient._build_request_body(
        user_id="user-compat-mode",
        message="帮我梳理采购需求",
        session_id="sess-compat-mode",
        context={
            "mode": "requirement_canvas",
            "manual_mode": "requirement_canvas",
            "target_mode": "requirement_canvas",
            "function_type": "procurement",
        },
    )

    assert request_body["mode"] == "requirement_intake"
    assert request_body["manual_mode"] == "requirement_intake"
    assert request_body["target_mode"] == "requirement_intake"
    assert request_body["context"]["mode"] == "requirement_intake"
    assert request_body["payload"]["mode"] == "requirement_intake"
