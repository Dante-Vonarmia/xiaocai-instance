"""
JWT Token 编解码器

职责:
1. 生成 JWT access token
2. 解析和验证 JWT token
3. 提取 user_id 等 claims
"""

from datetime import datetime, timedelta, timezone
import jwt
from xiaocai_instance_api.settings import get_settings


def create_access_token(user_id: str) -> str:
    """
    生成 JWT access token

    Args:
        user_id: 用户 ID

    Returns:
        str: JWT token 字符串

    业务说明:
        - Token 中包含 user_id, exp (过期时间), iat (签发时间)
        - 使用 HS256 算法
        - 过期时间从配置读取
    """
    settings = get_settings()

    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)

    payload = {
        "sub": user_id,  # subject = user_id
        "exp": expire,
        "iat": now,
    }

    # 2. 编码
    token = jwt.encode(payload, settings.instance_jwt_secret, algorithm=settings.jwt_algorithm)

    return token


def decode_access_token(token: str) -> str:
    """
    解析 JWT token 并返回 user_id

    Args:
        token: JWT token 字符串

    Returns:
        str: 用户 ID

    Raises:
        jwt.ExpiredSignatureError: Token 已过期
        jwt.InvalidTokenError: Token 无效

    业务说明:
        - 验证签名
        - 检查过期时间
        - 提取 user_id
    """
    settings = get_settings()

    try:
        payload = jwt.decode(token, settings.instance_jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            raise jwt.InvalidTokenError("Missing user_id in token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError:
        raise
