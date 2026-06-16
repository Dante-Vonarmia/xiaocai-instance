"""
采购中国认证提供者

用途: 使用采购中国小程序传入的登录凭证换取 xiaocai 本地登录身份。
"""

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Any

import httpx

from xiaocai_instance_api.auth.identity import AuthIdentity
from xiaocai_instance_api.auth.providers.base import AuthProvider


@dataclass(frozen=True)
class CaigouChinaVerifiedUser:
    """采购中国认证响应归一化后的最小用户信息。"""

    user_id: str
    display_name: str
    status: str


class CaigouChinaAuthProvider(AuthProvider):
    """采购中国登录凭证认证提供者"""

    def __init__(self, verify_url: str, app_id: str, app_secret: str):
        self.verify_url = verify_url
        self.app_id = app_id
        self.app_secret = app_secret

    async def verify(
        self,
        host_token: str | None = None,
        wechat_code: str | None = None,
        login_ticket: str | None = None,
        root_token: str | None = None,
    ) -> AuthIdentity:
        """调用采购中国服务端接口校验登录凭证并返回 xiaocai 用户 ID。"""
        credential = (login_ticket or "").strip()
        if not self.verify_url:
            raise ValueError("Caigou China auth verification URL is not configured")
        if not self.app_secret:
            raise ValueError("Caigou China app secret is not configured")
        if not credential:
            raise ValueError("Caigou China login ticket is required")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.verify_url, json=self._build_payload(credential))
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ValueError("Caigou China auth verification failed") from exc
            except httpx.RequestError as exc:
                raise ValueError("Caigou China auth verification request failed") from exc

        verified_user = self._normalize_response(response.json())
        if verified_user.status and verified_user.status != "active":
            raise ValueError("Caigou China user is not active")
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
            raise ValueError("Caigou China auth response must be an object")

        valid = data.get("valid")
        if valid is not True:
            message = data.get("message") or data.get("error") or "Caigou China credential is invalid"
            raise ValueError(str(message))

        user = data.get("user")
        if not isinstance(user, dict) and isinstance(data.get("data"), dict):
            user = data["data"].get("user")
        if not isinstance(user, dict):
            raise ValueError("Caigou China auth response missing user")

        user_id = str(user.get("id") or user.get("user_id") or "").strip()
        if not user_id:
            raise ValueError("Caigou China auth response missing user id")
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
