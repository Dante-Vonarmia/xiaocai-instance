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
from xiaocai_instance_api.chat.kernel_client import get_kernel_client
from xiaocai_instance_api.chat.local_orchestration import build_local_orchestration_response
from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.conversation_store import get_conversation_store
import json


router = APIRouter(prefix="/chat", tags=["chat"])
INTAKE_MODE_PREFIX = "requirement_intake"
INTAKE_MODE_ALIAS = "requirement_canvas"


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
        function_type="requirement_canvas",
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
    if not isinstance(mode, str):
        return False
    normalized = mode.strip()
    return normalized == INTAKE_MODE_ALIAS or normalized.startswith(INTAKE_MODE_PREFIX)


def _resolve_effective_mode(request_mode: str | None, session_mode: str | None) -> str | None:
    if _is_intake_mode(session_mode):
        if _is_intake_mode(request_mode):
            return request_mode
        return session_mode
    return request_mode or session_mode


def _as_object(value: object) -> dict | None:
    if isinstance(value, dict):
        return value
    return None


def _as_list(value: object) -> list:
    if isinstance(value, list):
        return value
    return []


def _to_text(value: object) -> str:
    if _is_non_empty_text(value):
        return str(value).strip()
    return ""


def _to_bool(value: object) -> bool:
    return bool(value is True)


def _has_interaction_node(payload: dict) -> bool:
    question = _as_object(payload.get("question"))
    chooser = _as_object(payload.get("chooser"))
    interaction_node = _as_object(payload.get("interaction_node"))
    current_question = _as_object(payload.get("current_question"))
    missing_fields = _as_list(payload.get("missing_fields")) or _as_list(payload.get("required_missing"))
    return bool(question or chooser or interaction_node or current_question or missing_fields)


def _extract_pending_source(payload: dict) -> dict:
    for candidate in (
        payload,
        _as_object(payload.get("pending")),
        _as_object(payload.get("result")),
        _as_object(payload.get("payload")),
        _as_object(_as_object(payload.get("metadata")) or {}).get("pending"),
    ):
        if isinstance(candidate, dict) and candidate:
            if _has_interaction_node(candidate):
                return candidate
            gate = _as_object(candidate.get("gate"))
            command_type = _to_text(candidate.get("command_type"))
            if gate or command_type == "continue_collection":
                return candidate
    return {}


def _build_pending_contract(
    payload: dict,
    *,
    session_id: str,
    mode: str | None,
) -> dict | None:
    source = _extract_pending_source(payload)
    if not source:
        return None

    missing_fields = _as_list(source.get("missing_fields")) or _as_list(source.get("required_missing"))
    question = _as_object(source.get("question"))
    chooser = _as_object(source.get("chooser"))
    interaction_node = _as_object(source.get("interaction_node"))
    current_question = _as_object(source.get("current_question"))
    gate = _as_object(source.get("gate")) or {}
    command_type = _to_text(source.get("command_type")) or "continue_collection"
    current_stage = _to_text(source.get("current_stage")) or "collecting"
    summary_confirmed = _to_bool(source.get("summary_confirmed"))

    if not current_question:
        question_text = ""
        for candidate in (
            _to_text(_as_object(question or {}).get("question_text")),
            _to_text(_as_object(question or {}).get("text")),
            _to_text(_as_object(chooser or {}).get("question_text")),
            _to_text(_as_object(interaction_node or {}).get("title")),
            _to_text(_as_object(interaction_node or {}).get("text")),
        ):
            if candidate:
                question_text = candidate
                break
        if question_text:
            field_key = (
                _to_text(_as_object(question or {}).get("field_key"))
                or _to_text(_as_object(chooser or {}).get("field_key"))
                or _to_text(_as_object(interaction_node or {}).get("field_key"))
                or _to_text(_as_object(interaction_node or {}).get("id"))
                or (_to_text(missing_fields[0]) if missing_fields else "pending")
            )
            current_question = {
                "field_key": field_key,
                "field_label": _to_text(_as_object(question or {}).get("field_label")) or field_key,
                "question_text": question_text,
                "options": _as_list(_as_object(question or {}).get("options")) or _as_list(_as_object(chooser or {}).get("options")),
            }

    if not _has_interaction_node(
        {
            "question": question,
            "chooser": chooser,
            "interaction_node": interaction_node,
            "current_question": current_question,
            "missing_fields": missing_fields,
        }
    ):
        return None

    next_actions = _as_list(source.get("next_actions")) or _as_list(source.get("actions"))
    if not next_actions:
        next_actions = [{
            "action_key": "continue_collection",
            "label": "继续补充",
            "status": "available",
            "target_mode": mode or INTAKE_MODE_ALIAS,
        }]

    if not gate:
        gate = {
            "status": "blocked" if missing_fields else "collecting",
            "reason": "missing_required_fields" if missing_fields else "continue_collection",
        }

    question_payload = question
    if not question_payload and current_question:
        question_payload = {
            "field_key": current_question.get("field_key"),
            "question_text": current_question.get("question_text"),
            "options": current_question.get("options", []),
        }

    return {
        "current_stage": current_stage,
        "command_type": command_type,
        "missing_fields": missing_fields,
        "current_question": current_question or {},
        "question": question_payload or {},
        "chooser": chooser or {},
        "interaction_node": interaction_node or {},
        "next_actions": next_actions,
        "gate": gate,
        "summary_confirmed": summary_confirmed,
        "intake_session_id": _to_text(source.get("intake_session_id")) or session_id,
    }


def _should_suppress_assistant_message(pending_contract: dict | None) -> bool:
    if not isinstance(pending_contract, dict):
        return False
    command_type = _to_text(pending_contract.get("command_type"))
    gate = _as_object(pending_contract.get("gate")) or {}
    gate_status = _to_text(gate.get("status")).lower()
    return command_type == "continue_collection" or gate_status in {"blocked", "collecting", "pending"}


def _ensure_response_cards(
    cards: list[dict],
    mode: str | None,
    message: str,
    context: dict | None,
) -> list[dict]:
    _ = mode, message, context
    return cards


def _is_result_minimal(result: dict | None) -> bool:
    if not isinstance(result, dict):
        return True
    message = _to_text(result.get("message")) or _to_text(result.get("reply"))
    cards = result.get("cards")
    has_cards = isinstance(cards, list) and len(cards) > 0
    pending_contract = _build_pending_contract(
        result,
        session_id=_to_text(result.get("session_id")) or "unknown",
        mode=_to_text((_as_object(result.get("metadata")) or {}).get("mode")),
    )
    return not message and not has_cards and pending_contract is None


async def _build_local_fallback_result(
    *,
    request_message: str,
    request_session_id: str,
    mode: str | None,
    claims: AuthClaims,
) -> dict:
    conversation_store = get_conversation_store()
    history = await conversation_store.list_messages(user_id=claims.user_id, session_id=request_session_id)
    history_user_messages = [record.content for record in history if record.role == "user"]
    local_result = build_local_orchestration_response(
        user_message=request_message,
        mode=mode,
        history_user_messages=history_user_messages,
    )
    metadata: dict = dict(local_result.metadata)
    metadata["fallback"] = "local_orchestration"
    if local_result.pending_contract:
        metadata["pending_contract"] = local_result.pending_contract
    return {
        "message": local_result.message,
        "cards": local_result.cards,
        "session_id": request_session_id,
        "metadata": metadata,
    }


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
        mode = _resolve_effective_mode(request_mode=request_mode, session_mode=session.mode)
        await _check_mode_allowed(mode=mode)
        conversation_store = get_conversation_store()
        if mode and mode != session.mode:
            session = await conversation_store.update_session_mode(
                user_id=claims.user_id,
                session_id=request.session_id,
                mode=mode,
            ) or session
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
        kernel_context.setdefault("function_type", session.function_type)
        kernel_context.setdefault("intake_session_id", request.session_id)
        kernel_client = get_kernel_client()
        settings = get_settings()
        try:
            result = await kernel_client.chat_run(
                user_id=claims.user_id,
                message=request.message,
                session_id=request.session_id,
                context=kernel_context,
            )
        except Exception:
            if not settings.enable_local_orchestration_fallback:
                raise
            result = await _build_local_fallback_result(
                request_message=request.message,
                request_session_id=request.session_id,
                mode=mode,
                claims=claims,
            )
        if settings.enable_local_orchestration_fallback and _is_result_minimal(result):
            result = await _build_local_fallback_result(
                request_message=request.message,
                request_session_id=request.session_id,
                mode=mode,
                claims=claims,
            )
        pending_contract = _build_pending_contract(
            result if isinstance(result, dict) else {},
            session_id=request.session_id,
            mode=mode,
        )
        message = result.get("message") or result.get("reply", "")
        if _should_suppress_assistant_message(pending_contract):
            pending_question = _as_object((pending_contract or {}).get("question"))
            current_question = _as_object((pending_contract or {}).get("current_question"))
            message = _to_text((pending_question or {}).get("question_text"))
            if not message:
                message = _to_text((current_question or {}).get("question_text"))

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
                **({"pending_contract": pending_contract} if pending_contract else {}),
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}",
        )


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
            mode = _resolve_effective_mode(request_mode=request_mode, session_mode=session.mode)
            await _check_mode_allowed(mode=mode)
            conversation_store = get_conversation_store()
            if mode and mode != session.mode:
                session = await conversation_store.update_session_mode(
                    user_id=claims.user_id,
                    session_id=request.session_id,
                    mode=mode,
                ) or session
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
            kernel_context.setdefault("function_type", session.function_type)
            kernel_context.setdefault("intake_session_id", request.session_id)
            kernel_client = get_kernel_client()
            final_message_chunks: list[str] = []
            done_message: str | None = None
            latest_pending_contract: dict | None = None
            settings = get_settings()
            try:
                async for event in kernel_client.chat_stream(
                    user_id=claims.user_id,
                    message=request.message,
                    session_id=request.session_id,
                    context=kernel_context,
                ):
                    event_type = event.get("type", "message")
                    pending_contract = _build_pending_contract(
                        event if isinstance(event, dict) else {},
                        session_id=request.session_id,
                        mode=mode,
                    )
                    if pending_contract:
                        latest_pending_contract = pending_contract
                        event = {**event, **pending_contract}
                    if _is_intake_mode(mode) and str(event_type).lower() in ("token", "chunk", "content", "message"):
                        continue
                    chunk = _extract_event_chunk(event)
                    if chunk:
                        final_message_chunks.append(chunk)
                    if event_type in ("done", "complete") and isinstance(event.get("message"), str):
                        done_message = event.get("message")
                    yield f"event: {event_type}\n"
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    if pending_contract and event_type not in ("next_actions", "early_patch", "final_patch"):
                        yield "event: next_actions\n"
                        yield f"data: {json.dumps(pending_contract, ensure_ascii=False)}\n\n"
            except Exception:
                if not settings.enable_local_orchestration_fallback:
                    raise
                local_result = await _build_local_fallback_result(
                    request_message=request.message,
                    request_session_id=request.session_id,
                    mode=mode,
                    claims=claims,
                )
                latest_pending_contract = _as_object(_as_object(local_result.get("metadata") or {}).get("pending_contract"))
                fallback_message = _to_text(local_result.get("message"))
                fallback_cards = local_result.get("cards") if isinstance(local_result.get("cards"), list) else []
                yield "event: content\n"
                yield f"data: {json.dumps({'type': 'content', 'content': fallback_message}, ensure_ascii=False)}\n\n"
                if fallback_cards:
                    yield "event: ui_cards\n"
                    yield f"data: {json.dumps({'type': 'ui_cards', 'cards': fallback_cards}, ensure_ascii=False)}\n\n"
                if latest_pending_contract:
                    yield "event: next_actions\n"
                    yield f"data: {json.dumps(latest_pending_contract, ensure_ascii=False)}\n\n"
                yield "event: done\n"
                yield f"data: {json.dumps({'type': 'done', 'message': fallback_message}, ensure_ascii=False)}\n\n"
                done_message = fallback_message

            final_message = done_message or "".join(final_message_chunks)
            if _should_suppress_assistant_message(latest_pending_contract):
                pending_question = _as_object((latest_pending_contract or {}).get("question"))
                current_question = _as_object((latest_pending_contract or {}).get("current_question"))
                final_message = _to_text((pending_question or {}).get("question_text"))
                if not final_message:
                    final_message = _to_text((current_question or {}).get("question_text"))
            if final_message:
                await conversation_store.append_exchange(
                    user_id=claims.user_id,
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
