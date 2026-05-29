from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app


def _headers(client: TestClient, user_id: str = "analysis-parity-user") -> dict[str, str]:
    response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": user_id})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _session(client: TestClient, headers: dict[str, str], project_id: str) -> str:
    bind = client.post("/projects/bind", headers=headers, json={"project_id": project_id})
    assert bind.status_code == 200
    created = client.post(
        "/sessions",
        headers=headers,
        json={"project_id": project_id, "title": "analysis parity", "mode": "analysis_mode"},
    )
    assert created.status_code == 200
    return created.json()["sessionId"]


def test_analysis_action_preserves_payload_extra_and_target_mode(monkeypatch):
    client = TestClient(create_app())
    headers = _headers(client, "analysis-action-user")
    session_id = _session(client, headers, "proj-analysis-action")
    observed = {}

    async def fake_call_kernel_action(**kwargs):
        observed.update(kwargs)
        return {"message": "analysis action ok", "result": {"message": "analysis action ok"}}

    monkeypatch.setattr(
        "xiaocai_instance_api.chat.action_compat.call_kernel_action",
        fake_call_kernel_action,
    )

    response = client.post(
        "/chat/action",
        headers=headers,
        json={
            "session_id": session_id,
            "action_key": "generate_analysis",
            "target_mode": "analysis_mode",
            "payload": {
                "target_mode": "analysis_mode",
                "workflow_projection": {"mode_key": "analysis_mode"},
                "active_artifact_context": {"artifact_id": "req-doc-1"},
            },
        },
    )

    assert response.status_code == 200
    assert observed["context"]["action_key"] == "generate_analysis"
    assert observed["context"]["target_mode"] == "analysis_mode"
    extra = observed["context"]["flare_payload_extra"]
    assert extra["workflow_projection"] == {"mode_key": "analysis_mode"}
    assert extra["active_artifact_context"] == {"artifact_id": "req-doc-1"}


def test_analysis_writeback_persists_payload_and_projection():
    client = TestClient(create_app())
    headers = _headers(client, "analysis-writeback-user")
    session_id = _session(client, headers, "proj-analysis-writeback")

    response = client.post(
        f"/chat/sessions/{session_id}/messages",
        headers=headers,
        json={
            "user_message": "生成需求分析",
            "assistant_message": "已生成需求分析。",
            "analysis_payload": {
                "markdown": "# 需求分析报告\n\n## 项目理解与核心需求",
            },
            "workflow_projection": {"mode_key": "analysis_mode", "artifact_type": "analysis_report"},
            "artifact_edit_request": {"content": "# 需求分析报告\n\n已编辑"},
        },
    )
    assert response.status_code == 200

    messages = client.get(f"/sessions/{session_id}/messages", headers=headers)
    assert messages.status_code == 200
    assistant = messages.json()["messages"][-1]
    assert assistant["analysis_payload"]["markdown"].startswith("# 需求分析报告")
    assert assistant["workflow_projection"]["mode_key"] == "analysis_mode"
    assert assistant["artifact_edit_request"]["content"].startswith("# 需求分析报告")
    assert assistant["canvas_state"]["versions"][0]["content"].startswith("# 需求分析报告")
