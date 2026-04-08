"""
认证路由

提供的接口:
- POST /auth/exchange - 身份换取（宿主应用 token 或微信 code 换取 xiaocai token）
"""

from fastapi import APIRouter, HTTPException, status
from xiaocai_instance_api.contracts.auth_contract import (
    AuthExchangeRequest,
    AuthExchangeResponse,
)
from xiaocai_instance_api.auth.service import get_auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/exchange", response_model=AuthExchangeResponse)
async def exchange_token(request: AuthExchangeRequest) -> AuthExchangeResponse:
    """
    身份换取 - 宿主应用 token 或微信 code 换取 xiaocai JWT token

    业务流程:
    1. 如果 mock=true，直接返回测试 token
    2. 如果有 host_token，调用宿主应用验证接口
    3. 如果有 wechat_code，调用微信 API 验证
    4. 验证成功后，生成 xiaocai JWT token 并返回

    参考: docs/discussions/phase-1-member-management.md
          用户管理和认证流程
    """
    try:
        auth_service = get_auth_service()
        result = await auth_service.exchange_token(
            mock=request.mock,
            mock_user_id=request.mock_user_id,
            host_token=request.host_token,
            wechat_code=request.wechat_code,
            root_token=request.root_token,
        )

        return AuthExchangeResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            user_id=result["user_id"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}",
        )
