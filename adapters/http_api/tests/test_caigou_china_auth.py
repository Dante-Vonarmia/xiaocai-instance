"""
采购中国小程序会员登录认证测试
"""

import hashlib
import hmac

from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.security.token_codec import decode_access_token_claims
from xiaocai_instance_api.settings import get_settings
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
    """测试采购中国 credential 换取"""
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
            "credential": "credential-123",
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
    message = f"yunhe_aicredential-123{payload['timestamp']}{payload['nonce']}"
    expected_signature = hmac.new(
        b"secret-123",
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    assert request["url"] == "https://caigou.example.com/api/auth/verify-credential"
    assert payload["credential"] == "credential-123"
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


def test_caigou_china_local_test_credential(monkeypatch):
    """测试本地假 credential=test"""
    monkeypatch.setenv("MOCK_AUTH", "true")
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)
    response = client.post("/auth/exchange", json={"credential": "test"})

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
    assert response.json()["detail"] == {
        "code": "CREDENTIAL_INVALID",
        "message": "登录凭证无效，请返回采购中国小程序重新进入",
    }
    _FakeCaigouChinaAsyncClient.response_data = {
        "valid": True,
        "user": {
            "id": "316",
            "status": "active",
        },
    }
    get_settings.cache_clear()


def test_caigou_china_auth_exchange_expired_credential(monkeypatch):
    """测试采购中国过期凭证映射为产品提示"""
    monkeypatch.setenv("MOCK_AUTH", "false")
    monkeypatch.setenv("CAIGOU_CHINA_AUTH_VERIFY_URL", "https://caigou.example.com/api/auth/verify-credential")
    monkeypatch.setenv("CAIGOU_CHINA_APP_ID", "yunhe_ai")
    monkeypatch.setenv("CAIGOU_CHINA_APP_SECRET", "secret-123")
    monkeypatch.setattr(
        "xiaocai_instance_api.auth.providers.caigou_china_provider.httpx.AsyncClient",
        _FakeCaigouChinaAsyncClient,
    )
    _FakeCaigouChinaAsyncClient.response_data = {
        "valid": False,
        "error": "CREDENTIAL_EXPIRED",
        "message": "upstream raw expired message",
    }
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)
    response = client.post("/auth/exchange", json={"credential": "expired-credential"})

    assert response.status_code == 401
    assert response.json()["detail"] == {
        "code": "CREDENTIAL_EXPIRED",
        "message": "登录已过期，请返回采购中国小程序重新进入",
    }
    get_settings.cache_clear()


def test_caigou_china_auth_exchange_disabled_user(monkeypatch):
    """测试采购中国用户禁用提示"""
    monkeypatch.setenv("MOCK_AUTH", "false")
    monkeypatch.setenv("CAIGOU_CHINA_AUTH_VERIFY_URL", "https://caigou.example.com/api/auth/verify-credential")
    monkeypatch.setenv("CAIGOU_CHINA_APP_ID", "yunhe_ai")
    monkeypatch.setenv("CAIGOU_CHINA_APP_SECRET", "secret-123")
    monkeypatch.setattr(
        "xiaocai_instance_api.auth.providers.caigou_china_provider.httpx.AsyncClient",
        _FakeCaigouChinaAsyncClient,
    )
    _FakeCaigouChinaAsyncClient.response_data = {
        "valid": True,
        "user": {
            "id": "316",
            "name": "韩经伟",
            "status": "disabled",
        },
    }
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)
    response = client.post("/auth/exchange", json={"credential": "disabled-user-credential"})

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "code": "USER_DISABLED",
        "message": "当前账号状态不可用，请联系采购中国客服",
    }
    get_settings.cache_clear()


def test_caigou_china_auth_exchange_config_missing_does_not_leak(monkeypatch):
    """测试配置错误不向用户泄露技术字段"""
    monkeypatch.setenv("MOCK_AUTH", "false")
    monkeypatch.setenv("CAIGOU_CHINA_AUTH_VERIFY_URL", "https://caigou.example.com/api/auth/verify-credential")
    monkeypatch.setenv("CAIGOU_CHINA_APP_ID", "yunhe_ai")
    monkeypatch.setenv("CAIGOU_CHINA_APP_SECRET", "")
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)
    response = client.post("/auth/exchange", json={"credential": "credential-123"})

    assert response.status_code == 500
    assert response.json()["detail"] == {
        "code": "CONFIG_MISSING",
        "message": "云鹤AI登录服务配置异常，请联系管理员",
    }
    assert "app secret" not in str(response.json()).lower()
    get_settings.cache_clear()


def test_caigou_china_local_bad_credential_uses_product_error(monkeypatch):
    """测试本地假 credential 失败不透传技术异常"""
    monkeypatch.setenv("MOCK_AUTH", "true")
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)
    response = client.post("/auth/exchange", json={"credential": "bad"})

    assert response.status_code == 401
    assert response.json()["detail"] == {
        "code": "CREDENTIAL_INVALID",
        "message": "登录凭证无效，请返回采购中国小程序重新进入",
    }
    get_settings.cache_clear()

