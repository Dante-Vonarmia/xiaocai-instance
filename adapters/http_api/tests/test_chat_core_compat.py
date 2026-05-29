from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.chat.kernel_action_client import _normalize_action_result
from xiaocai_instance_api.chat.kernel_client import KernelClient
from xiaocai_instance_api.chat.kernel_request_body import build_kernel_request_body
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


def test_chat_core_message_writeback_ignores_blank_noop_turn():
    client = TestClient(create_app())
    token = _token(client, user_id="compat-blank-writeback-user")
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
        json={},
    )
    assert append_response.status_code == 200

    messages_response = client.get(f"/chat/sessions/{session_id}/messages", headers=headers)
    assert messages_response.status_code == 200
    assert messages_response.json()["messages"] == []


def test_chat_core_artifact_only_writeback_does_not_create_blank_user_turn():
    client = TestClient(create_app())
    token = _token(client, user_id="compat-artifact-only-user")
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
            "workflow_projection": {"mode_key": "requirement_intake"},
            "artifact_edit_request": {"content": "# 需求梳理文档\n\n已保存"},
        },
    )
    assert append_response.status_code == 200

    messages_response = client.get(f"/chat/sessions/{session_id}/messages", headers=headers)
    assert messages_response.status_code == 200
    messages = messages_response.json()["messages"]
    assert [item["role"] for item in messages] == ["assistant"]
    assert messages[0]["content"] == ""
    assert messages[0]["workflow_projection"] == {"mode_key": "requirement_intake"}
    assert messages[0]["artifact_edit_request"]["content"].startswith("# 需求梳理文档")


def test_chat_core_message_writeback_preserves_projection_and_edit_request():
    client = TestClient(create_app())
    token = _token(client, user_id="compat-writeback-user")
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
            "user_message": "保存右侧文档",
            "assistant_message": "已保存。",
            "workflow_projection": {"mode_key": "requirement_intake"},
            "track_result": {"readiness": {"blocking_gaps": ["采购目的"]}},
            "artifact_edit_request": {"content": "# 需求梳理文档\n\n已修改"},
        },
    )
    assert append_response.status_code == 200

    messages_response = client.get(f"/sessions/{session_id}/messages", headers=headers)
    assert messages_response.status_code == 200
    assistant_message = messages_response.json()["messages"][-1]
    assert assistant_message["workflow_projection"] == {"mode_key": "requirement_intake"}
    assert assistant_message["track_result"] == {"readiness": {"blocking_gaps": ["采购目的"]}}
    assert assistant_message["artifact_edit_request"]["content"].startswith("# 需求梳理文档")
    assert assistant_message["canvas_state"]["versions"][0]["content"].startswith("# 需求梳理文档")


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


def test_chat_core_action_route_delegates_to_kernel_action(monkeypatch):
    client = TestClient(create_app())
    token = _token(client, user_id="compat-action-user")
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/chat/sessions",
        headers=headers,
        json={"function_type": "auto", "title": "Action session"},
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["sessionId"]
    observed = {}

    async def fake_call_kernel_action(**kwargs):
        observed.update(kwargs)
        return {"result": {"message": "action ok"}, "message": "action ok"}

    monkeypatch.setattr(
        "xiaocai_instance_api.chat.action_compat.call_kernel_action",
        fake_call_kernel_action,
    )

    response = client.post(
        "/chat/action",
        headers=headers,
        json={
            "session_id": session_id,
            "action_key": "continue_collection",
            "payload": {
                "target_mode": "requirement_intake",
                "question_answer": {"field_key": "采购目的", "value": "周年庆执行"},
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "action ok"
    assert observed["session_id"] == session_id
    assert observed["context"]["action_key"] == "continue_collection"
    assert observed["context"]["flare_payload_extra"]["question_answer"]["value"] == "周年庆执行"


def test_kernel_action_result_normalization_preserves_artifact_payloads():
    normalized = _normalize_action_result(
        {
            "result": {
                "message": "已生成分析。",
                "analysis_payload": {"markdown": "# 需求分析报告"},
                "canvas_state": {"versions": [{"content": "# 需求梳理文档"}]},
                "workflow_projection": {"mode_key": "analysis_mode"},
            },
        },
        "sess-action-artifact",
    )

    assert normalized["message"] == "已生成分析。"
    assert normalized["session_id"] == "sess-action-artifact"
    assert normalized["analysis_payload"]["markdown"] == "# 需求分析报告"
    assert normalized["canvas_state"]["versions"][0]["content"] == "# 需求梳理文档"
    assert normalized["workflow_projection"] == {"mode_key": "analysis_mode"}


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


def test_chat_core_payload_extra_passes_through_to_kernel_payload():
    request = ChatStreamRequest.model_validate({
        "session_id": "sess-payload-extra",
        "payload": {
            "message": "继续修改文档",
            "mode": "requirement_intake",
            "completion_policy": {"artifact_first": True},
            "question_answer": {"field_key": "采购目的", "value": "周年庆执行"},
            "artifact_edit_request": {"content": "# 更新后的文档"},
        },
    })

    request_body = build_kernel_request_body(
        user_id="user-payload-extra",
        message=request.message,
        session_id=request.session_id,
        context=request.context,
    )

    assert request_body["payload"]["completion_policy"] == {"artifact_first": True}
    assert request_body["payload"]["question_answer"]["field_key"] == "采购目的"
    assert request_body["payload"]["artifact_edit_request"]["content"] == "# 更新后的文档"
    assert "flare_payload_extra" not in request_body["context"]
