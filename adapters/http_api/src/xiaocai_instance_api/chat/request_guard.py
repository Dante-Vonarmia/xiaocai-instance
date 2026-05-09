"""Chat request guard for xiaocai-owned product boundaries.

This module stays pure: it does not call providers, repositories, or FLARE.
The API layer uses it before handing a user request to the kernel.
"""

from __future__ import annotations

from dataclasses import dataclass


REFUSAL_MESSAGE = (
    "这类信息属于系统内部配置或受权限控制的数据，不能通过普通对话直接查询或披露。"
    "你可以在当前账号权限范围内查看自己的会话记录；如需数据库结构、全量历史或运维排查，"
    "请通过管理员后台或受控运维流程处理。我可以继续协助你梳理采购需求、分析已授权资料，"
    "或设计一个安全的查询/脱敏导出流程。"
)


@dataclass(frozen=True)
class RequestGuardResult:
    allowed: bool
    reason: str = ""
    message: str = ""

    def to_metadata(self) -> dict[str, str | bool]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
        }


def _normalize_text(value: str) -> str:
    return value.strip().lower()


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _matches_prompt_query(text: str) -> bool:
    prompt_terms = ("system prompt", "系统 prompt", "系统提示词", "内部提示词", "prompt")
    reveal_terms = ("告诉我", "展示", "泄露", "查看", "有哪些", "show", "reveal", "dump", "list")
    return _contains_any(text, prompt_terms) and _contains_any(text, reveal_terms)


def _matches_tooling_query(text: str) -> bool:
    tooling_terms = ("mcp", "tool", "tools", "工具", "connector", "连接器")
    listing_terms = ("有哪些", "列表", "清单", "可用", "全部", "所有", "show", "list", "available")
    return _contains_any(text, tooling_terms) and _contains_any(text, listing_terms)


def _matches_database_query(text: str) -> bool:
    database_terms = ("数据库", "database", "db", "schema", "表结构", "连接信息", "dsn")
    internal_terms = ("设计", "结构", "连接", "当前", "所有", "全部", "全量", "信息", "元数据")
    return _contains_any(text, database_terms) and _contains_any(text, internal_terms)


def _matches_conversation_history_query(text: str) -> bool:
    history_terms = ("会话历史", "聊天历史", "conversation history", "sessions", "messages")
    scope_terms = ("所有", "全部", "全量", "当前采购助手", "其他用户", "所有用户", "全部用户")
    return _contains_any(text, history_terms) and _contains_any(text, scope_terms)


def _matches_other_user_data_query(text: str) -> bool:
    user_terms = ("其他用户", "所有用户", "全部用户", "别人的", "他人的")
    data_terms = ("数据", "会话", "消息", "历史", "记录", "user data")
    return _contains_any(text, user_terms) and _contains_any(text, data_terms)


def evaluate_request_guard(message: str) -> RequestGuardResult:
    """Return a product-boundary decision before kernel/provider execution."""
    text = _normalize_text(message)
    if not text:
        return RequestGuardResult(allowed=True)

    checks = (
        ("internal_prompt", _matches_prompt_query),
        ("tooling_inventory", _matches_tooling_query),
        ("database_metadata", _matches_database_query),
        ("conversation_history", _matches_conversation_history_query),
        ("other_user_data", _matches_other_user_data_query),
    )
    for reason, matcher in checks:
        if matcher(text):
            return RequestGuardResult(
                allowed=False,
                reason=reason,
                message=REFUSAL_MESSAGE,
            )
    return RequestGuardResult(allowed=True)
