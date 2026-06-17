from unittest.mock import patch

from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.settings import get_settings


def _auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/exchange",
        json={"mock": True, "mock_user_id": "projection-user"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_stream_answer_does_not_receive_synthetic_canvas_projection(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _auth_headers(client)

    bind_response = client.post(
        "/projects/bind",
        headers=headers,
        json={"project_id": "proj-stream-projection"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {
                "type": "text.delta",
                "channel": "assistant",
                "delta": "我先按测试服务器采购场景整理需求，并列出待补充信息。",
            }
            yield {"type": "done", "session_id": "sess-stream-projection"}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "我要采购一批测试服务器，请先帮我梳理采购需求并列出还缺的关键信息。",
                "session_id": "sess-stream-projection",
                "context": {
                    "project_id": "proj-stream-projection",
                    "mode": "requirement_canvas",
                },
            },
        )

    assert response.status_code == 200
    assert "我先按测试服务器采购场景整理需求，并列出待补充信息。" in response.text
    assert "event: canvas_state" not in response.text
    assert "# 需求梳理草稿" not in response.text
    legacy_projection_question = "".join(["请", "补", "充", "字", "段", "：", "项目名称"])
    assert legacy_projection_question not in response.text
    assert "event: text.replace" not in response.text


def test_structured_reasoning_artifact_projects_requirement_canvas_state(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _auth_headers(client)

    bind_response = client.post(
        "/projects/bind",
        headers=headers,
        json={"project_id": "proj-structured-reasoning-canvas"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {
                "type": "patch_event",
                "session_id": "sess-structured-reasoning-canvas",
                "run_id": "run-structured-reasoning-canvas",
                "event_type": "structured_reasoning",
                "payload": {
                    "structured_reasoning": {
                        "artifact_document": {
                            "artifact_type": "requirements_document",
                            "title": "培训室采购需求整理",
                            "content_format": "markdown",
                            "content": "# 培训室采购需求整理\n\n## 目标与范围\n\n## 待确认问题",
                        },
                    },
                },
            }
            yield {"type": "done", "session_id": "sess-structured-reasoning-canvas"}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "公司要改造两间培训室，需要采购会议屏、麦克风、音响和远程会议设备，请先帮我梳理采购需求。",
                "session_id": "sess-structured-reasoning-canvas",
                "context": {
                    "project_id": "proj-structured-reasoning-canvas",
                    "mode": "requirement_canvas",
                },
            },
        )

    assert response.status_code == 200
    assert "event: canvas_state" in response.text
    assert response.text.index("event: canvas_state") < response.text.index("event: patch_event")
    assert '"mode_key": "requirement_intake"' in response.text
    assert '"active_tab": "requirement"' in response.text
    assert '"key": "smart_structure"' in response.text
    assert '"semantic_map"' in response.text
    assert "培训室采购需求整理" in response.text


def test_projected_pending_does_not_override_existing_stream_text(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _auth_headers(client)

    bind_response = client.post(
        "/projects/bind",
        headers=headers,
        json={"project_id": "proj-stream-native-text"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {
                "type": "text.delta",
                "channel": "assistant",
                "delta": "您希望采购或寻找合适的衍射仪，我先给出选型框架。",
            }
            yield {
                "type": "early_patch",
                "missing_fields": ["一级品类"],
                "current_question": {
                    "field_key": "一级品类",
                    "question_text": "请确认更接近哪类采购方向。",
                    "options": [],
                },
                "gate": {"status": "blocked", "reason": "missing_required_fields"},
            }
            yield {"type": "done", "session_id": "sess-stream-native-text"}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "我要找衍射仪",
                "session_id": "sess-stream-native-text",
                "context": {
                    "project_id": "proj-stream-native-text",
                    "mode": "requirement_canvas",
                },
            },
        )

    assert response.status_code == 200
    assert "您希望采购或寻找合适的衍射仪，我先给出选型框架。" in response.text
    assert "为避免品类判断偏差" not in response.text
    assert "event: text.replace" not in response.text
