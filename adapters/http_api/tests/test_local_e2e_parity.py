from unittest.mock import patch

from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app


def _headers(client: TestClient) -> dict[str, str]:
    response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": "local-e2e-user"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_project_intake_patch_analysis_patch_and_refresh_restore():
    client = TestClient(create_app())
    headers = _headers(client)
    project_id = "proj-local-e2e"
    bind = client.post("/projects/bind", headers=headers, json={"project_id": project_id})
    assert bind.status_code == 200
    created = client.post(
        "/sessions",
        headers=headers,
        json={"project_id": project_id, "title": "本地端到端", "mode": "requirement_canvas"},
    )
    assert created.status_code == 200
    session_id = created.json()["sessionId"]

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def intake_stream():
            yield {
                "type": "patch_event",
                "payload": {
                    "question": {
                        "field_key": "采购目的",
                        "question_text": "本次采购最终要解决什么问题？",
                    },
                    "missing_fields": {"required": ["采购目的"]},
                    "track_result": {"readiness": {"blocking_gaps": ["采购目的"]}},
                },
            }
            yield {
                "type": "done",
                "session_id": session_id,
                "message": "本次采购最终要解决什么问题？",
            }

        mock_stream.return_value = intake_stream()
        intake = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "请帮我梳理采购需求",
                "session_id": session_id,
                "context": {"project_id": project_id, "mode": "requirement_canvas"},
            },
        )

    assert intake.status_code == 200
    assert "event: canvas_state" not in intake.text
    assert "采购目的" in intake.text
    assert "ready_for_submit" not in intake.text

    intake_writeback = client.post(
        f"/chat/sessions/{session_id}/messages",
        headers=headers,
        json={
            "user_message": "采购目的：支持公司周年庆活动",
            "assistant_message": "已更新需求文档。",
            "workflow_projection": {"mode_key": "requirement_intake"},
            "artifact_edit_request": {"content": "# 需求梳理文档\n\n采购目的：支持公司周年庆活动"},
        },
    )
    assert intake_writeback.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def analysis_stream():
            yield {
                "type": "analysis_payload",
                "markdown": "# 需求分析报告\n\n## 项目理解与核心需求",
            }
            yield {
                "type": "done",
                "session_id": session_id,
                "message": "已生成需求分析报告。",
            }

        mock_stream.return_value = analysis_stream()
        analysis = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "基于当前需求生成需求分析",
                "session_id": session_id,
                "context": {"project_id": project_id, "mode": "analysis_mode"},
            },
        )

    assert analysis.status_code == 200
    assert "event: analysis_payload" in analysis.text
    assert "需求分析报告" in analysis.text

    analysis_writeback = client.post(
        f"/chat/sessions/{session_id}/messages",
        headers=headers,
        json={
            "user_message": "保存分析报告",
            "assistant_message": "分析报告已保存。",
            "analysis_payload": {"markdown": "# 需求分析报告\n\n已保存"},
            "workflow_projection": {"mode_key": "analysis_mode", "artifact_type": "analysis_report"},
            "artifact_edit_request": {"content": "# 需求分析报告\n\n已保存"},
        },
    )
    assert analysis_writeback.status_code == 200

    messages = client.get(f"/sessions/{session_id}/messages", headers=headers)
    assert messages.status_code == 200
    payload = messages.json()["messages"]
    assert any((item.get("artifact_edit_request") or {}).get("content", "").startswith("# 需求梳理文档") for item in payload)
    assert any((item.get("analysis_payload") or {}).get("markdown", "").startswith("# 需求分析报告") for item in payload)
    assert any((item.get("workflow_projection") or {}).get("mode_key") == "analysis_mode" for item in payload)
