"""
安全依赖 - FastAPI Dependencies

职责:
1. 从请求中提取 JWT token
2. 验证 token 并解析 user_id
3. 作为 FastAPI Depends() 注入到需要认证的路由
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from xiaocai_instance_api.security.auth_claims import AuthClaims, claims_from_payload
from xiaocai_instance_api.security.token_codec import decode_access_token, decode_access_token_claims
import jwt


# HTTP Bearer 认证 scheme
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    从请求中提取并验证 JWT token，返回 user_id

    Args:
        credentials: FastAPI 自动注入的 HTTP 认证凭据

    Returns:
        str: 用户 ID

    Raises:
        HTTPException: Token 无效或过期

    使用示例:
        @router.get("/me")
        async def get_me(user_id: str = Depends(get_current_user_id)):
            return {"user_id": user_id}

    业务说明:
        - 适用于所有需要认证的接口
        - Token 格式: Authorization: Bearer <token>
        - 如果 token 无效，返回 401 Unauthorized
    """
    token = credentials.credentials

    try:
        user_id = decode_access_token(token)
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_auth_claims(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AuthClaims:
    token = credentials.credentials
    try:
        payload = decode_access_token_claims(token)
        return claims_from_payload(payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
