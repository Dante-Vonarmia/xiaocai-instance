"""
认证提供者基类

定义认证提供者的接口规范
"""

from abc import ABC, abstractmethod

from xiaocai_instance_api.auth.identity import AuthIdentity


class AuthProvider(ABC):
    """认证提供者基类"""

    @abstractmethod
    async def verify(
        self,
        host_token: str | None = None,
        wechat_code: str | None = None,
        credential: str | None = None,
        login_ticket: str | None = None,
        root_token: str | None = None,
    ) -> AuthIdentity:
        """
        验证身份并返回归一化身份

        Args:
            host_token: 宿主应用 token
            wechat_code: 微信小程序 code
            credential: 采购中国小程序 credential
            login_ticket: 采购中国 credential 兼容字段
            root_token: root 登录 token

        Returns:
            AuthIdentity: 归一化身份

        Raises:
            ValueError: 验证失败
        """
        pass
