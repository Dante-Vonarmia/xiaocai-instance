"""
认证服务

职责:
1. 处理身份换取逻辑
2. 调用认证提供者（Mock 或 Real）
3. 生成 JWT token
"""

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.auth.providers.base import AuthProvider
from xiaocai_instance_api.auth.providers.mock_provider import MockAuthProvider
from xiaocai_instance_api.auth.providers.real_provider import RealAuthProvider
from xiaocai_instance_api.auth.providers.root_provider import RootAuthProvider
from xiaocai_instance_api.security.token_codec import create_access_token


class AuthService:
    """认证服务"""

    def __init__(self):
        self.settings = get_settings()
        self._provider: AuthProvider | None = None

    def _get_provider(self, use_mock: bool = False, use_root: bool = False) -> AuthProvider:
        """
        获取认证提供者

        Args:
            use_mock: 是否使用 Mock 提供者

        Returns:
            AuthProvider: 认证提供者实例
        """
        if use_root:
            return RootAuthProvider(
                root_auth_token=self.settings.root_auth_token,
                root_user_id=self.settings.root_user_id,
            )
        if use_mock or self.settings.mock_auth:
            return MockAuthProvider()
        else:
            return RealAuthProvider(self.settings.real_auth_verify_url)

    async def exchange_token(
        self,
        mock: bool = False,
        mock_user_id: str | None = None,
        host_token: str | None = None,
        wechat_code: str | None = None,
        root_token: str | None = None,
    ) -> dict:
        """
        身份换取

        Args:
            mock: 是否使用 Mock 模式
            mock_user_id: Mock 用户 ID
            host_token: 宿主应用 token
            wechat_code: 微信小程序 code

        Returns:
            dict: 包含 access_token, user_id 等信息
        """
        provider = self._get_provider(use_mock=mock, use_root=bool(root_token))

        if isinstance(provider, MockAuthProvider):
            user_id = await provider.verify(mock_user_id=mock_user_id)
        elif isinstance(provider, RootAuthProvider):
            user_id = await provider.verify(root_token=root_token)
        else:
            user_id = await provider.verify(host_token=host_token, wechat_code=wechat_code)

        access_token = create_access_token(user_id=user_id)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.settings.jwt_expire_minutes * 60,
            "user_id": user_id,
        }


def get_auth_service() -> AuthService:
    """获取认证服务单例"""
    return AuthService()
