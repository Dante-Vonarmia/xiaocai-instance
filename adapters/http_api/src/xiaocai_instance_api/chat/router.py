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
from xiaocai_instance_api.chat.context_policy import enrich_kernel_context_with_retrieval_policy
from xiaocai_instance_api.chat.pending_policy import apply_confidence_policy_to_pending_contract
from xiaocai_instance_api.chat.analysis_projection import (
    build_analysis_report_projection,
    has_structured_analysis_content,
)
from xiaocai_instance_api.chat.analysis_events import extract_analysis_payload, with_analysis_payload
from xiaocai_instance_api.chat.sourcing_projection import build_sourcing_candidates_projection
from xiaocai_instance_api.chat.orchestration.field_candidates import normalize_candidate_payload
from xiaocai_instance_api.chat.orchestration.mode_resolution import (
    INTAKE_MODE_ALIAS,
    INTAKE_MODE_PREFIX,
    is_intake_mode,
    resolve_effective_mode,
)
from xiaocai_instance_api.chat.orchestration.question_options import normalize_question_payload
from xiaocai_instance_api.chat.request_guard import evaluate_request_guard
from xiaocai_instance_api.chat.response_text import normalize_assistant_display_text, replace_event_text
from xiaocai_instance_api.chat.stream_text import StreamTextAccumulator
from xiaocai_instance_api.chat.stream_turn import (
    build_stream_busy_events,
    get_stream_turn_registry,
    serialize_sse_event,
)
from xiaocai_instance_api.chat.workbench_projection import (
    build_intake_workbench_projection,
    projection_key,
)
from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.conversation_store import get_conversation_store
import json


router = APIRouter(prefix="/chat", tags=["chat"])
EMPTY_ASSISTANT_MESSAGE = (
    "我这边没有拿到完整的可展示结果，先不直接给结论。\n"
    "你可以继续补充采购目标、品类/规格、数量、预算、交付地点和时间；我会基于这些信息继续梳理需求。\n"
    "如果这是系统异常，请稍后重试或回到上一步继续。"
)


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


def _as_object(value: object) -> dict | None:
    if isinstance(value, dict):
        return value
    return None


def _as_list(value: object) -> list:
    if isinstance(value, list):
        return value
    return []


def _has_usable_canvas_state_event(event: dict) -> bool:
    """Respect FLARE-native canvas state when it already carries intake UI state."""
    canvas_state = _as_object(event.get("canvas_state"))
    if not canvas_state:
        payload = _as_object(event.get("payload"))
        canvas_state = _as_object((payload or {}).get("canvas_state"))
    if not canvas_state:
        return False
    if _as_object(canvas_state.get("current_question")):
        return True
    if _as_list(canvas_state.get("question_plan")):
        return True
    if _as_list(canvas_state.get("collected")) or _as_list(canvas_state.get("missing")):
        return True
    progress = canvas_state.get("progress")
    return isinstance(progress, (int, float)) and progress > 0


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
    if not _is_intake_mode(mode):
        return None

    source = _extract_pending_source(payload)
    if not source:
        return None

    missing_fields = _as_list(source.get("missing_fields")) or _as_list(source.get("required_missing"))
    question = normalize_question_payload(_as_object(source.get("question")))
    chooser = normalize_question_payload(_as_object(source.get("chooser")))
    interaction_node = _as_object(source.get("interaction_node"))
    current_question = normalize_question_payload(_as_object(source.get("current_question")))
    gate = _as_object(source.get("gate")) or {}
    command_type = _to_text(source.get("command_type")) or "continue_collection"
    current_stage = _to_text(source.get("current_stage")) or "collecting"
    summary_confirmed = _to_bool(source.get("summary_confirmed"))
    candidate_payload = normalize_candidate_payload(source)

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
        "candidate_fields": candidate_payload["candidate_fields"],
        "rejected_candidates": candidate_payload["rejected_candidates"],
        "intake_session_id": _to_text(source.get("intake_session_id")) or session_id,
    }


def _should_suppress_assistant_message(pending_contract: dict | None) -> bool:
    if not pending_contract:
        return False
    if not _is_intake_mode(_to_text(pending_contract.get("mode_key"))):
        return False
    current_question = _as_object(pending_contract.get("current_question"))
    missing_fields = _as_list(pending_contract.get("missing_fields"))
    gate = _as_object(pending_contract.get("gate")) or {}
    gate_status = _to_text(gate.get("status")).lower()
    return bool(current_question or missing_fields or gate_status == "blocked")


def _pending_question_text(pending_contract: dict | None) -> str:
    pending_question = _as_object((pending_contract or {}).get("question"))
    current_question = _as_object((pending_contract or {}).get("current_question"))
    return _to_text((pending_question or {}).get("question_text")) or _to_text((current_question or {}).get("question_text"))


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
        kernel_context.setdefault("function_type", session.function_type)
        kernel_context.setdefault("intake_session_id", request.session_id)
        kernel_client = get_kernel_client()
        result = await kernel_client.chat_run(
            user_id=claims.user_id,
            message=request.message,
            session_id=request.session_id,
            context=kernel_context,
        )
        pending_contract = _build_pending_contract(
            result if isinstance(result, dict) else {},
            session_id=request.session_id,
            mode=mode,
        )
        pending_contract = apply_confidence_policy_to_pending_contract(
            pending_contract=pending_contract,
            confidence_policy=kernel_context.get("confidence_policy"),
            clarification_policy=kernel_context.get("clarification_policy"),
            category_prior=kernel_context.get("category_prior"),
            session_id=request.session_id,
            mode=mode,
        )
        # FLARE owns user-visible assistant text; adapter-side pending/projection
        # may only fill an otherwise empty response, never override kernel output.
        message = result.get("message") or result.get("reply", "")
        has_kernel_message = _is_non_empty_text(message)
        if not has_kernel_message and _should_suppress_assistant_message(pending_contract):
            pending_question = _as_object((pending_contract or {}).get("question"))
            current_question = _as_object((pending_contract or {}).get("current_question"))
            message = _to_text((pending_question or {}).get("question_text"))
            if not message:
                message = _to_text((current_question or {}).get("question_text"))
        if not _is_non_empty_text(message):
            message = EMPTY_ASSISTANT_MESSAGE
        message = normalize_assistant_display_text(message)

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
                kernel_context.setdefault("function_type", session.function_type)
                kernel_context.setdefault("intake_session_id", request.session_id)
                kernel_client = get_kernel_client()
                text_accumulator = StreamTextAccumulator()
                done_message: str | None = None
                emitted_done_event = False
                latest_pending_contract: dict | None = None
                exchange_persisted = False
                emitted_projection_keys: set[str] = set()
                emitted_suppressed_question = False
                has_native_analysis_payload = False
                has_native_structured_analysis_payload = False
                event_iter = kernel_client.chat_stream(
                    user_id=claims.user_id,
                    message=request.message,
                    session_id=request.session_id,
                    context=kernel_context,
                )
                async for event in event_iter:
                    event_type = event.get("type", "message")
                    native_analysis_payload = extract_analysis_payload(event)
                    if native_analysis_payload:
                        has_native_analysis_payload = True
                        has_native_structured_analysis_payload = (
                            has_native_structured_analysis_payload
                            or has_structured_analysis_content(native_analysis_payload)
                        )
                    pending_contract = _build_pending_contract(
                        event if isinstance(event, dict) else {},
                        session_id=request.session_id,
                        mode=mode,
                    )
                    pending_contract = apply_confidence_policy_to_pending_contract(
                        pending_contract=pending_contract,
                        confidence_policy=kernel_context.get("confidence_policy"),
                        clarification_policy=kernel_context.get("clarification_policy"),
                        category_prior=kernel_context.get("category_prior"),
                        session_id=request.session_id,
                        mode=mode,
                    )
                    native_pending_contract = pending_contract
                    workbench_projection = build_intake_workbench_projection(
                        pending_contract=pending_contract,
                        mode=mode,
                        session_id=request.session_id,
                        user_message=request.message,
                        candidate_context=kernel_context,
                    )
                    projection_events: list[tuple[str, dict]] = []
                    if workbench_projection:
                        projected_pending = _as_object(workbench_projection.get("pending_contract"))
                        if projected_pending:
                            pending_contract = projected_pending
                        plan_payload = _as_object(workbench_projection.get("plan_payload"))
                        canvas_payload = _as_object(workbench_projection.get("canvas_payload"))
                        if plan_payload:
                            projection_events.append(("primary_flow_payload", plan_payload))
                        if canvas_payload:
                            projection_events.append(("canvas_state", canvas_payload))
                    has_native_canvas_state = event_type == "canvas_state" and _has_usable_canvas_state_event(event)
                    if has_native_canvas_state:
                        projection_events = []
                    if event_type != "sourcing_candidates":
                        sourcing_payload = build_sourcing_candidates_projection(
                            kernel_context=kernel_context,
                            mode=mode,
                            session_id=request.session_id,
                            user_message=request.message,
                        )
                        if sourcing_payload:
                            projection_events.append(("sourcing_candidates", sourcing_payload))
                    if native_pending_contract:
                        latest_pending_contract = native_pending_contract
                    if pending_contract:
                        event = {**event, **pending_contract}
                    if event_type == "canvas_state" and workbench_projection and not has_native_canvas_state:
                        canvas_payload = _as_object(workbench_projection.get("canvas_payload"))
                        if canvas_payload:
                            event = canvas_payload
                            emitted_projection_keys.add(f"canvas_state:{projection_key(canvas_payload)}")
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
                        if display_delta != chunk_delta:
                            event = replace_event_text(event, display_delta)
                        text_accumulator.append(chunk_delta)
                    if event_type in ("done", "complete"):
                        emitted_done_event = True
                        done_message, event = _resolve_stream_terminal_message(
                            event=event,
                            final_message_chunks=text_accumulator.chunks,
                        )
                        if done_message:
                            done_message = normalize_assistant_display_text(done_message)
                            event = replace_event_text(event, done_message)
                        # Preserve FLARE text when it exists. Question fallback is
                        # only for native pending events that did not emit text.
                        suppress_contract = latest_pending_contract or native_pending_contract
                        if not _is_non_empty_text(done_message) and _should_suppress_assistant_message(suppress_contract):
                            question_text = _pending_question_text(suppress_contract)
                            if question_text:
                                done_message = question_text
                                event = {**event, "message": question_text, "content": question_text}
                                if not emitted_suppressed_question:
                                    replacement_event = {
                                        "type": "text.replace",
                                        "content": question_text,
                                        "session_id": request.session_id,
                                    }
                                    yield "event: text.replace\n"
                                    yield f"data: {json.dumps(replacement_event, ensure_ascii=False)}\n\n"
                                    emitted_suppressed_question = True
                        if done_message is None and not text_accumulator.chunks:
                            done_message = EMPTY_ASSISTANT_MESSAGE
                            event = {**event, "message": done_message}
                        if not has_native_structured_analysis_payload:
                            analysis_payload = build_analysis_report_projection(
                                kernel_context=kernel_context,
                                mode=mode,
                                user_message=request.message,
                                assistant_message=done_message or text_accumulator.final_message(),
                                force=has_native_analysis_payload,
                            )
                            if analysis_payload:
                                event = with_analysis_payload(event, analysis_payload)
                                projection_events.append(("analysis_payload", analysis_payload))
                    if event_type in ("done", "complete"):
                        for projected_type, projected_payload in projection_events:
                            event_key = f"{projected_type}:{projection_key(projected_payload)}"
                            if event_key in emitted_projection_keys:
                                continue
                            emitted_projection_keys.add(event_key)
                            yield f"event: {projected_type}\n"
                            yield f"data: {json.dumps(projected_payload, ensure_ascii=False)}\n\n"
                        projection_events = []
                    yield f"event: {event_type}\n"
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    if pending_contract and event_type not in ("next_actions", "early_patch", "final_patch"):
                        yield "event: next_actions\n"
                        yield f"data: {json.dumps(pending_contract, ensure_ascii=False)}\n\n"
                    for projected_type, projected_payload in projection_events:
                        event_key = f"{projected_type}:{projection_key(projected_payload)}"
                        if event_key in emitted_projection_keys:
                            continue
                        emitted_projection_keys.add(event_key)
                        yield f"event: {projected_type}\n"
                        yield f"data: {json.dumps(projected_payload, ensure_ascii=False)}\n\n"
                final_message = normalize_assistant_display_text(done_message or text_accumulator.final_message())
                if not _is_non_empty_text(final_message) and _should_suppress_assistant_message(latest_pending_contract):
                    pending_question = _as_object((latest_pending_contract or {}).get("question"))
                    current_question = _as_object((latest_pending_contract or {}).get("current_question"))
                    final_message = _to_text((pending_question or {}).get("question_text"))
                    if not final_message:
                        final_message = _to_text((current_question or {}).get("question_text"))
                    final_message = normalize_assistant_display_text(final_message)
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
