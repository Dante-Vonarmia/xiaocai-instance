"""
对话接口契约

定义 POST /chat/run 和 POST /chat/stream 的请求/响应结构
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """对话消息"""
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")


class ChatRunRequest(BaseModel):
    """
    同步对话请求

    用途: 发送消息，等待完整响应
    """
    message: str = Field(..., description="用户消息")
    session_id: str = Field(..., description="会话 ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")


class ChatRunResponse(BaseModel):
    """同步对话响应"""
    message: str = Field(..., description="助手回复")
    session_id: str = Field(..., description="会话 ID")
    cards: List[Dict[str, Any]] = Field(default_factory=list, description="UI 卡片")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class ChatStreamRequest(BaseModel):
    """
    流式对话请求

    用途: 发送消息，接收 SSE 流式响应
    """
    message: str = Field(..., description="用户消息")
    session_id: str = Field(..., description="会话 ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")


# SSE 响应是流式的，不需要单独的响应模型
# 每条 SSE 消息格式:
# data: {"type": "chunk", "content": "...", "delta": "..."}
# data: {"type": "card", "card_data": {...}}
# data: {"type": "done", "final_message": "..."}
