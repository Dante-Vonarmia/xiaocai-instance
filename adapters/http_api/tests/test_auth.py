"""
认证模块测试

测试范围:
1. Mock 认证流程
2. JWT token 生成和验证
3. 认证依赖注入
4. /auth/exchange 接口
"""

import pytest
from fastapi.testclient import TestClient
from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.security.token_codec import create_access_token, decode_access_token
from xiaocai_instance_api.settings import get_settings


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app()
    return TestClient(app)


def test_create_and_decode_token():
    """测试 JWT token 创建和解码"""
    user_id = "test-user-123"

    token = create_access_token(user_id)
    assert token is not None
    assert len(token) > 0

    decoded_user_id = decode_access_token(token)
    assert decoded_user_id == user_id


def test_mock_auth_exchange(client):
    """测试 Mock 认证换取"""
    response = client.post(
        "/auth/exchange",
        json={
            "mock": True,
            "mock_user_id": "test-user-456",
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user_id"] == "test-user-456"
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_auth_dependency(client):
    """测试认证依赖注入"""
    auth_response = client.post(
        "/auth/exchange",
        json={"mock": True, "mock_user_id": "test-user-789"}
    )
    token = auth_response.json()["access_token"]

    from unittest.mock import patch

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "ok",
            "cards": [],
            "session_id": "test-session",
        }

        chat_response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "测试消息",
                "session_id": "test-session",
            }
        )

    assert chat_response.status_code == 200


def test_invalid_token(client):
    """测试无效 token"""
    response = client.post(
        "/chat/run",
        headers={"Authorization": "Bearer invalid-token"},
        json={
            "message": "测试消息",
            "session_id": "test-session",
        }
    )

    assert response.status_code == 401


def test_missing_token(client):
    """测试缺少 token"""
    response = client.post(
        "/chat/run",
        json={
            "message": "测试消息",
            "session_id": "test-session",
        }
    )

    assert response.status_code in (401, 403)  # FastAPI 版本差异


def test_root_auth_exchange_success(monkeypatch):
    """测试 root 认证换取"""
    monkeypatch.setenv("MOCK_AUTH", "false")
    monkeypatch.setenv("ROOT_AUTH_TOKEN", "root-token-123")
    monkeypatch.setenv("ROOT_USER_ID", "root")
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/auth/exchange",
        json={
            "root_token": "root-token-123",
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "root"
    assert data["token_type"] == "bearer"
    assert "access_token" in data
    get_settings.cache_clear()


def test_root_auth_exchange_invalid_token(monkeypatch):
    """测试 root 认证失败"""
    monkeypatch.setenv("MOCK_AUTH", "false")
    monkeypatch.setenv("ROOT_AUTH_TOKEN", "root-token-123")
    monkeypatch.setenv("ROOT_USER_ID", "root")
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/auth/exchange",
        json={
            "root_token": "invalid-root-token",
        }
    )

    assert response.status_code == 401
    get_settings.cache_clear()
