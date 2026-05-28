"""
FLARE Kernel 客户端

职责:
1. 调用 FLARE kernel 的 chat 接口
2. 处理同步和流式两种模式
3. 转换请求/响应格式

重要:
- FLARE kernel 是独立服务，提供 chat 核心能力
- xiaocai 不实现 chat 逻辑，只是调用 kernel
- kernel 地址从配置读取
"""

import json
import httpx
from typing import Dict, Any, AsyncGenerator
from functools import lru_cache
from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.chat.kernel_request_body import build_kernel_request_body
from xiaocai_instance_api.chat.replay.hooks import (
    append_kernel_capture,
    begin_kernel_capture,
    finish_kernel_capture,
)


class KernelStreamConflictError(RuntimeError):
    """Raised when FLARE kernel reports an active stream for the same session."""

class KernelClient:
    """FLARE Kernel 客户端"""

    def __init__(self):
        self.settings = get_settings()
        self.kernel_base_url = self.settings.kernel_base_url
        self._runtime_mode = (self.settings.kernel_runtime_mode or "http").strip().lower()
        if self._runtime_mode != "http":
            raise ValueError(
                f"Unsupported KERNEL_RUNTIME_MODE={self._runtime_mode}. Supported: http."
            )

    def _build_kernel_url(self, path: str) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        return f"{self.kernel_base_url}{normalized_path}"

    @staticmethod
    def _build_request_body(
        user_id: str,
        message: str,
        session_id: str,
        context: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        settings = get_settings()
        return build_kernel_request_body(
            user_id=user_id,
            message=message,
            session_id=session_id,
            context=context,
            default_instance_id=settings.flare_instance_id,
            default_domain_pack_domain=settings.flare_domain_pack_default_domain,
            default_domain_pack_version=settings.flare_domain_pack_version,
        )

    @staticmethod
    def _parse_sse_event(event_name: str | None, data_lines: list[str]) -> Dict[str, Any]:
        raw_data = "\n".join(data_lines).strip()
        payload: Any = raw_data
        if raw_data:
            try:
                payload = json.loads(raw_data)
            except json.JSONDecodeError:
                payload = raw_data

        if isinstance(payload, dict):
            event_type = event_name or payload.get("type") or "message"
            event = dict(payload)
            event["type"] = event_type
            event.setdefault("payload", payload)
            if "content" not in event and isinstance(event.get("message"), str):
                event["content"] = event["message"]
            return event

        event_type = event_name or "message"
        return {"type": event_type, "payload": payload, "content": payload}

    async def chat_run(
        self,
        user_id: str,
        message: str,
        session_id: str,
        context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        同步对话 - 调用 FLARE kernel

        Args:
            user_id: 用户 ID
            message: 用户消息
            session_id: 会话 ID
            context: 上下文信息（可选）

        Returns:
            Dict: kernel 返回的响应，包含 message, cards 等

        业务说明:
            - 调用 kernel 的 /chat/run 接口
            - kernel 会调用 7 Engine 处理对话
            - 返回完整的响应（文本 + UI cards）

        参考: docs/discussions/phase-1-procurement-product-logic.md
              需求梳理、智能寻源等业务逻辑在 kernel 处理
        """
        kernel_url = self._build_kernel_url(self.settings.kernel_run_path)
        request_body = self._build_request_body(
            user_id=user_id,
            message=message,
            session_id=session_id,
            context=context,
        )
        replay = begin_kernel_capture(
            kind="run",
            user_id=user_id,
            session_id=session_id,
            kernel_url=kernel_url,
            request_body=request_body,
        )
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(kernel_url, json=request_body, timeout=30.0)
                response.raise_for_status()
                result = response.json()
        except Exception as exc:
            append_kernel_capture(replay, "kernel.error", {"message": str(exc)})
            finish_kernel_capture(replay, status="error", error=str(exc))
            raise
        append_kernel_capture(replay, "kernel.response.raw", result)
        if isinstance(result, dict):
            result_payload = result.get("result", {})
            if not isinstance(result_payload, dict):
                result_payload = {}

            metadata = result.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            # FLARE recovery protocol compatibility:
            # keep newly added top-level fields in metadata for instance-side orchestration.
            if "confusion_detector" in result:
                metadata["confusion_detector"] = result.get("confusion_detector")
            if "recovery_plan" in result:
                metadata["recovery_plan"] = result.get("recovery_plan")
            observability = result.get("observability")
            if isinstance(observability, dict) and "recovery" in observability:
                metadata["observability"] = dict(metadata.get("observability", {})) if isinstance(metadata.get("observability"), dict) else {}
                metadata["observability"]["recovery"] = observability.get("recovery")
            if isinstance(result.get("events"), list):
                metadata["events"] = result.get("events")
            if isinstance(result.get("state"), str):
                metadata["state"] = result.get("state")

            next_actions = result.get("next_actions")
            if not isinstance(next_actions, list):
                next_actions = result_payload.get("next_actions")
            if isinstance(next_actions, list) and next_actions:
                metadata["next_actions"] = next_actions

            cards = result.get("cards")
            if not isinstance(cards, list):
                cards = result_payload.get("cards", [])
            if not isinstance(cards, list):
                cards = []

            if not cards and isinstance(next_actions, list) and next_actions:
                cards = [
                    {
                        "type": "next_actions",
                        "actions": next_actions,
                        "next_actions": next_actions,
                        "render_hint": "next_actions",
                    }
                ]

            normalized = dict(result)
            normalized["message"] = (
                result.get("message")
                or result.get("reply")
                or result_payload.get("message", "")
            )
            normalized["cards"] = cards
            normalized["session_id"] = (
                result.get("session_id")
                or result_payload.get("session_id")
                or session_id
            )
            normalized["metadata"] = metadata
            append_kernel_capture(replay, "kernel.response.normalized", normalized)
            finish_kernel_capture(replay, status="ok")
            return normalized
        finish_kernel_capture(replay, status="error", error="Kernel response must be a JSON object")
        raise ValueError("Kernel response must be a JSON object")

    async def chat_stream(
        self,
        user_id: str,
        message: str,
        session_id: str,
        context: Dict[str, Any] | None = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式对话 - 调用 FLARE kernel 的 SSE 接口

        Args:
            user_id: 用户 ID
            message: 用户消息
            session_id: 会话 ID
            context: 上下文信息（可选）

        Yields:
            Dict: 流式事件，包含 type, data 等字段

        业务说明:
            - 调用 kernel 的 /chat/stream 接口
            - 使用 Server-Sent Events (SSE) 协议
            - 逐步返回 token、卡片等内容
            - 适用于需要实时反馈的场景

        事件类型:
            - token: 文本 token
            - card: UI 卡片
            - done: 对话结束
            - error: 错误
        """
        event_name: str | None = None
        data_lines: list[str] = []
        line_buffer = ""
        kernel_url = self._build_kernel_url(self.settings.kernel_stream_path)
        request_body = self._build_request_body(
            user_id=user_id,
            message=message,
            session_id=session_id,
            context=context,
        )
        replay = begin_kernel_capture(
            kind="stream",
            user_id=user_id,
            session_id=session_id,
            kernel_url=kernel_url,
            request_body=request_body,
        )

        async def _consume_line(line: str) -> AsyncGenerator[Dict[str, Any], None]:
            nonlocal event_name, data_lines
            if line == "":
                if event_name is not None or data_lines:
                    yield self._parse_sse_event(event_name, data_lines)
                    event_name = None
                    data_lines = []
                return
            if line.startswith("event:"):
                event_name = line[len("event:"):].strip() or None
                return
            if line.startswith("data:"):
                data_lines.append(line[len("data:"):].lstrip())
                return
            if line.startswith(":"):
                return

        async def _parse_sse_chunks(chunks: AsyncGenerator[str, None]) -> AsyncGenerator[Dict[str, Any], None]:
            nonlocal line_buffer
            async for chunk in chunks:
                if not chunk:
                    continue
                line_buffer += chunk
                while "\n" in line_buffer:
                    line, line_buffer = line_buffer.split("\n", 1)
                    normalized_line = line.rstrip("\r")
                    async for parsed in _consume_line(normalized_line):
                        yield parsed
            if line_buffer:
                async for parsed in _consume_line(line_buffer.rstrip("\r")):
                    yield parsed
            if event_name is not None or data_lines:
                yield self._parse_sse_event(event_name, data_lines)

        async def _http_chunks() -> AsyncGenerator[str, None]:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    kernel_url,
                    json=request_body,
                    timeout=httpx.Timeout(connect=10.0, read=None, write=60.0, pool=60.0),
                ) as response:
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code != 409:
                            raise
                        raise KernelStreamConflictError("kernel stream conflict") from exc
                    async for line in response.aiter_lines():
                        yield f"{line}\n"

        try:
            async for parsed_event in _parse_sse_chunks(_http_chunks()):
                append_kernel_capture(replay, "kernel.stream.event", parsed_event)
                yield parsed_event
        except Exception as exc:
            append_kernel_capture(replay, "kernel.error", {"message": str(exc)})
            finish_kernel_capture(replay, status="error", error=str(exc))
            raise
        finish_kernel_capture(replay, status="ok")


@lru_cache()
def get_kernel_client() -> KernelClient:
    """获取 kernel 客户端单例"""
    return KernelClient()
