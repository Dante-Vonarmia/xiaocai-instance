"""
对话路由

提供的接口:
- POST /chat/run - 同步对话（等待完整响应）
- POST /chat/stream - 流式对话（SSE 实时返回）
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
from xiaocai_instance_api.contracts.chat_contract import (
    ChatRunRequest,
    ChatRunResponse,
    ChatStreamRequest,
)
from xiaocai_instance_api.security.dependencies import get_current_user_id
from xiaocai_instance_api.chat.kernel_client import get_kernel_client
from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.conversation_store import get_conversation_store
from xiaocai_instance_api.storage.ownership_store import get_ownership_store
import json


router = APIRouter(prefix="/chat", tags=["chat"])


async def _check_project_access(user_id: str, context: dict | None) -> None:
    if not isinstance(context, dict):
        return
    project_id = context.get("project_id")
    if not project_id:
        return
    store = get_ownership_store()
    has_access = await store.check_project_access(user_id=user_id, project_id=project_id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Project access denied: {project_id}",
        )


async def _ensure_session_exists(user_id: str, request: ChatRunRequest | ChatStreamRequest):
    store = get_conversation_store()
    existing = await store.get_session(user_id=user_id, session_id=request.session_id)
    if existing:
        return existing
    session_owner = await store.get_session_owner(session_id=request.session_id)
    if session_owner and session_owner != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Session access denied: {request.session_id}",
        )
    context = request.context if isinstance(request.context, dict) else {}
    mode = _extract_mode(context)
    return await store.create_session(
        user_id=user_id,
        function_type="requirement_canvas",
        title="新会话",
        project_id=context.get("project_id"),
        mode=mode,
        session_id=request.session_id,
    )


def _extract_event_chunk(event: dict) -> str:
    for key in ("content", "delta", "chunk", "text", "message"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _extract_mode(context: dict | None) -> str | None:
    if not isinstance(context, dict):
        return None
    mode = context.get("mode")
    if isinstance(mode, str) and mode.strip():
        return mode.strip()
    return None


def _ensure_response_cards(
    cards: list[dict],
    mode: str | None,
    message: str,
    context: dict | None,
) -> list[dict]:
    _ = mode, message, context
    return cards


async def _check_mode_allowed(context: dict | None) -> None:
    mode = _extract_mode(context)
    if not mode:
        return
    settings = get_settings()
    if mode not in settings.enabled_modes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"mode not allowed: {mode}",
        )


async def _check_daily_limit(user_id: str, context: dict | None = None) -> None:
    settings = get_settings()
    project_id: str | None = None
    if isinstance(context, dict):
        candidate = context.get("project_id")
        if isinstance(candidate, str) and candidate.strip():
            project_id = candidate.strip()
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    store = get_conversation_store()
    if settings.daily_message_limit > 0:
        used = await store.count_user_messages_since(user_id=user_id, since_iso=today_start)
        if used >= settings.daily_message_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="daily message limit exceeded",
            )
    if settings.daily_project_message_limit > 0 and project_id:
        project_used = await store.count_user_project_messages_since(
            user_id=user_id,
            project_id=project_id,
            since_iso=today_start,
        )
        if project_used >= settings.daily_project_message_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"daily project message limit exceeded: {project_id}",
            )


@router.post("/run", response_model=ChatRunResponse)
async def chat_run(
    request: ChatRunRequest,
    user_id: str = Depends(get_current_user_id),
) -> ChatRunResponse:
    """
    同步对话 - 等待 FLARE kernel 返回完整响应

    业务流程:
    1. 从 JWT token 中提取 user_id（通过 Depends 自动注入）
    2. 调用 FLARE kernel 的 /chat/run 接口
    3. kernel 会调用 7 Engine 处理对话:
       - Decision Engine: 意图识别
       - Knowledge Engine: 知识检索
       - Execution Engine: 执行采购流程
       - Presentation Engine: 生成 UI cards
    4. 返回文本 + UI cards

    参考: docs/discussions/phase-1-procurement-product-logic.md
          需求梳理流程、智能寻源流程、意图识别
    """
    try:
        await _check_project_access(user_id=user_id, context=request.context)
        await _check_mode_allowed(context=request.context)
        await _check_daily_limit(user_id=user_id, context=request.context)
        session = await _ensure_session_exists(user_id=user_id, request=request)
        mode = _extract_mode(request.context)
        kernel_context = dict(request.context) if isinstance(request.context, dict) else {}
        kernel_context.setdefault("function_type", session.function_type)
        kernel_client = get_kernel_client()
        result = await kernel_client.chat_run(
            user_id=user_id,
            message=request.message,
            session_id=request.session_id,
            context=kernel_context,
        )

        response = ChatRunResponse(
            message=result.get("message") or result.get("reply", ""),
            cards=_ensure_response_cards(
                cards=result.get("cards", []),
                mode=mode,
                message=result.get("message") or result.get("reply", ""),
                context=request.context,
            ),
            session_id=result.get("session_id", request.session_id),
            metadata=result.get("metadata", {}),
        )
        conversation_store = get_conversation_store()
        await conversation_store.append_exchange(
            user_id=user_id,
            session_id=request.session_id,
            user_message=request.message,
            assistant_message=response.message,
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}",
        )


@router.post("/stream")
async def chat_stream(
    request: ChatStreamRequest,
    user_id: str = Depends(get_current_user_id),
) -> StreamingResponse:
    """
    流式对话 - 使用 Server-Sent Events (SSE) 实时返回响应

    业务流程:
    1. 从 JWT token 中提取 user_id
    2. 调用 FLARE kernel 的 /chat/stream 接口
    3. 逐步返回:
       - token: 文本 token（逐字显示）
       - card: UI 卡片（表单、确认框等）
       - done: 对话结束
    4. 前端使用 EventSource API 接收

    事件格式:
        data: {"type": "token", "content": "你好"}
        data: {"type": "card", "card": {...}}
        data: {"type": "done"}

    参考: FLARE packages - flare-chat-ui 的流式渲染
    """
    async def event_generator():
        """SSE 事件生成器"""
        try:
            await _check_project_access(user_id=user_id, context=request.context)
            await _check_mode_allowed(context=request.context)
            await _check_daily_limit(user_id=user_id, context=request.context)
            session = await _ensure_session_exists(user_id=user_id, request=request)
            kernel_context = dict(request.context) if isinstance(request.context, dict) else {}
            kernel_context.setdefault("function_type", session.function_type)
            kernel_client = get_kernel_client()
            final_message_chunks: list[str] = []
            done_message: str | None = None
            async for event in kernel_client.chat_stream(
                user_id=user_id,
                message=request.message,
                session_id=request.session_id,
                context=kernel_context,
            ):
                event_type = event.get("type", "message")
                chunk = _extract_event_chunk(event)
                if chunk:
                    final_message_chunks.append(chunk)
                if event_type in ("done", "complete") and isinstance(event.get("message"), str):
                    done_message = event.get("message")
                yield f"event: {event_type}\n"
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            final_message = done_message or "".join(final_message_chunks)
            if final_message:
                conversation_store = get_conversation_store()
                await conversation_store.append_exchange(
                    user_id=user_id,
                    session_id=request.session_id,
                    user_message=request.message,
                    assistant_message=final_message,
                )
        except Exception as e:
            error_event = {"type": "error", "message": str(e)}
            yield "event: error\n"
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
