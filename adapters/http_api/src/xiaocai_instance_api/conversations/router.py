"""
Conversation 路由（标准权限路径）
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.dependencies import get_current_auth_claims
from xiaocai_instance_api.security.authorization import get_authorization_service
from xiaocai_instance_api.storage.conversation_store import get_conversation_store


router = APIRouter(tags=["conversations"])


class ConversationCreateRequest(BaseModel):
    function_type: str = Field(default="requirement_canvas")
    title: str = Field(default="新会话")
    mode: str | None = None


class ConversationMessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=1)
    role: str = Field(default="user")


@router.get("/projects/{project_id}/conversations")
async def list_project_conversations(
    project_id: str,
    page: int = 1,
    page_size: int = 20,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_project_access(claims=claims, project_id=project_id)
    store = get_conversation_store()
    safe_page = max(page, 1)
    safe_page_size = max(1, min(page_size, 100))
    total = await store.count_sessions(user_id=claims.user_id, project_id=project_id)
    conversations = await store.list_sessions(
        user_id=claims.user_id,
        project_id=project_id,
        offset=(safe_page - 1) * safe_page_size,
        limit=safe_page_size,
    )
    return {
        "project_id": project_id,
        "conversations": [
            {
                "id": item.session_id,
                "project_id": item.project_id,
                "owner_user_id": item.owner_user_id,
                "visibility": item.visibility,
                "title": item.title,
                "function_type": item.function_type,
                "mode": item.mode,
                "status": item.status,
                "preview": item.preview,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            for item in conversations
        ],
        "pagination": {
            "page": safe_page,
            "page_size": safe_page_size,
            "total": total,
            "total_pages": (total + safe_page_size - 1) // safe_page_size,
        },
    }


@router.post("/projects/{project_id}/conversations")
async def create_project_conversation(
    project_id: str,
    request: ConversationCreateRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_project_access(claims=claims, project_id=project_id)
    store = get_conversation_store()
    record = await store.create_session(
        user_id=claims.user_id,
        function_type=request.function_type,
        title=request.title,
        project_id=project_id,
        mode=request.mode,
        visibility="private",
    )
    return {
        "id": record.session_id,
        "project_id": record.project_id,
        "owner_user_id": record.owner_user_id,
        "visibility": record.visibility,
        "title": record.title,
        "status": record.status,
        "mode": record.mode,
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation_detail(
    conversation_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_conversation_access(claims=claims, conversation_id=conversation_id)
    store = get_conversation_store()
    record = await store.get_session_for_user(user_id=claims.user_id, session_id=conversation_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return {
        "id": record.session_id,
        "project_id": record.project_id,
        "owner_user_id": record.owner_user_id,
        "visibility": record.visibility,
        "title": record.title,
        "function_type": record.function_type,
        "mode": record.mode,
        "status": record.status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


@router.get("/conversations/{conversation_id}/messages")
async def list_conversation_messages(
    conversation_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_conversation_access(claims=claims, conversation_id=conversation_id)
    store = get_conversation_store()
    records = await store.list_messages(user_id=claims.user_id, session_id=conversation_id)
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "id": item.message_id,
                "conversation_id": item.session_id,
                "sender_user_id": item.sender_user_id,
                "role": item.role,
                "content": item.content,
                "created_at": item.created_at,
            }
            for item in records
        ],
    }


@router.post("/conversations/{conversation_id}/messages")
async def append_conversation_message(
    conversation_id: str,
    request: ConversationMessageCreateRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_conversation_write(claims=claims, conversation_id=conversation_id)
    store = get_conversation_store()
    message = await store.append_message(
        user_id=claims.user_id,
        session_id=conversation_id,
        role=request.role,
        content=request.content,
    )
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return {
        "id": message.message_id,
        "conversation_id": message.session_id,
        "sender_user_id": message.sender_user_id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at,
    }
