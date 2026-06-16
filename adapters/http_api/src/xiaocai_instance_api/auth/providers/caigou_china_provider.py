"""
采购中国认证提供者

用途: 使用采购中国小程序传入的 credential 换取 xiaocai 本地登录身份。
"""

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Any

import httpx

from xiaocai_instance_api.auth.errors import AuthError
from xiaocai_instance_api.auth.identity import AuthIdentity
from xiaocai_instance_api.auth.providers.base import AuthProvider


UPSTREAM_ERROR_CODE_MAP = {
    "CREDENTIAL_MISSING": "CREDENTIAL_MISSING",
    "CREDENTIAL_INVALID": "CREDENTIAL_INVALID",
    "CREDENTIAL_EXPIRED": "CREDENTIAL_EXPIRED",
    "CREDENTIAL_USED": "CREDENTIAL_USED",
    "USER_DISABLED": "USER_DISABLED",
    "SIGNATURE_INVALID": "SIGNATURE_INVALID",
    "APP_UNAUTHORIZED": "APP_UNAUTHORIZED",
    "VERIFY_FAILED": "VERIFY_FAILED",
}


@dataclass(frozen=True)
class CaigouChinaVerifiedUser:
    """采购中国认证响应归一化后的最小用户信息。"""

    user_id: str
    display_name: str
    status: str


class CaigouChinaAuthProvider(AuthProvider):
    """采购中国 credential 认证提供者"""

    def __init__(self, verify_url: str, app_id: str, app_secret: str):
        self.verify_url = verify_url
        self.app_id = app_id
        self.app_secret = app_secret

    async def verify(
        self,
        host_token: str | None = None,
        wechat_code: str | None = None,
        credential: str | None = None,
        login_ticket: str | None = None,
        root_token: str | None = None,
    ) -> AuthIdentity:
        """调用采购中国服务端接口校验 credential 并返回 xiaocai 用户 ID。"""
        credential_value = (credential or login_ticket or "").strip()
        if not self.verify_url:
            raise AuthError("CONFIG_MISSING", log_message="caigou china verify url missing")
        if not self.app_secret:
            raise AuthError("CONFIG_MISSING", log_message="caigou china app secret missing")
        if not credential_value:
            raise AuthError("CREDENTIAL_MISSING", log_message="caigou china credential missing")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.verify_url, json=self._build_payload(credential_value))
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise AuthError(
                    "VERIFY_FAILED",
                    log_message=f"caigou china verify http status {exc.response.status_code}",
                ) from exc
            except httpx.TimeoutException as exc:
                raise AuthError("VERIFY_TIMEOUT", log_message="caigou china verify timeout") from exc
            except httpx.RequestError as exc:
                raise AuthError("VERIFY_FAILED", log_message="caigou china verify request failed") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise AuthError("RESPONSE_INVALID", log_message="caigou china verify response not json") from exc

        verified_user = self._normalize_response(payload)
        if verified_user.status and verified_user.status != "active":
            raise AuthError("USER_DISABLED", log_message="caigou china user status is not active")
        return AuthIdentity(
            user_id=verified_user.user_id,
            source="caigou_china",
            display_name=verified_user.display_name or verified_user.user_id,
            member_status=verified_user.status or "active",
            external_user_id=verified_user.user_id,
        )

    def _build_payload(self, credential: str) -> dict[str, str | int]:
        """集中生成签名请求，避免签名细节散落到 service/router。"""
        timestamp = int(time.time())
        nonce = secrets.token_hex(16)
        signature = self._sign(
            credential=credential,
            timestamp=timestamp,
            nonce=nonce,
        )
        return {
            "appId": self.app_id,
            "credential": credential,
            "timestamp": timestamp,
            "nonce": nonce,
            "signature": signature,
        }

    def _sign(self, credential: str, timestamp: int, nonce: str) -> str:
        message = f"{self.app_id}{credential}{timestamp}{nonce}"
        return hmac.new(
            self.app_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _normalize_response(self, data: dict[str, Any]) -> CaigouChinaVerifiedUser:
        if not isinstance(data, dict):
            raise AuthError("RESPONSE_INVALID", log_message="caigou china auth response must be object")

        valid = data.get("valid")
        if valid is not True:
            upstream_code = str(data.get("error") or "CREDENTIAL_INVALID").strip().upper()
            code = UPSTREAM_ERROR_CODE_MAP.get(upstream_code, "CREDENTIAL_INVALID")
            upstream_message = str(data.get("message") or upstream_code).strip()
            raise AuthError(code, log_message=f"caigou china verify rejected: {upstream_message}")

        user = data.get("user")
        if not isinstance(user, dict) and isinstance(data.get("data"), dict):
            user = data["data"].get("user")
        if not isinstance(user, dict):
            raise AuthError("RESPONSE_INVALID", log_message="caigou china auth response missing user")

        user_id = str(user.get("id") or user.get("user_id") or "").strip()
        if not user_id:
            raise AuthError("RESPONSE_INVALID", log_message="caigou china auth response missing user id")
        display_name = str(
            user.get("name")
            or user.get("nickname")
            or user.get("display_name")
            or user_id
        ).strip()
        return CaigouChinaVerifiedUser(
            user_id=user_id,
            display_name=display_name,
            status=str(user.get("status") or "").strip(),
        )
