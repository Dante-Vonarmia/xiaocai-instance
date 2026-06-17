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
from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.dependencies import get_current_auth_claims
from xiaocai_instance_api.security.authorization import get_authorization_service
from xiaocai_instance_api.chat.kernel_client import KernelStreamConflictError, get_kernel_client
from xiaocai_instance_api.chat.kernel_request_body import sanitize_kernel_context_for_kernel
from xiaocai_instance_api.chat.context_policy import enrich_kernel_context_with_retrieval_policy
from xiaocai_instance_api.chat.instance_profile_projection import project_instance_profile_event
from xiaocai_instance_api.chat.orchestration.mode_resolution import (
    INTAKE_MODE_ALIAS,
    INTAKE_MODE_PREFIX,
    is_intake_mode,
    resolve_effective_mode,
)
from xiaocai_instance_api.chat.request_guard import evaluate_request_guard
from xiaocai_instance_api.chat.response_text import normalize_assistant_display_text, replace_event_text
from xiaocai_instance_api.chat.stream_text import StreamTextAccumulator
from xiaocai_instance_api.chat.stream_turn import (
    build_stream_busy_events,
    get_stream_turn_registry,
    serialize_sse_event,
)
from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.conversation_store import get_conversation_store
import json


router = APIRouter(prefix="/chat", tags=["chat"])
EMPTY_ASSISTANT_MESSAGE = "暂时没有收到完整回复，请稍后重试。"


def _is_non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _extract_project_id(context: dict | None) -> str | None:
    if not isinstance(context, dict):
        return None
    project_id = context.get("project_id")
    if isinstance(project_id, str) and project_id.strip():
        return project_id.strip()
    return None


async def _check_project_access(claims: AuthClaims, context: dict | None) -> None:
    project_id = _extract_project_id(context)
    if not project_id:
        return
    authz = get_authorization_service()
    await authz.require_project_access(claims=claims, project_id=project_id)


async def _ensure_session_exists(claims: AuthClaims, request: ChatRunRequest | ChatStreamRequest):
    store = get_conversation_store()
    authz = get_authorization_service()
    existing = await store.get_session_for_user(user_id=claims.user_id, session_id=request.session_id)
    if existing:
        requested_project_id = _extract_project_id(request.context)
        if requested_project_id and existing.project_id and requested_project_id != existing.project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Session project mismatch: {request.session_id}",
            )
        if existing.project_id:
            await authz.require_project_access(claims=claims, project_id=existing.project_id)
        return existing
    session_owner = await store.get_session_owner(session_id=request.session_id)
    if session_owner and session_owner != claims.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Session access denied: {request.session_id}",
        )
    context = request.context if isinstance(request.context, dict) else {}
    project_id = _extract_project_id(context)
    if project_id:
        await authz.require_project_access(claims=claims, project_id=project_id)
    mode = _extract_mode(context)
    return await store.create_session(
        user_id=claims.user_id,
        function_type="auto",
        title="新会话",
        project_id=project_id,
        mode=mode,
        session_id=request.session_id,
        visibility="private",
    )


def _extract_event_chunk(event: dict) -> str:
    for key in ("content", "delta", "chunk", "text", "message"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _extract_mode(source: dict | None) -> str | None:
    if not isinstance(source, dict):
        return None
    mode = source.get("mode")
    if _is_non_empty_text(mode):
        return str(mode).strip()
    return None


def _is_intake_mode(mode: str | None) -> bool:
    return is_intake_mode(mode)


def _resolve_effective_mode(
    request_mode: str | None,
    session_mode: str | None,
    message: str = "",
) -> str | None:
    return resolve_effective_mode(
        request_mode=request_mode,
        session_mode=session_mode,
        message=message,
    )


def _to_text(value: object) -> str:
    if _is_non_empty_text(value):
        return str(value).strip()
    return ""


def _ensure_response_cards(
    cards: list[dict],
    mode: str | None,
    message: str,
    context: dict | None,
) -> list[dict]:
    _ = mode, message, context
    return cards


def _resolve_stream_terminal_message(
    event: dict,
    final_message_chunks: list[str],
) -> tuple[str | None, dict]:
    """确保 stream 终态事件尽量携带可展示的 assistant 文本。"""
    event_message = _to_text(event.get("message"))
    if _is_non_empty_text(event_message):
        return event_message, event

    accumulated_message = "".join(final_message_chunks).strip()
    if _is_non_empty_text(accumulated_message):
        return accumulated_message, {**event, "message": accumulated_message}

    return None, event


def _should_accumulate_stream_chunk(event_type: str, event: dict) -> bool:
    """仅累计真正的 assistant 文本，避免把 error 文案拼进最终回复。"""
    if event_type in {"error", "done", "complete"}:
        return False
    channel = _to_text(event.get("channel"))
    if channel and channel != "assistant":
        return False
    return True


async def _check_mode_allowed(mode: str | None) -> None:
    if not mode:
        return
    settings = get_settings()
    if mode in settings.enabled_modes:
        return
    if _is_intake_mode(mode) and INTAKE_MODE_ALIAS in settings.enabled_modes:
        return
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
    claims: AuthClaims = Depends(get_current_auth_claims),
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
        authz = get_authorization_service()
        await _check_project_access(claims=claims, context=request.context)
        await _check_daily_limit(user_id=claims.user_id, context=request.context)
        session = await _ensure_session_exists(claims=claims, request=request)
        request_mode = _extract_mode(request.context)
        mode = _resolve_effective_mode(
            request_mode=request_mode,
            session_mode=session.mode,
            message=request.message,
        )
        await _check_mode_allowed(mode=mode)
        conversation_store = get_conversation_store()
        if mode and mode != session.mode:
            session = await conversation_store.update_session_mode(
                user_id=claims.user_id,
                session_id=request.session_id,
                mode=mode,
            ) or session
        guard = evaluate_request_guard(request.message)
        if not guard.allowed:
            response = ChatRunResponse(
                message=guard.message,
                cards=[],
                session_id=request.session_id,
                metadata={"request_guard": guard.to_metadata()},
            )
            await conversation_store.append_exchange(
                user_id=claims.user_id,
                session_id=request.session_id,
                user_message=request.message,
                assistant_message=response.message,
            )
            return response
        kernel_context = dict(request.context) if isinstance(request.context, dict) else {}
        if session.project_id and not kernel_context.get("project_id"):
            kernel_context["project_id"] = session.project_id
        if mode:
            kernel_context["mode"] = mode
        retrieval_scope = await authz.build_retrieval_scope(
            claims=claims,
            project_id=_extract_project_id(kernel_context),
        )
        kernel_context["auth_scope"] = retrieval_scope.to_dict()
        kernel_context = await enrich_kernel_context_with_retrieval_policy(
            claims=claims,
            kernel_context=kernel_context,
            user_message=request.message,
        )
        kernel_context.setdefault("intake_session_id", request.session_id)
        kernel_context = sanitize_kernel_context_for_kernel(kernel_context)
        kernel_client = get_kernel_client()
        result = await kernel_client.chat_run(
            user_id=claims.user_id,
            message=request.message,
            session_id=request.session_id,
            context=kernel_context,
        )
        message = result.get("message") or result.get("reply", "")
        message = normalize_assistant_display_text(message)
        if not _is_non_empty_text(message):
            message = EMPTY_ASSISTANT_MESSAGE

        response = ChatRunResponse(
            message=message,
            cards=_ensure_response_cards(
                cards=result.get("cards", []),
                mode=mode,
                message=message,
                context=request.context,
            ),
            session_id=result.get("session_id", request.session_id),
            metadata={
                **(result.get("metadata", {}) if isinstance(result.get("metadata"), dict) else {}),
                **({"intake_session_id": request.session_id} if mode and _is_intake_mode(mode) else {}),
            },
        )
        await conversation_store.append_exchange(
            user_id=claims.user_id,
            session_id=request.session_id,
            user_message=request.message,
            assistant_message=response.message,
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        fallback_response = ChatRunResponse(
            message=EMPTY_ASSISTANT_MESSAGE,
            cards=[],
            session_id=request.session_id,
            metadata={
                "degraded": True,
                "degrade_reason": "kernel_exception",
                "degrade_detail": str(e),
            },
        )
        conversation_store = get_conversation_store()
        await conversation_store.append_exchange(
            user_id=claims.user_id,
            session_id=request.session_id,
            user_message=request.message,
            assistant_message=fallback_response.message,
        )
        return fallback_response


@router.post("/stream")
async def chat_stream(
    request: ChatStreamRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
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
            authz = get_authorization_service()
            await _check_project_access(claims=claims, context=request.context)
            await _check_daily_limit(user_id=claims.user_id, context=request.context)
            session = await _ensure_session_exists(claims=claims, request=request)
            request_mode = _extract_mode(request.context)
            mode = _resolve_effective_mode(
                request_mode=request_mode,
                session_mode=session.mode,
                message=request.message,
            )
            await _check_mode_allowed(mode=mode)
            conversation_store = get_conversation_store()
            if mode and mode != session.mode:
                session = await conversation_store.update_session_mode(
                    user_id=claims.user_id,
                    session_id=request.session_id,
                    mode=mode,
                ) or session
            client_handles_writeback = _is_non_empty_text(request.command)
            guard = evaluate_request_guard(request.message)
            if not guard.allowed:
                guard_event = {
                    "type": "content",
                    "channel": "assistant",
                    "content": guard.message,
                    "session_id": request.session_id,
                    "request_guard": guard.to_metadata(),
                }
                done_event = {
                    "type": "done",
                    "status": "done",
                    "message": guard.message,
                    "session_id": request.session_id,
                    "request_guard": guard.to_metadata(),
                }
                complete_event = {
                    "type": "complete",
                    "status": "done",
                    "message": guard.message,
                    "session_id": request.session_id,
                    "request_guard": guard.to_metadata(),
                }
                yield "event: content\n"
                yield f"data: {json.dumps(guard_event, ensure_ascii=False)}\n\n"
                yield "event: done\n"
                yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"
                yield "event: complete\n"
                yield f"data: {json.dumps(complete_event, ensure_ascii=False)}\n\n"
                if not client_handles_writeback:
                    await conversation_store.append_exchange(
                        user_id=claims.user_id,
                        session_id=request.session_id,
                        user_message=request.message,
                        assistant_message=guard.message,
                    )
                return
            turn_registry = get_stream_turn_registry()
            turn_admission = await turn_registry.try_acquire(request.session_id)
            if not turn_admission.accepted:
                for event_type, payload in build_stream_busy_events(request.session_id):
                    yield serialize_sse_event(event_type, payload)
                return
            try:
                kernel_context = dict(request.context) if isinstance(request.context, dict) else {}
                if session.project_id and not kernel_context.get("project_id"):
                    kernel_context["project_id"] = session.project_id
                if mode:
                    kernel_context["mode"] = mode
                retrieval_scope = await authz.build_retrieval_scope(
                    claims=claims,
                    project_id=_extract_project_id(kernel_context),
                )
                kernel_context["auth_scope"] = retrieval_scope.to_dict()
                kernel_context = await enrich_kernel_context_with_retrieval_policy(
                    claims=claims,
                    kernel_context=kernel_context,
                    user_message=request.message,
                )
                kernel_context.setdefault("intake_session_id", request.session_id)
                kernel_context = sanitize_kernel_context_for_kernel(kernel_context)
                kernel_client = get_kernel_client()
                text_accumulator = StreamTextAccumulator()
                done_message: str | None = None
                emitted_done_event = False
                exchange_persisted = False
                event_iter = kernel_client.chat_stream(
                    user_id=claims.user_id,
                    message=request.message,
                    session_id=request.session_id,
                    context=kernel_context,
                )
                async for event in event_iter:
                    event_type = event.get("type", "message")
                    if event_type == "instance_profile":
                        event = project_instance_profile_event(event if isinstance(event, dict) else {})
                    chunk = _extract_event_chunk(event)
                    if chunk and _should_accumulate_stream_chunk(event_type, event):
                        event, chunk_delta, should_emit_event = text_accumulator.normalize_event(
                            event_type=event_type,
                            event=event,
                            chunk=chunk,
                        )
                        if not should_emit_event:
                            continue
                        display_delta = normalize_assistant_display_text(chunk_delta)
                        if not display_delta:
                            continue
                        if display_delta != chunk_delta:
                            event = replace_event_text(event, display_delta)
                        text_accumulator.append(display_delta)
                    if event_type in ("done", "complete"):
                        emitted_done_event = True
                        done_message, event = _resolve_stream_terminal_message(
                            event=event,
                            final_message_chunks=text_accumulator.chunks,
                        )
                        if done_message:
                            normalized_done_message = normalize_assistant_display_text(done_message)
                            if normalized_done_message:
                                done_message = normalized_done_message
                                event = replace_event_text(event, done_message)
                            else:
                                done_message = None
                                event = replace_event_text(event, "")
                        terminal_message_was_empty = done_message is None and not text_accumulator.chunks
                        if terminal_message_was_empty:
                            done_message = ""
                            event = {**event, "message": ""}
                        if terminal_message_was_empty and not _is_non_empty_text(done_message):
                            done_message = EMPTY_ASSISTANT_MESSAGE
                            event = replace_event_text(event, done_message)
                    yield f"event: {event_type}\n"
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                final_message = normalize_assistant_display_text(done_message or text_accumulator.final_message())
                if not _is_non_empty_text(final_message):
                    final_message = EMPTY_ASSISTANT_MESSAGE
                if not emitted_done_event:
                    synthetic_done_event = {
                        "type": "done",
                        "message": final_message,
                        "session_id": request.session_id,
                    }
                    yield "event: done\n"
                    yield f"data: {json.dumps(synthetic_done_event, ensure_ascii=False)}\n\n"
                if final_message and not client_handles_writeback:
                    await conversation_store.append_exchange(
                        user_id=claims.user_id,
                        session_id=request.session_id,
                        user_message=request.message,
                        assistant_message=final_message,
                    )
            except KernelStreamConflictError:
                for event_type, payload in build_stream_busy_events(request.session_id):
                    yield serialize_sse_event(event_type, payload)
                return
            finally:
                await turn_registry.release(request.session_id)
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
