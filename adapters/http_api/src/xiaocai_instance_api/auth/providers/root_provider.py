"""
Root 认证提供者

用途: 在未接入宿主真实认证前，提供可控的 root 真实登录能力（非 mock）
"""

from xiaocai_instance_api.auth.providers.base import AuthProvider


class RootAuthProvider(AuthProvider):
    """Root 认证提供者"""

    def __init__(self, root_auth_token: str, root_user_id: str):
        self.root_auth_token = root_auth_token
        self.root_user_id = root_user_id

    async def verify(
        self,
        host_token: str | None = None,
        wechat_code: str | None = None,
        root_token: str | None = None,
    ) -> str:
        if not self.root_auth_token:
            raise ValueError("Root auth token is not configured")
        if not root_token:
            raise ValueError("Root token is required")
        if root_token != self.root_auth_token:
            raise ValueError("Invalid root token")
        return self.root_user_id
