"""
认证提供者基类

定义认证提供者的接口规范
"""

from abc import ABC, abstractmethod


class AuthProvider(ABC):
    """认证提供者基类"""

    @abstractmethod
    async def verify(
        self,
        host_token: str | None = None,
        wechat_code: str | None = None,
        root_token: str | None = None,
    ) -> str:
        """
        验证身份并返回用户 ID

        Args:
            host_token: 宿主应用 token
            wechat_code: 微信小程序 code
            root_token: root 登录 token

        Returns:
            str: 用户 ID

        Raises:
            ValueError: 验证失败
        """
        pass
