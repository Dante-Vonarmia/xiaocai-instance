"""
对话模块测试

测试范围:
1. /chat/run 接口（同步对话）
2. /chat/stream 接口（流式对话）
3. Kernel 客户端调用
4. 错误处理

注意: 这些测试需要 mock kernel 响应，不依赖真实 kernel 服务
"""

import pytest
from fastapi.testclient import TestClient
from xiaocai_instance_api.app import create_app
from unittest.mock import patch
from xiaocai_instance_api.settings import get_settings


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    """获取测试用的认证 token"""
    response = client.post(
        "/auth/exchange",
        json={"mock": True, "mock_user_id": "test-user"}
    )
    return response.json()["access_token"]


def test_chat_run_success(client, auth_token):
    """测试同步对话成功场景"""
    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "reply": "我理解您需要采购办公设备",
            "cards": [
                {
                    "type": "requirement-form",
                    "data": {"fields": ["category", "quantity"]},
                }
            ],
            "session_id": "test-session",
        }

        response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "我需要采购一批办公电脑",
                "session_id": "test-session",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "我理解您需要采购办公设备"
        assert "cards" in data
        assert len(data["cards"]) > 0


def test_chat_run_without_auth(client):
    """测试未认证的对话请求"""
    response = client.post(
        "/chat/run",
        json={
            "message": "测试消息",
            "session_id": "test-session",
        }
    )

    assert response.status_code in (401, 403)


def test_chat_stream_success(client, auth_token):
    """测试流式对话成功场景"""
    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {"type": "token", "content": "你好"}
            yield {"type": "token", "content": "，"}
            yield {"type": "token", "content": "我是小菜"}
            yield {"type": "done"}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "你好",
                "session_id": "test-session",
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        assert "event: token" in response.text
        assert "data: {\"type\": \"token\"" in response.text


def test_chat_with_context(client, auth_token):
    """测试带上下文的对话"""
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"project_id": "proj-123"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "reply": "根据之前的需求，推荐以下供应商",
            "cards": [],
            "session_id": "test-session",
        }

        response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "继续",
                "session_id": "test-session",
                "context": {
                    "project_id": "proj-123",
                    "previous_step": "requirement-collection",
                },
            }
        )

        assert response.status_code == 200
        # 验证 context 被正确传递给 kernel
        mock_chat.assert_called_once()
        call_args = mock_chat.call_args[1]
        assert call_args["context"]["project_id"] == "proj-123"


def test_chat_run_intelligent_sourcing_keeps_empty_cards_when_kernel_returns_none(client, auth_token):
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"project_id": "proj-sourcing-1"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "已进入智能寻源",
            "cards": [],
            "session_id": "sourcing-session",
            "metadata": {},
        }

        response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "帮我找供应商",
                "session_id": "sourcing-session",
                "context": {
                    "project_id": "proj-sourcing-1",
                    "mode": "intelligent_sourcing",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["cards"]) == 0


def test_chat_run_injects_requirement_canvas_function_type(client, auth_token):
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"project_id": "proj-func-1"},
    )
    assert bind_response.status_code == 200

    session_response = client.post(
        "/sessions",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"project_id": "proj-func-1", "title": "函数类型会话"},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["sessionId"]

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "ok",
            "cards": [],
            "session_id": session_id,
            "metadata": {},
        }

        response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "测试",
                "session_id": session_id,
                "context": {"project_id": "proj-func-1"},
            },
        )

        assert response.status_code == 200
        mock_chat.assert_called_once()
        call_args = mock_chat.call_args[1]
        assert call_args["context"]["project_id"] == "proj-func-1"
        assert call_args["context"]["function_type"] == "requirement_canvas"


def test_chat_stream_injects_requirement_canvas_function_type(client, auth_token):
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"project_id": "proj-func-2"},
    )
    assert bind_response.status_code == 200

    session_response = client.post(
        "/sessions",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"project_id": "proj-func-2", "title": "函数类型会话"},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["sessionId"]

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {"type": "token", "content": "测"}
            yield {"type": "done"}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "测试",
                "session_id": session_id,
                "context": {"project_id": "proj-func-2"},
            },
        )

        assert response.status_code == 200
        mock_stream.assert_called_once()
        call_args = mock_stream.call_args[1]
        assert call_args["context"]["project_id"] == "proj-func-2"
        assert call_args["context"]["function_type"] == "requirement_canvas"
        assert "event: token" in response.text


def test_kernel_error_handling(client, auth_token):
    """测试 kernel 错误处理"""
    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.side_effect = Exception("Kernel service unavailable")

        response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "测试消息",
                "session_id": "test-session",
            }
        )

        assert response.status_code == 500
        assert "Kernel service unavailable" in response.json()["detail"]


def test_chat_mode_not_allowed(monkeypatch):
    monkeypatch.setenv("ENABLED_MODES", '["auto","requirement_canvas"]')
    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    auth_response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": "mode-user"})
    token = auth_response.json()["access_token"]
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-mode"},
    )
    assert bind_response.status_code == 200

    response = client.post(
        "/chat/run",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "测试模式",
            "session_id": "sess-mode",
            "context": {"project_id": "proj-mode", "mode": "intelligent_sourcing"},
        },
    )
    assert response.status_code == 400
    assert "mode not allowed" in response.json()["detail"]
    get_settings.cache_clear()


def test_chat_run_rejects_cross_user_existing_session_id(client):
    owner_auth = client.post("/auth/exchange", json={"mock": True, "mock_user_id": "owner-user"})
    attacker_auth = client.post("/auth/exchange", json={"mock": True, "mock_user_id": "attacker-user"})
    owner_token = owner_auth.json()["access_token"]
    attacker_token = attacker_auth.json()["access_token"]

    owner_bind = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"project_id": "proj-owner"},
    )
    assert owner_bind.status_code == 200

    attacker_bind = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {attacker_token}"},
        json={"project_id": "proj-attacker"},
    )
    assert attacker_bind.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "owner ok",
            "cards": [],
            "session_id": "sess-shared",
            "metadata": {},
        }
        owner_run = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "message": "owner first message",
                "session_id": "sess-shared",
                "context": {"project_id": "proj-owner"},
            },
        )
        assert owner_run.status_code == 200

    attacker_run = client.post(
        "/chat/run",
        headers={"Authorization": f"Bearer {attacker_token}"},
        json={
            "message": "attacker tries to reuse session id",
            "session_id": "sess-shared",
            "context": {"project_id": "proj-attacker"},
        },
    )
    assert attacker_run.status_code == 403
    assert "Session access denied" in attacker_run.json()["detail"]


def test_chat_daily_limit(monkeypatch):
    monkeypatch.setenv("DAILY_MESSAGE_LIMIT", "1")
    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    auth_response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": "quota-user"})
    token = auth_response.json()["access_token"]
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-quota"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "ok",
            "cards": [],
            "session_id": "sess-quota",
            "metadata": {},
        }
        first = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "第一条",
                "session_id": "sess-quota",
                "context": {"project_id": "proj-quota"},
            },
        )
        assert first.status_code == 200

        second = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "第二条",
                "session_id": "sess-quota",
                "context": {"project_id": "proj-quota"},
            },
        )
        assert second.status_code == 429
        assert "daily message limit exceeded" in second.json()["detail"]
    get_settings.cache_clear()


def test_chat_daily_project_limit(monkeypatch):
    monkeypatch.setenv("DAILY_MESSAGE_LIMIT", "0")
    monkeypatch.setenv("DAILY_PROJECT_MESSAGE_LIMIT", "1")
    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    auth_response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": "quota-project-user"})
    token = auth_response.json()["access_token"]

    for project_id in ("proj-a", "proj-b"):
        bind_response = client.post(
            "/projects/bind",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_id": project_id},
        )
        assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "ok",
            "cards": [],
            "session_id": "sess-qa",
            "metadata": {},
        }
        first_a = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "A-1",
                "session_id": "sess-a",
                "context": {"project_id": "proj-a"},
            },
        )
        assert first_a.status_code == 200

        second_a = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "A-2",
                "session_id": "sess-a",
                "context": {"project_id": "proj-a"},
            },
        )
        assert second_a.status_code == 429
        assert "daily project message limit exceeded: proj-a" in second_a.json()["detail"]

        first_b = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "B-1",
                "session_id": "sess-b",
                "context": {"project_id": "proj-b"},
            },
        )
        assert first_b.status_code == 200
    get_settings.cache_clear()


def test_chat_run_auto_creates_session_with_default_function_type(client, auth_token):
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"project_id": "proj-auto-create"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "ok",
            "cards": [],
            "session_id": "sess-auto-create",
            "metadata": {},
        }

        response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "创建会话",
                "session_id": "sess-auto-create",
                "context": {"project_id": "proj-auto-create"},
            },
        )
        assert response.status_code == 200

    session_response = client.get(
        "/sessions/sess-auto-create",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert session_response.status_code == 200
    session_data = session_response.json()
    assert session_data["function_type"] == "requirement_canvas"
    assert session_data["project_id"] == "proj-auto-create"


def test_chat_run_forbidden_when_project_not_bound(client, auth_token):
    response = client.post(
        "/chat/run",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "message": "未绑定项目访问",
            "session_id": "sess-no-project-access",
            "context": {"project_id": "proj-not-bound"},
        },
    )
    assert response.status_code == 403
    assert "Project access denied" in response.json()["detail"]


def test_chat_stream_forbidden_when_project_not_bound(client, auth_token):
    response = client.post(
        "/chat/stream",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "message": "未绑定项目访问",
            "session_id": "sess-no-project-access-stream",
            "context": {"project_id": "proj-not-bound-stream"},
        },
    )
    assert response.status_code == 200
    assert "event: error" in response.text
    assert "Project access denied" in response.text


def test_chat_run_appends_exchange_to_session_messages(client, auth_token):
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"project_id": "proj-append-run"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "run response",
            "cards": [],
            "session_id": "sess-append-run",
            "metadata": {},
        }

        run_response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "run input",
                "session_id": "sess-append-run",
                "context": {"project_id": "proj-append-run"},
            },
        )
        assert run_response.status_code == 200

    messages_response = client.get(
        "/sessions/sess-append-run/messages",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert messages_response.status_code == 200
    messages = messages_response.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "run input"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "run response"


def test_chat_stream_appends_exchange_to_session_messages(client, auth_token):
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"project_id": "proj-append-stream"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {"type": "token", "content": "hello "}
            yield {"type": "token", "content": "stream"}
            yield {"type": "done"}

        mock_stream.return_value = mock_generator()

        stream_response = client.post(
            "/chat/stream",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "stream input",
                "session_id": "sess-append-stream",
                "context": {"project_id": "proj-append-stream"},
            },
        )
        assert stream_response.status_code == 200
        assert "event: token" in stream_response.text
        assert "event: done" in stream_response.text

    messages_response = client.get(
        "/sessions/sess-append-stream/messages",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert messages_response.status_code == 200
    messages = messages_response.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "stream input"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "hello stream"


def test_chat_stream_emits_error_event_when_kernel_fails(client, auth_token):
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"project_id": "proj-stream-error"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def broken_generator():
            raise RuntimeError("kernel stream unavailable")
            yield {"type": "done"}  # pragma: no cover

        mock_stream.return_value = broken_generator()

        response = client.post(
            "/chat/stream",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "触发错误",
                "session_id": "sess-stream-error",
                "context": {"project_id": "proj-stream-error"},
            },
        )

        assert response.status_code == 200
        assert "event: error" in response.text
        assert "kernel stream unavailable" in response.text
