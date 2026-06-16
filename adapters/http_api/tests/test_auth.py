"""
认证模块测试

测试范围:
1. Mock 认证流程
2. JWT token 生成和验证
3. 认证依赖注入
4. /auth/exchange 接口
"""

import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient
from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.security.token_codec import (
    create_access_token,
    decode_access_token,
    decode_access_token_claims,
)
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


class _FakeCaigouChinaResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


class _FakeCaigouChinaAsyncClient:
    requests = []
    response_data = {
        "valid": True,
        "user": {
            "id": "316",
            "name": "韩经伟",
            "mobile": "176****1134",
            "status": "active",
            "openid": None,
            "unionid": None,
        },
    }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def post(self, url, json):
        self.requests.append({"url": url, "json": json})
        return _FakeCaigouChinaResponse(self.response_data)


def test_caigou_china_auth_exchange_success(monkeypatch):
    """测试采购中国登录凭证换取"""
    monkeypatch.setenv("MOCK_AUTH", "false")
    monkeypatch.setenv("CAIGOU_CHINA_AUTH_VERIFY_URL", "https://caigou.example.com/api/auth/verify-credential")
    monkeypatch.setenv("CAIGOU_CHINA_APP_ID", "yunhe_ai")
    monkeypatch.setenv("CAIGOU_CHINA_APP_SECRET", "secret-123")
    monkeypatch.setattr(
        "xiaocai_instance_api.auth.providers.caigou_china_provider.httpx.AsyncClient",
        _FakeCaigouChinaAsyncClient,
    )
    _FakeCaigouChinaAsyncClient.requests = []
    _FakeCaigouChinaAsyncClient.response_data = {
        "valid": True,
        "user": {
            "id": "316",
            "name": "韩经伟",
            "status": "active",
        },
    }
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/auth/exchange",
        json={
            "login_ticket": "ticket-123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "316"
    assert data["display_name"] == "韩经伟"
    assert data["source"] == "caigou_china"
    assert data["member_status"] == "active"
    assert data["token_type"] == "bearer"
    claims = decode_access_token_claims(data["access_token"])
    assert claims["external_user_id"] == "316"
    assert claims["display_name"] == "韩经伟"
    assert claims["source"] == "caigou_china"
    request = _FakeCaigouChinaAsyncClient.requests[0]
    payload = request["json"]
    message = f"yunhe_aiticket-123{payload['timestamp']}{payload['nonce']}"
    expected_signature = hmac.new(
        b"secret-123",
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    assert request["url"] == "https://caigou.example.com/api/auth/verify-credential"
    assert payload["credential"] == "ticket-123"
    assert payload["signature"] == expected_signature
    get_settings.cache_clear()


def test_caigou_china_auth_exchange_ticket_alias(monkeypatch):
    """测试采购中国 ticket 兼容字段"""
    monkeypatch.setenv("MOCK_AUTH", "false")
    monkeypatch.setenv("CAIGOU_CHINA_AUTH_VERIFY_URL", "https://caigou.example.com/api/auth/verify-credential")
    monkeypatch.setenv("CAIGOU_CHINA_APP_ID", "yunhe_ai")
    monkeypatch.setenv("CAIGOU_CHINA_APP_SECRET", "secret-123")
    monkeypatch.setattr(
        "xiaocai_instance_api.auth.providers.caigou_china_provider.httpx.AsyncClient",
        _FakeCaigouChinaAsyncClient,
    )
    _FakeCaigouChinaAsyncClient.requests = []
    _FakeCaigouChinaAsyncClient.response_data = {
        "valid": True,
        "user": {
            "id": "316",
            "nickname": "采购会员",
            "status": "active",
        },
    }
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)
    response = client.post("/auth/exchange", json={"ticket": "ticket-alias"})

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "316"
    assert data["display_name"] == "采购会员"
    assert _FakeCaigouChinaAsyncClient.requests[0]["json"]["credential"] == "ticket-alias"
    get_settings.cache_clear()


def test_caigou_china_local_test_ticket(monkeypatch):
    """测试本地假凭证 ticket=test"""
    monkeypatch.setenv("MOCK_AUTH", "true")
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)
    response = client.post("/auth/exchange", json={"ticket": "test"})

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "caigou-china-test-user"
    assert data["display_name"] == "采购中国测试用户"
    claims = decode_access_token_claims(data["access_token"])
    assert claims["source"] == "caigou_china"
    assert claims["member_status"] == "active"
    assert claims["external_user_id"] == "test"
    assert claims["last_login_at"]
    get_settings.cache_clear()


def test_caigou_china_auth_exchange_invalid_credential(monkeypatch):
    """测试采购中国登录凭证失败"""
    monkeypatch.setenv("MOCK_AUTH", "false")
    monkeypatch.setenv("CAIGOU_CHINA_AUTH_VERIFY_URL", "https://caigou.example.com/api/auth/verify-credential")
    monkeypatch.setenv("CAIGOU_CHINA_APP_ID", "yunhe_ai")
    monkeypatch.setenv("CAIGOU_CHINA_APP_SECRET", "secret-123")
    monkeypatch.setattr(
        "xiaocai_instance_api.auth.providers.caigou_china_provider.httpx.AsyncClient",
        _FakeCaigouChinaAsyncClient,
    )
    _FakeCaigouChinaAsyncClient.requests = []
    _FakeCaigouChinaAsyncClient.response_data = {
        "valid": False,
        "error": "CREDENTIAL_INVALID",
        "message": "登录凭证无效",
    }
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/auth/exchange",
        json={
            "credential": "bad-ticket",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "登录凭证无效"
    _FakeCaigouChinaAsyncClient.response_data = {
        "valid": True,
        "user": {
            "id": "316",
            "status": "active",
        },
    }
    get_settings.cache_clear()


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
