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


class KernelClient:
    """FLARE Kernel 客户端"""

    def __init__(self):
        self.settings = get_settings()
        self.kernel_base_url = self.settings.kernel_base_url
        self._runtime_mode = (self.settings.kernel_runtime_mode or "http").strip().lower()
        if self._runtime_mode and self._runtime_mode != "http":
            raise ValueError(
                f"Unsupported KERNEL_RUNTIME_MODE={self._runtime_mode}. Only 'http' is supported."
            )

    def _build_kernel_url(self, path: str) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        return f"{self.kernel_base_url}{normalized_path}"

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
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._build_kernel_url(self.settings.kernel_run_path),
                json={
                    "user_id": user_id,
                    "message": message,
                    "session_id": session_id,
                    "context": context or {},
                },
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()
            if isinstance(result, dict):
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

                normalized = dict(result)
                normalized["message"] = result.get("message") or result.get("reply", "")
                normalized["cards"] = result.get("cards", [])
                normalized["session_id"] = result.get("session_id", session_id)
                normalized["metadata"] = metadata
                return normalized
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
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                self._build_kernel_url(self.settings.kernel_stream_path),
                json={
                    "user_id": user_id,
                    "message": message,
                    "session_id": session_id,
                    "context": context or {},
                },
                timeout=60.0,
            ) as response:
                response.raise_for_status()
                event_name: str | None = None
                data_lines: list[str] = []
                async for line in response.aiter_lines():
                    if line == "":
                        if event_name is not None or data_lines:
                            yield self._parse_sse_event(event_name, data_lines)
                            event_name = None
                            data_lines = []
                        continue
                    if line.startswith("event:"):
                        event_name = line[len("event:"):].strip() or None
                        continue
                    if line.startswith("data:"):
                        data_lines.append(line[len("data:"):].lstrip())
                        continue
                    if line.startswith(":"):
                        continue

                if event_name is not None or data_lines:
                    yield self._parse_sse_event(event_name, data_lines)


@lru_cache()
def get_kernel_client() -> KernelClient:
    """获取 kernel 客户端单例"""
    return KernelClient()
