"""Session message window persistence queries."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from flare_kernel.session_message_window import (
    clamp_message_window_limit,
    decode_message_cursor,
    encode_message_cursor,
)

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.conversation_store import ConversationStore, MessageRecord
from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config


@dataclass(frozen=True)
class MessageWindowResult:
    messages: list[MessageRecord]
    window: dict[str, object]


def _cursor_from_message(message: MessageRecord | None) -> str:
    if message is None:
        return ""
    return encode_message_cursor({
        "created_at": message.created_at,
        "message_id": message.message_id,
    })


def _full_window(messages: list[MessageRecord]) -> MessageWindowResult:
    return MessageWindowResult(
        messages=messages,
        window={
            "mode": "full",
            "limit": None,
            "has_older": False,
            "next_before": "",
        },
    )


class MessageWindowStore:
    def __init__(self, db_path: str, db_url: str = "", initial_limit: int = 6):
        self._lock = asyncio.Lock()
        self._initial_limit = max(1, clamp_message_window_limit(initial_limit))
        config = resolve_db_config(storage_db_url=db_url, storage_db_path=db_path)
        self._runtime = SQLRuntime(config)

    def _list_all_messages(self, session_id: str) -> list[MessageRecord]:
        rows = self._runtime.fetchall(
            """
            SELECT * FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC, message_id ASC
            """,
            (session_id,),
        )
        return [ConversationStore._row_to_message(row) for row in rows]

    def _list_descending_window(
        self,
        session_id: str,
        *,
        before_created_at: str = "",
        before_message_id: str = "",
        limit: int,
    ) -> list[MessageRecord]:
        cursor_filter = ""
        params: list[object] = [session_id]
        if before_created_at and before_message_id:
            cursor_filter = " AND (created_at < ? OR (created_at = ? AND message_id < ?))"
            params.extend([before_created_at, before_created_at, before_message_id])
        params.append(limit)
        rows = self._runtime.fetchall(
            f"""
            SELECT * FROM messages
            WHERE session_id = ?{cursor_filter}
            ORDER BY created_at DESC, message_id DESC
            LIMIT ?
            """,
            params,
        )
        return [ConversationStore._row_to_message(row) for row in rows]

    async def list_message_window(
        self,
        *,
        session_id: str,
        limit: int = 0,
        before: str = "",
    ) -> MessageWindowResult:
        async with self._lock:
            resolved_session_id = str(session_id or "").strip()
            resolved_before = str(before or "").strip()
            if not resolved_session_id:
                return _full_window([])
            if not limit and not resolved_before:
                return _full_window(self._list_all_messages(resolved_session_id))

            requested_limit = clamp_message_window_limit(limit)
            cursor = decode_message_cursor(resolved_before)
            bounded_limit = requested_limit if cursor else min(requested_limit, self._initial_limit)
            rows_descending = self._list_descending_window(
                resolved_session_id,
                before_created_at=cursor.get("created_at", ""),
                before_message_id=cursor.get("message_id", ""),
                limit=bounded_limit + 1,
            )
            has_older = len(rows_descending) > bounded_limit
            messages = list(reversed(rows_descending[:bounded_limit]))
            return MessageWindowResult(
                messages=messages,
                window={
                    "mode": "before" if cursor else "latest",
                    "limit": bounded_limit,
                    "has_older": has_older,
                    "next_before": _cursor_from_message(messages[0] if has_older and messages else None),
                },
            )


_store: MessageWindowStore | None = None
_store_db_key: tuple[str, str, int] | None = None


def get_message_window_store() -> MessageWindowStore:
    global _store, _store_db_key
    settings = get_settings()
    key = (settings.storage_db_path, settings.storage_db_url, settings.message_window_initial_limit)
    if _store is None or _store_db_key != key:
        _store = MessageWindowStore(
            db_path=settings.storage_db_path,
            db_url=settings.storage_db_url,
            initial_limit=settings.message_window_initial_limit,
        )
        _store_db_key = key
    return _store
