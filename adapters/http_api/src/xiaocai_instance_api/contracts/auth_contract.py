"""
认证接口契约

定义 POST /auth/exchange 的请求/响应结构
"""

from pydantic import BaseModel, Field


class AuthExchangeRequest(BaseModel):
    """
    身份换取请求

    用途: 宿主应用用自己的身份凭证换取 xiaocai 的 access_token
    """

    # Mock 模式参数
    mock: bool = Field(default=False, description="是否使用 Mock 模式")
    mock_user_id: str = Field(default="root-local-dev", description="Mock 用户 ID")

    # 真实模式参数
    host_token: str | None = Field(default=None, description="宿主应用的 token")
    wechat_code: str | None = Field(default=None, description="微信小程序 code")
    root_token: str | None = Field(default=None, description="root 登录 token")


class AuthExchangeResponse(BaseModel):
    """身份换取响应"""

    access_token: str = Field(..., description="xiaocai access_token")
    token_type: str = Field(default="bearer", description="Token 类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user_id: str = Field(..., description="用户 ID")
