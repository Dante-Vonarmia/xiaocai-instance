"""
认证会话 Cookie 边界

集中管理浏览器会话 Cookie，避免路由和认证依赖散落硬编码名称。
"""

from fastapi import Response


ACCESS_COOKIE_NAME = "xiaocai_access_token"
SESSION_MARKER_COOKIE_NAME = "xiaocai_session_active"
COOKIE_PATH = "/"
COOKIE_SAMESITE = "lax"


def set_auth_session_cookies(response: Response, access_token: str) -> None:
    token = access_token.strip()
    if not token:
        return

    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite=COOKIE_SAMESITE,
        path=COOKIE_PATH,
    )
    response.set_cookie(
        key=SESSION_MARKER_COOKIE_NAME,
        value="1",
        httponly=False,
        secure=True,
        samesite=COOKIE_SAMESITE,
        path=COOKIE_PATH,
    )


def clear_auth_session_cookies(response: Response) -> None:
    response.delete_cookie(
        key=ACCESS_COOKIE_NAME,
        path=COOKIE_PATH,
        samesite=COOKIE_SAMESITE,
        secure=True,
        httponly=True,
    )
    response.delete_cookie(
        key=SESSION_MARKER_COOKIE_NAME,
        path=COOKIE_PATH,
        samesite=COOKIE_SAMESITE,
        secure=True,
        httponly=False,
    )
