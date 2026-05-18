from unittest.mock import patch

from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.settings import get_settings


def _auth_headers(client: TestClient, user_id: str = "chat-mode-regression-user") -> dict[str, str]:
    response = client.post(
        "/auth/exchange",
        json={"mock": True, "mock_user_id": user_id},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    return TestClient(create_app())


def _bind_project(client: TestClient, headers: dict[str, str], project_id: str) -> None:
    bind_response = client.post(
        "/projects/bind",
        headers=headers,
        json={"project_id": project_id},
    )
    assert bind_response.status_code == 200


def _create_session_with_mode(
    client: TestClient,
    headers: dict[str, str],
    project_id: str,
    session_id: str,
    mode: str,
) -> None:
    create_response = client.post(
        "/sessions",
        headers=headers,
        json={
            "project_id": project_id,
            "title": "mode regression",
            "mode": mode,
        },
    )
    assert create_response.status_code == 200
    created_session_id = create_response.json()["sessionId"]
    if created_session_id != session_id:
        # 通过一次 run 固定我们想测试的 session_id，避免依赖自动生成 id。
        with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
            mock_chat.return_value = {
                "message": "session prepare",
                "cards": [],
                "session_id": session_id,
                "metadata": {},
            }
            prepare_response = client.post(
                "/chat/run",
                headers=headers,
                json={
                    "message": "prepare",
                    "session_id": session_id,
                    "context": {"project_id": project_id, "mode": mode},
                },
            )
        assert prepare_response.status_code == 200


def test_chat_002_t1_auto_mode_does_not_stick_to_intake(monkeypatch, tmp_path):
    client = _create_client(monkeypatch, tmp_path)
    headers = _auth_headers(client)
    project_id = "proj-chat-002-t1"
    session_id = "sess-chat-002-t1"
    _bind_project(client, headers, project_id)
    _create_session_with_mode(client, headers, project_id, session_id, "requirement_canvas")

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "这是自然对话响应",
            "cards": [],
            "session_id": session_id,
            "metadata": {},
        }

        response = client.post(
            "/chat/run",
            headers=headers,
            json={
                "message": "我们这里没有开启梳理模式，为什么会自己冒出来？",
                "session_id": session_id,
                "context": {"project_id": project_id, "mode": "auto"},
            },
        )

    assert response.status_code == 200
    assert response.json()["message"] == "这是自然对话响应"
    assert "pending_contract" not in response.json()["metadata"]

    kernel_context = mock_chat.call_args[1]["context"]
    resolved_mode = str(kernel_context.get("mode") or "").strip()
    assert resolved_mode not in {"requirement_canvas", "requirement_intake"}


def test_chat_002_t2_auto_mode_does_not_emit_intake_canvas_projection(monkeypatch, tmp_path):
    client = _create_client(monkeypatch, tmp_path)
    headers = _auth_headers(client)
    project_id = "proj-chat-002-t2"
    session_id = "sess-chat-002-t2"
    _bind_project(client, headers, project_id)
    _create_session_with_mode(client, headers, project_id, session_id, "requirement_canvas")

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {
                "type": "text.delta",
                "channel": "assistant",
                "delta": "这是一条普通对话回复，不是需求梳理。",
            }
            yield {"type": "done", "session_id": session_id}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "这里我们都没有开启梳理模式，为什么会自己冒出来呢？",
                "session_id": session_id,
                "context": {"project_id": project_id, "mode": "auto"},
            },
        )

    assert response.status_code == 200
    assert "这是一条普通对话回复，不是需求梳理。" in response.text
    assert "event: canvas_state" not in response.text
    assert "# 需求梳理草稿" not in response.text
    assert "event: text.replace" not in response.text


def test_chat_002_t3_auto_mode_should_not_fallback_to_blocking_question(monkeypatch, tmp_path):
    client = _create_client(monkeypatch, tmp_path)
    headers = _auth_headers(client)
    project_id = "proj-chat-002-t3"
    session_id = "sess-chat-002-t3"
    _bind_project(client, headers, project_id)
    _create_session_with_mode(client, headers, project_id, session_id, "requirement_canvas")

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "",
            "cards": [],
            "session_id": session_id,
            "metadata": {},
            "command_type": "continue_collection",
            "missing_fields": ["项目名称"],
            "question": {"question_text": "请先补充项目名称"},
            "gate": {"status": "blocked", "reason": "missing_required_fields"},
        }

        response = client.post(
            "/chat/run",
            headers=headers,
            json={
                "message": "为什么自然对话会被阻断？",
                "session_id": session_id,
                "context": {"project_id": project_id, "mode": "auto"},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] != "请先补充项目名称"
    assert "pending_contract" not in body["metadata"]


def test_chat_002_t4_kernel_run_error_should_degrade_not_hard_fail(monkeypatch, tmp_path):
    client = _create_client(monkeypatch, tmp_path)
    headers = _auth_headers(client)
    project_id = "proj-chat-002-t4"
    _bind_project(client, headers, project_id)

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.side_effect = RuntimeError("kernel temporarily unavailable")

        response = client.post(
            "/chat/run",
            headers=headers,
            json={
                "message": "继续自然对话",
                "session_id": "sess-chat-002-t4",
                "context": {"project_id": project_id, "mode": "auto"},
            },
        )

    assert response.status_code == 200
    assert "当前未生成可展示回复，请重试。" in response.json()["message"]


def test_chat_002_t5_explicit_intake_mode_still_emits_canvas_projection(monkeypatch, tmp_path):
    client = _create_client(monkeypatch, tmp_path)
    headers = _auth_headers(client)
    project_id = "proj-chat-002-t5"
    session_id = "sess-chat-002-t5"
    _bind_project(client, headers, project_id)

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {
                "type": "text.delta",
                "channel": "assistant",
                "delta": "我先帮你梳理采购需求。",
            }
            yield {"type": "done", "session_id": session_id}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "我要采购一批测试服务器，请先帮我梳理需求。",
                "session_id": session_id,
                "context": {"project_id": project_id, "mode": "requirement_canvas"},
            },
        )

    assert response.status_code == 200
    assert "event: canvas_state" in response.text
    assert "# 需求梳理草稿" in response.text
