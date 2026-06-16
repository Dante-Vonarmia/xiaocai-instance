"""
Mock 认证提供者

用途: 开发测试时使用，直接返回固定用户 ID
"""

from xiaocai_instance_api.auth.identity import AuthIdentity
from xiaocai_instance_api.auth.providers.base import AuthProvider


class MockAuthProvider(AuthProvider):
    """Mock 认证提供者"""

    async def verify(
        self,
        host_token: str | None = None,
        wechat_code: str | None = None,
        login_ticket: str | None = None,
        root_token: str | None = None,
        mock_user_id: str | None = None,
    ) -> AuthIdentity:
        """
        Mock 验证 - 直接返回测试用户 ID

        Returns:
            str: 固定的测试用户 ID
        """
        user_id = mock_user_id or "root-local-dev"
        return AuthIdentity(
            user_id=user_id,
            source="mock",
            display_name=user_id,
            member_status="active",
            external_user_id=user_id,
        )
