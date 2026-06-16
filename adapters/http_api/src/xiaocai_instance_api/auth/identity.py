"""
认证身份归一化模型

用途: 隔离 provider 原始返回，向 AuthService 提供稳定的本地登录态输入。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthIdentity:
    """认证成功后的最小身份信息。"""

    user_id: str
    source: str
    display_name: str = ""
    member_status: str = ""
    external_user_id: str = ""

    def normalized_display_name(self) -> str:
        return self.display_name.strip() or self.user_id

    def normalized_external_user_id(self) -> str:
        return self.external_user_id.strip() or self.user_id
