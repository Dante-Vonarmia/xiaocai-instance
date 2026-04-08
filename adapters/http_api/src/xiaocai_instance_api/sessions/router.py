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

from xiaocai_instance_api.security.dependencies import get_current_user_id
from xiaocai_instance_api.storage.conversation_store import get_conversation_store
from xiaocai_instance_api.storage.ownership_store import get_ownership_store


router = APIRouter(prefix="/sessions", tags=["sessions"])


async def _ensure_project_access(user_id: str, project_id: str) -> None:
    ownership_store = get_ownership_store()
    has_access = await ownership_store.check_project_access(user_id=user_id, project_id=project_id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Project access denied: {project_id}",
        )


class SessionListResponse(BaseModel):
    sessions: list[dict]
    pagination: dict | None = None
    grouped: dict | None = None


class SessionCreateRequest(BaseModel):
    function_type: str = Field(default="requirement_canvas")
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
    title: str


class SessionUpdateResponse(BaseModel):
    sessionId: str
    title: str


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
    user_id: str = Depends(get_current_user_id),
) -> SessionListResponse:
    if project_id:
        await _ensure_project_access(user_id=user_id, project_id=project_id)
    store = get_conversation_store()
    safe_page = max(page, 1)
    safe_page_size = max(1, min(page_size, 100))
    total = await store.count_sessions(
        user_id=user_id,
        function_type=function_type,
        project_id=project_id,
    )
    sessions = await store.list_sessions(
        user_id=user_id,
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


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    store = get_conversation_store()
    session = await store.get_session(user_id=user_id, session_id=session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return {
        "sessionId": session.session_id,
        "project_id": session.project_id,
        "user_id": session.user_id,
        "mode": session.mode,
        "function_type": session.function_type,
        "title": session.title,
        "status": session.status,
    }


@router.post("", response_model=SessionCreateResponse)
async def create_session(
    request: SessionCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> SessionCreateResponse:
    if request.project_id:
        await _ensure_project_access(user_id=user_id, project_id=request.project_id)
    store = get_conversation_store()
    session = await store.create_session(
        user_id=user_id,
        function_type=request.function_type,
        title=request.title,
        project_id=request.project_id,
        mode=request.mode,
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
    user_id: str = Depends(get_current_user_id),
) -> SessionUpdateResponse:
    store = get_conversation_store()
    session = await store.update_session_title(
        user_id=user_id,
        session_id=session_id,
        title=request.title,
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return SessionUpdateResponse(
        sessionId=session.session_id,
        title=session.title,
    )


@router.get("/{session_id}/messages", response_model=MessageListResponse)
async def list_messages(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
) -> MessageListResponse:
    store = get_conversation_store()
    messages = await store.list_messages(user_id=user_id, session_id=session_id)
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
    user_id: str = Depends(get_current_user_id),
) -> AppendExchangeResponse:
    store = get_conversation_store()
    success = await store.append_exchange(
        user_id=user_id,
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
    user_id: str = Depends(get_current_user_id),
) -> SessionDeleteResponse:
    store = get_conversation_store()
    deleted = await store.delete_session(user_id=user_id, session_id=session_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return SessionDeleteResponse(deleted=True)
