"""
认证路由

提供的接口:
- POST /auth/exchange - 身份换取（宿主应用 token 或微信 code 换取 xiaocai token）
"""

import logging

from fastapi import APIRouter, HTTPException
from xiaocai_instance_api.auth.errors import AuthError
from xiaocai_instance_api.auth.errors import AUTH_ERROR_SPECS
from xiaocai_instance_api.contracts.auth_contract import (
    AuthExchangeRequest,
    AuthExchangeResponse,
)
from xiaocai_instance_api.auth.service import get_auth_service


router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


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
            login_ticket=request.login_ticket,
            ticket=request.ticket,
            token=request.token,
            credential=request.credential,
            sso_ticket=request.sso_ticket,
            auth_code=request.auth_code,
            root_token=request.root_token,
        )

        return AuthExchangeResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            user_id=result["user_id"],
            source=result["source"],
            display_name=result["display_name"],
            member_status=result["member_status"],
            external_user_id=result["external_user_id"],
        )
    except AuthError as e:
        logger.warning(
            "auth exchange failed",
            extra={"auth_error_code": e.code, "auth_log_message": e.log_message},
        )
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_detail(),
        )
    except ValueError as e:
        error = AuthError("CREDENTIAL_INVALID", log_message=str(e))
        logger.warning(
            "auth exchange failed",
            extra={"auth_error_code": error.code, "auth_log_message": error.log_message},
        )
        raise HTTPException(
            status_code=error.status_code,
            detail=error.to_detail(),
        )
    except Exception as e:
        spec = AUTH_ERROR_SPECS["VERIFY_FAILED"]
        logger.exception("auth exchange unexpected failure")
        raise HTTPException(
            status_code=spec.status_code,
            detail={"code": spec.code, "message": spec.user_message},
        )
