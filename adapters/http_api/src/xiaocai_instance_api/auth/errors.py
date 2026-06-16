"""
认证错误契约

用途: 统一认证失败的错误码、用户提示和 HTTP 状态，避免技术异常透传到产品界面。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthErrorSpec:
    code: str
    user_message: str
    status_code: int


AUTH_ERROR_SPECS: dict[str, AuthErrorSpec] = {
    "CREDENTIAL_MISSING": AuthErrorSpec(
        code="CREDENTIAL_MISSING",
        user_message="请从采购中国小程序进入云鹤AI服务",
        status_code=401,
    ),
    "CREDENTIAL_INVALID": AuthErrorSpec(
        code="CREDENTIAL_INVALID",
        user_message="登录凭证无效，请返回采购中国小程序重新进入",
        status_code=401,
    ),
    "CREDENTIAL_EXPIRED": AuthErrorSpec(
        code="CREDENTIAL_EXPIRED",
        user_message="登录已过期，请返回采购中国小程序重新进入",
        status_code=401,
    ),
    "CREDENTIAL_USED": AuthErrorSpec(
        code="CREDENTIAL_USED",
        user_message="登录凭证已失效，请重新进入",
        status_code=401,
    ),
    "USER_DISABLED": AuthErrorSpec(
        code="USER_DISABLED",
        user_message="当前账号状态不可用，请联系采购中国客服",
        status_code=403,
    ),
    "VERIFY_TIMEOUT": AuthErrorSpec(
        code="VERIFY_TIMEOUT",
        user_message="登录服务暂时不可用，请稍后重试",
        status_code=503,
    ),
    "VERIFY_FAILED": AuthErrorSpec(
        code="VERIFY_FAILED",
        user_message="登录服务暂时不可用，请稍后重试",
        status_code=503,
    ),
    "CONFIG_MISSING": AuthErrorSpec(
        code="CONFIG_MISSING",
        user_message="云鹤AI登录服务配置异常，请联系管理员",
        status_code=500,
    ),
    "SIGNATURE_INVALID": AuthErrorSpec(
        code="SIGNATURE_INVALID",
        user_message="云鹤AI登录服务配置异常，请联系管理员",
        status_code=502,
    ),
    "APP_UNAUTHORIZED": AuthErrorSpec(
        code="APP_UNAUTHORIZED",
        user_message="云鹤AI登录服务暂未获得授权，请联系管理员",
        status_code=502,
    ),
    "RESPONSE_INVALID": AuthErrorSpec(
        code="RESPONSE_INVALID",
        user_message="登录服务暂时不可用，请稍后重试",
        status_code=502,
    ),
}


class AuthError(Exception):
    """产品级认证错误。"""

    def __init__(self, code: str, *, log_message: str = ""):
        spec = AUTH_ERROR_SPECS.get(code, AUTH_ERROR_SPECS["VERIFY_FAILED"])
        super().__init__(log_message or spec.user_message)
        self.code = spec.code
        self.user_message = spec.user_message
        self.status_code = spec.status_code
        self.log_message = log_message

    def to_detail(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.user_message,
        }
