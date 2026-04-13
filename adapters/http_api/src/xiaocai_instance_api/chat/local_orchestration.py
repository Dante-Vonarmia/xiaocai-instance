"""
xiaocai 本地会话编排入口。

保留该入口文件以兼容已有 import 路径，具体实现拆分在 chat/orchestration/ 目录。
"""

from xiaocai_instance_api.chat.orchestration import (
    LocalOrchestrationResult,
    build_local_orchestration_response,
)

__all__ = ["LocalOrchestrationResult", "build_local_orchestration_response"]
