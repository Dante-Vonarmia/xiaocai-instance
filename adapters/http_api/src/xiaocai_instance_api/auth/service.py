"""
认证服务

职责:
1. 处理身份换取逻辑
2. 调用认证提供者（Mock 或 Real）
3. 生成 JWT token
"""

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.auth.identity import AuthIdentity
from xiaocai_instance_api.auth.providers.base import AuthProvider
from xiaocai_instance_api.auth.providers.caigou_china_provider import CaigouChinaAuthProvider
from xiaocai_instance_api.auth.providers.mock_provider import MockAuthProvider
from xiaocai_instance_api.auth.providers.real_provider import RealAuthProvider
from xiaocai_instance_api.auth.providers.root_provider import RootAuthProvider
from xiaocai_instance_api.security.token_codec import create_access_token

CAIGOU_CHINA_LOCAL_TEST_TICKET = "test"


class AuthService:
    """认证服务"""

    def __init__(self):
        self.settings = get_settings()
        self._provider: AuthProvider | None = None

    def _get_provider(
        self,
        use_mock: bool = False,
        use_root: bool = False,
        use_caigou_china: bool = False,
    ) -> AuthProvider:
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
        if use_caigou_china:
            return CaigouChinaAuthProvider(
                verify_url=self.settings.caigou_china_auth_verify_url,
                app_id=self.settings.caigou_china_app_id,
                app_secret=self.settings.caigou_china_app_secret,
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
        login_ticket: str | None = None,
        ticket: str | None = None,
        token: str | None = None,
        credential: str | None = None,
        sso_ticket: str | None = None,
        auth_code: str | None = None,
        root_token: str | None = None,
    ) -> dict:
        """
        身份换取

        Args:
            mock: 是否使用 Mock 模式
            mock_user_id: Mock 用户 ID
            host_token: 宿主应用 token
            wechat_code: 微信小程序 code
            login_ticket: 采购中国登录凭证
            ticket: 采购中国登录凭证兼容字段

        Returns:
            dict: 包含 access_token, user_id 等信息
        """
        caigou_login_ticket = self._first_present(
            login_ticket,
            ticket,
            token,
            credential,
            sso_ticket,
            auth_code,
        )
        if caigou_login_ticket and self.settings.mock_auth:
            identity = self._verify_local_caigou_china_ticket(caigou_login_ticket)
            return self._build_exchange_response(identity)

        provider = self._get_provider(
            use_mock=mock,
            use_root=bool(root_token),
            use_caigou_china=bool(caigou_login_ticket),
        )

        if isinstance(provider, MockAuthProvider):
            identity = await provider.verify(mock_user_id=mock_user_id)
        elif isinstance(provider, RootAuthProvider):
            identity = await provider.verify(root_token=root_token)
        elif isinstance(provider, CaigouChinaAuthProvider):
            identity = await provider.verify(login_ticket=caigou_login_ticket)
        else:
            identity = await provider.verify(host_token=host_token, wechat_code=wechat_code)

        return self._build_exchange_response(identity)

    def _build_exchange_response(self, identity: AuthIdentity) -> dict:
        display_name = identity.normalized_display_name()
        external_user_id = identity.normalized_external_user_id()
        access_token = create_access_token(
            user_id=identity.user_id,
            source=identity.source,
            display_name=display_name,
            member_status=identity.member_status,
            external_user_id=external_user_id,
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.settings.jwt_expire_minutes * 60,
            "user_id": identity.user_id,
            "source": identity.source,
            "display_name": display_name,
            "member_status": identity.member_status,
            "external_user_id": external_user_id,
        }

    def _verify_local_caigou_china_ticket(self, ticket: str) -> AuthIdentity:
        if ticket != CAIGOU_CHINA_LOCAL_TEST_TICKET:
            raise ValueError("Caigou China credential is invalid")
        return AuthIdentity(
            user_id="caigou-china-test-user",
            source="caigou_china",
            display_name="采购中国测试用户",
            member_status="active",
            external_user_id="test",
        )

    def _first_present(self, *values: str | None) -> str | None:
        for value in values:
            normalized = (value or "").strip()
            if normalized:
                return normalized
        return None


def get_auth_service() -> AuthService:
    """获取认证服务单例"""
    return AuthService()
