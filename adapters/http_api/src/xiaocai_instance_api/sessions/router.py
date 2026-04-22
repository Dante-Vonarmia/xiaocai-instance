"""
会话路由

接口:
- GET /sessions
- GET /sessions/{session_id}
- POST /sessions
- PATCH /sessions/{session_id}
- GET /sessions/{session_id}/messages
- POST /sessions/{session_id}/messages/append
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.dependencies import get_current_auth_claims
from xiaocai_instance_api.security.authorization import get_authorization_service
from xiaocai_instance_api.storage.conversation_store import get_conversation_store


router = APIRouter(prefix="/sessions", tags=["sessions"])
chat_compat_router = APIRouter(prefix="/chat", tags=["chat-compat"])


class SessionListResponse(BaseModel):
    sessions: list[dict]
    pagination: dict | None = None
    grouped: dict | None = None


class SessionCreateRequest(BaseModel):
    function_type: str = Field(default="auto")
    title: str = Field(default="新会话")
    project_id: str | None = Field(default=None)
    mode: str | None = Field(default=None)


class SessionCreateResponse(BaseModel):
    sessionId: str
    project_id: str | None
    user_id: str
    mode: str | None = None
    status: str


class SessionUpdateRequest(BaseModel):
    title: str | None = None
    status: str | None = None


class SessionUpdateResponse(BaseModel):
    sessionId: str
    title: str
    status: str


class MessageListResponse(BaseModel):
    messages: list[dict]


class AppendExchangeRequest(BaseModel):
    user_message: str
    assistant_message: str


class AppendExchangeResponse(BaseModel):
    success: bool


class SessionDeleteResponse(BaseModel):
    deleted: bool


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    function_type: str | None = None,
    project_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
    group_by_time: bool = False,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> SessionListResponse:
    authz = get_authorization_service()
    if project_id:
        await authz.require_project_access(claims=claims, project_id=project_id)
    store = get_conversation_store()
    safe_page = max(page, 1)
    safe_page_size = max(1, min(page_size, 100))
    total = await store.count_sessions(
        user_id=claims.user_id,
        function_type=function_type,
        project_id=project_id,
    )
    sessions = await store.list_sessions(
        user_id=claims.user_id,
        function_type=function_type,
        project_id=project_id,
        offset=(safe_page - 1) * safe_page_size,
        limit=safe_page_size,
    )
    session_items = [
        {
            "sessionId": item.session_id,
            "project_id": item.project_id,
            "user_id": item.user_id,
            "owner_user_id": item.owner_user_id,
            "visibility": item.visibility,
            "mode": item.mode,
            "title": item.title,
            "status": item.status,
            "updatedAt": item.updated_at,
            "preview": item.preview,
        }
        for item in sessions
    ]

    grouped = None
    if group_by_time:
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=7)
        groups = {"today": [], "last_7_days": [], "earlier": []}
        for item in session_items:
            try:
                updated_at = datetime.fromisoformat(item["updatedAt"])
            except ValueError:
                groups["earlier"].append(item)
                continue
            if updated_at.date() == now.date():
                groups["today"].append(item)
            elif updated_at >= week_start:
                groups["last_7_days"].append(item)
            else:
                groups["earlier"].append(item)
        grouped = groups

    return SessionListResponse(
        sessions=session_items,
        pagination={
            "page": safe_page,
            "page_size": safe_page_size,
            "total": total,
            "total_pages": (total + safe_page_size - 1) // safe_page_size,
        },
        grouped=grouped,
    )


@chat_compat_router.get("/sessions", response_model=SessionListResponse)
async def list_chat_sessions(
    function_type: str | None = None,
    project_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
    group_by_time: bool = False,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> SessionListResponse:
    return await list_sessions(
        function_type=function_type,
        project_id=project_id,
        page=page,
        page_size=page_size,
        group_by_time=group_by_time,
        claims=claims,
    )


@chat_compat_router.get("/sessions/{session_id}")
async def get_chat_session(
    session_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    return await get_session(session_id=session_id, claims=claims)


@chat_compat_router.post("/sessions", response_model=SessionCreateResponse)
async def create_chat_session(
    request: SessionCreateRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> SessionCreateResponse:
    return await create_session(request=request, claims=claims)


@chat_compat_router.patch("/sessions/{session_id}", response_model=SessionUpdateResponse)
async def update_chat_session(
    session_id: str,
    request: SessionUpdateRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> SessionUpdateResponse:
    return await update_session(
        session_id=session_id,
        request=request,
        claims=claims,
    )


@chat_compat_router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def list_chat_messages(
    session_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> MessageListResponse:
    return await list_messages(session_id=session_id, claims=claims)


@chat_compat_router.post("/sessions/{session_id}/messages/append", response_model=AppendExchangeResponse)
async def append_chat_exchange(
    session_id: str,
    request: AppendExchangeRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> AppendExchangeResponse:
    return await append_exchange(
        session_id=session_id,
        request=request,
        claims=claims,
    )


@chat_compat_router.delete("/sessions/{session_id}", response_model=SessionDeleteResponse)
async def delete_chat_session(
    session_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> SessionDeleteResponse:
    return await delete_session(session_id=session_id, claims=claims)


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_conversation_access(claims=claims, conversation_id=session_id)
    store = get_conversation_store()
    session = await store.get_session_for_user(user_id=claims.user_id, session_id=session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return {
        "sessionId": session.session_id,
        "project_id": session.project_id,
        "user_id": session.user_id,
        "owner_user_id": session.owner_user_id,
        "visibility": session.visibility,
        "mode": session.mode,
        "function_type": session.function_type,
        "title": session.title,
        "status": session.status,
    }


@router.post("", response_model=SessionCreateResponse)
async def create_session(
    request: SessionCreateRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> SessionCreateResponse:
    authz = get_authorization_service()
    if request.project_id:
        await authz.require_project_access(claims=claims, project_id=request.project_id)
    store = get_conversation_store()
    session = await store.create_session(
        user_id=claims.user_id,
        function_type=request.function_type,
        title=request.title,
        project_id=request.project_id,
        mode=request.mode,
        visibility="private",
    )
    return SessionCreateResponse(
        sessionId=session.session_id,
        project_id=session.project_id,
        user_id=session.user_id,
        mode=session.mode,
        status=session.status,
    )


@router.patch("/{session_id}", response_model=SessionUpdateResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> SessionUpdateResponse:
    if request.title is None and request.status is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided")
    if request.status is not None and request.status not in {"active", "archived"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status value")

    authz = get_authorization_service()
    await authz.require_conversation_write(claims=claims, conversation_id=session_id)
    store = get_conversation_store()
    session = await store.update_session_fields(
        user_id=claims.user_id,
        session_id=session_id,
        title=request.title,
        status=request.status,
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return SessionUpdateResponse(
        sessionId=session.session_id,
        title=session.title,
        status=session.status,
    )


@router.get("/{session_id}/messages", response_model=MessageListResponse)
async def list_messages(
    session_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> MessageListResponse:
    authz = get_authorization_service()
    await authz.require_conversation_access(claims=claims, conversation_id=session_id)
    store = get_conversation_store()
    messages = await store.list_messages(user_id=claims.user_id, session_id=session_id)
    return MessageListResponse(
        messages=[
            {
                "message_id": item.message_id,
                "role": item.role,
                "content": item.content,
                "created_at": item.created_at,
            }
            for item in messages
        ]
    )


@router.post("/{session_id}/messages/append", response_model=AppendExchangeResponse)
async def append_exchange(
    session_id: str,
    request: AppendExchangeRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> AppendExchangeResponse:
    authz = get_authorization_service()
    await authz.require_conversation_write(claims=claims, conversation_id=session_id)
    store = get_conversation_store()
    success = await store.append_exchange(
        user_id=claims.user_id,
        session_id=session_id,
        user_message=request.user_message,
        assistant_message=request.assistant_message,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return AppendExchangeResponse(success=True)


@router.delete("/{session_id}", response_model=SessionDeleteResponse)
async def delete_session(
    session_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> SessionDeleteResponse:
    authz = get_authorization_service()
    await authz.require_conversation_write(claims=claims, conversation_id=session_id)
    store = get_conversation_store()
    deleted = await store.delete_session(user_id=claims.user_id, session_id=session_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return SessionDeleteResponse(deleted=True)
