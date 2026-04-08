"""
真实认证提供者

用途: 对接宿主应用的认证系统或微信小程序认证
"""

import httpx
from xiaocai_instance_api.auth.providers.base import AuthProvider


class RealAuthProvider(AuthProvider):
    """真实认证提供者"""

    def __init__(self, verify_url: str):
        """
        Args:
            verify_url: 认证验证 URL
        """
        self.verify_url = verify_url

    async def verify(
        self,
        host_token: str | None = None,
        wechat_code: str | None = None,
        root_token: str | None = None,
    ) -> str:
        """
        真实验证 - 调用宿主应用或微信 API 验证身份

        Args:
            host_token: 宿主应用 token
            wechat_code: 微信小程序 code

        Returns:
            str: 用户 ID

        Raises:
            ValueError: 验证失败
        """
        if not self.verify_url:
            raise ValueError("Auth verification URL is not configured")

        if host_token:
            payload = {"token": host_token}
        elif wechat_code:
            payload = {"wechat_code": wechat_code}
        else:
            raise ValueError("No valid auth credentials provided")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.verify_url, json=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ValueError("Auth verification failed") from exc
            except httpx.RequestError as exc:
                raise ValueError("Auth verification request failed") from exc

        data = response.json()
        user_id = data.get("user_id")
        if not user_id and isinstance(data.get("data"), dict):
            user_id = data["data"].get("user_id")
        if not user_id:
            raise ValueError("Auth verification response missing user_id")
        return str(user_id)
