"""FLARE session persistence adapter backed by xiaocai storage."""

from __future__ import annotations

import json
import threading
from typing import Any, Protocol

from flare_kernel.contracts.context import ContextContract, create_empty_context
from flare_kernel.contracts.session_contract import SessionMessageRecord, SessionRecord

from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config
from xiaocai_instance_api.storage.migrations import run_storage_migrations


class SessionRepository(Protocol):
    def create_session_record(self, record: dict[str, Any]) -> dict[str, Any]: ...

    def load_session_record(self, session_id: str) -> dict[str, Any] | None: ...

    def save_session_record(self, record: dict[str, Any]) -> dict[str, Any]: ...

    def list_session_records(self) -> list[dict[str, Any]]: ...

    def list_session_messages(self, session_id: str) -> list[dict[str, Any]]: ...

    def append_session_messages(self, session_id: str, messages: list[dict[str, Any]]) -> list[dict[str, Any]]: ...

    def reset(self) -> None: ...


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _json_loads(raw: Any, default: Any) -> Any:
    if raw in (None, ""):
        return default
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(str(raw))
    except json.JSONDecodeError:
        return default


def _normalize_context_payload(value: Any) -> dict[str, Any]:
    payload = value if isinstance(value, dict) else _json_loads(value, {})
    return ContextContract.model_validate(payload or create_empty_context().model_dump()).model_dump(mode="python")


def _normalize_session_record(record: dict[str, Any]) -> dict[str, Any]:
    payload = dict(record)
    raw_user_id = payload.get("user_id")
    payload["user_id"] = raw_user_id if raw_user_id not in ("", None) else None
    payload["context"] = _normalize_context_payload(payload.get("context"))
    return SessionRecord.model_validate(payload).model_dump(mode="python")


def _normalize_message_record(record: dict[str, Any]) -> dict[str, Any]:
    payload = dict(record)
    payload["attachments"] = _json_loads(payload.get("attachments"), [])
    payload["context_refs"] = _json_loads(payload.get("context_refs"), [])
    payload["knowledge_refs"] = _json_loads(payload.get("knowledge_refs"), [])
    payload["agent_status"] = _json_loads(payload.get("agent_status"), None)
    payload["thinking_trace"] = str(payload.get("thinking_trace") or "")
    payload["execution_trace"] = _json_loads(payload.get("execution_trace"), None)
    payload["knowledge_search"] = _json_loads(payload.get("knowledge_search"), None)
    payload["sourcing_candidates"] = _json_loads(payload.get("sourcing_candidates"), None)
    payload["knowledge_citation"] = _json_loads(payload.get("knowledge_citation"), None)
    payload["context_usage"] = _json_loads(payload.get("context_usage"), None)
    return SessionMessageRecord.model_validate(payload).model_dump(mode="python")


class XiaocaiSessionPersistenceAdapter(SessionRepository):
    """Persist FLARE session/message records into xiaocai storage tables."""

    def __init__(self, *, db_path: str, db_url: str = "") -> None:
        run_storage_migrations(db_path=db_path, db_url=db_url)
        config = resolve_db_config(storage_db_url=db_url, storage_db_path=db_path)
        self._runtime = SQLRuntime(config)
        self._lock = threading.Lock()

    def create_session_record(self, record: dict[str, Any]) -> dict[str, Any]:
        return self._upsert_session_record(record)

    def load_session_record(self, session_id: str) -> dict[str, Any] | None:
        resolved = str(session_id or "").strip()
        if not resolved:
            return None
        with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT session_id, project_id, title, preview, title_source, status, user_id, function_type, context, created_at, updated_at
                FROM sessions
                WHERE session_id = ?
                LIMIT 1
                """,
                (resolved,),
            )
            return _normalize_session_record(row) if row else None

    def save_session_record(self, record: dict[str, Any]) -> dict[str, Any]:
        return self._upsert_session_record(record)

    def list_session_records(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._runtime.fetchall(
                """
                SELECT session_id, project_id, title, preview, title_source, status, user_id, function_type, context, created_at, updated_at
                FROM sessions
                ORDER BY updated_at DESC
                """
            )
            return [_normalize_session_record(row) for row in rows]

    def list_session_messages(self, session_id: str) -> list[dict[str, Any]]:
        resolved = str(session_id or "").strip()
        if not resolved:
            return []
        with self._lock:
            rows = self._runtime.fetchall(
                """
                SELECT
                    message_id, session_id, role, content, attachments, context_refs, knowledge_refs,
                    agent_status, thinking_trace, execution_trace, knowledge_search,
                    sourcing_candidates, knowledge_citation, context_usage, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (resolved,),
            )
            return [_normalize_message_record(row) for row in rows]

    def append_session_messages(self, session_id: str, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        resolved_session_id = str(session_id or "").strip()
        if not resolved_session_id:
            return []
        with self._lock:
            session_row = self._runtime.fetchone(
                "SELECT user_id FROM sessions WHERE session_id = ? LIMIT 1",
                (resolved_session_id,),
            )
            session_user_id = str((session_row or {}).get("user_id") or "")
            for message in messages:
                normalized = _normalize_message_record(
                    {
                        "session_id": resolved_session_id,
                        "attachments": [],
                        "context_refs": [],
                        "knowledge_refs": [],
                        "thinking_trace": "",
                        **dict(message),
                    }
                )
                self._runtime.execute(
                    """
                    INSERT INTO messages (
                        message_id, session_id, user_id, sender_user_id, role, content, created_at,
                        attachments, context_refs, knowledge_refs, agent_status, thinking_trace,
                        execution_trace, knowledge_search, sourcing_candidates, knowledge_citation, context_usage
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        normalized["message_id"],
                        normalized["session_id"],
                        session_user_id,
                        session_user_id,
                        normalized["role"],
                        normalized["content"],
                        normalized["created_at"],
                        _json_dumps(normalized["attachments"]),
                        _json_dumps(normalized["context_refs"]),
                        _json_dumps(normalized["knowledge_refs"]),
                        _json_dumps(normalized["agent_status"]) if normalized["agent_status"] is not None else None,
                        normalized["thinking_trace"],
                        _json_dumps(normalized["execution_trace"]) if normalized["execution_trace"] is not None else None,
                        _json_dumps(normalized["knowledge_search"]) if normalized["knowledge_search"] is not None else None,
                        _json_dumps(normalized["sourcing_candidates"]) if normalized["sourcing_candidates"] is not None else None,
                        _json_dumps(normalized["knowledge_citation"]) if normalized["knowledge_citation"] is not None else None,
                        _json_dumps(normalized["context_usage"]) if normalized["context_usage"] is not None else None,
                    ),
                )
            self._runtime.commit()
        return self.list_session_messages(resolved_session_id)

    def reset(self) -> None:
        with self._lock:
            self._runtime.execute("DELETE FROM messages")
            self._runtime.execute("DELETE FROM sessions")
            self._runtime.commit()

    def _upsert_session_record(self, record: dict[str, Any]) -> dict[str, Any]:
        normalized = _normalize_session_record(record)
        user_id = str(normalized.get("user_id") or "")
        with self._lock:
            self._runtime.execute(
                """
                INSERT INTO sessions (
                    session_id, function_type, project_id, user_id, owner_user_id, visibility, mode,
                    title, status, preview, title_source, context, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'private', NULL, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    function_type = excluded.function_type,
                    project_id = excluded.project_id,
                    user_id = excluded.user_id,
                    owner_user_id = excluded.owner_user_id,
                    title = excluded.title,
                    status = excluded.status,
                    preview = excluded.preview,
                    title_source = excluded.title_source,
                    context = excluded.context,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                (
                    normalized["session_id"],
                    normalized.get("function_type"),
                    normalized.get("project_id"),
                    user_id,
                    user_id,
                    normalized["title"],
                    normalized["status"],
                    normalized["preview"],
                    normalized["title_source"],
                    _json_dumps(normalized["context"]),
                    normalized["created_at"],
                    normalized["updated_at"],
                ),
            )
            self._runtime.commit()
        saved = self.load_session_record(normalized["session_id"])
        if saved is None:
            raise RuntimeError("Failed to reload persisted session record")
        return saved


__all__ = ["XiaocaiSessionPersistenceAdapter"]
