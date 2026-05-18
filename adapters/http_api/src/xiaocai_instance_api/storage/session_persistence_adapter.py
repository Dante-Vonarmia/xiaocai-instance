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


_MESSAGE_ARTIFACT_COLUMN_DEFINITIONS = {
    "run_id": "TEXT NOT NULL DEFAULT ''",
    "canvas_state": "TEXT NULL",
    "analysis_payload": "TEXT NULL",
    "provider_trace": "TEXT NULL",
    "context_authority": "TEXT NULL",
    "plan_payload": "TEXT NULL",
}


def _ensure_message_artifact_columns(runtime: SQLRuntime) -> None:
    """Keep direct FLARE repository writes compatible with older message tables."""
    if runtime.backend == "postgres":
        rows = runtime.fetchall(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = 'messages'
            """
        )
        names = {str(row["column_name"]) for row in rows}
    else:
        rows = runtime.fetchall("PRAGMA table_info(messages)")
        names = {str(row["name"]) for row in rows}
    if not names:
        return
    for name, definition in _MESSAGE_ARTIFACT_COLUMN_DEFINITIONS.items():
        if name not in names:
            runtime.execute(f"ALTER TABLE messages ADD COLUMN {name} {definition}")
    runtime.commit()


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
    payload["run_id"] = str(payload.get("run_id") or "")
    payload["attachments"] = _json_loads(payload.get("attachments"), [])
    payload["context_refs"] = _json_loads(payload.get("context_refs"), [])
    payload["knowledge_refs"] = _json_loads(payload.get("knowledge_refs"), [])
    payload["agent_status"] = _json_loads(payload.get("agent_status"), None)
    payload["thinking_trace"] = str(payload.get("thinking_trace") or "")
    payload["execution_trace"] = _json_loads(payload.get("execution_trace"), None)
    payload["knowledge_search"] = _json_loads(payload.get("knowledge_search"), None)
    payload["sourcing_candidates"] = _json_loads(payload.get("sourcing_candidates"), None)
    payload["knowledge_citation"] = _json_loads(payload.get("knowledge_citation"), None)
    payload["canvas_state"] = _json_loads(payload.get("canvas_state"), None)
    payload["analysis_payload"] = _json_loads(payload.get("analysis_payload"), None)
    payload["context_usage"] = _json_loads(payload.get("context_usage"), None)
    payload["provider_trace"] = _json_loads(payload.get("provider_trace"), None)
    payload["context_authority"] = _json_loads(payload.get("context_authority"), None)
    payload["plan_payload"] = _json_loads(payload.get("plan_payload"), None)
    return SessionMessageRecord.model_validate(payload).model_dump(mode="python")


class XiaocaiSessionPersistenceAdapter(SessionRepository):
    """Persist FLARE session/message records into xiaocai storage tables."""

    def __init__(self, *, db_path: str, db_url: str = "") -> None:
        run_storage_migrations(db_path=db_path, db_url=db_url)
        config = resolve_db_config(storage_db_url=db_url, storage_db_path=db_path)
        self._runtime = SQLRuntime(config)
        _ensure_message_artifact_columns(self._runtime)
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
                    message_id, session_id, run_id, role, content, attachments, context_refs, knowledge_refs,
                    agent_status, thinking_trace, execution_trace, knowledge_search,
                    sourcing_candidates, knowledge_citation, canvas_state, analysis_payload,
                    context_usage, provider_trace, context_authority, plan_payload, created_at
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
                        message_id, session_id, user_id, sender_user_id, run_id, role, content, created_at,
                        attachments, context_refs, knowledge_refs, agent_status, thinking_trace,
                        execution_trace, knowledge_search, sourcing_candidates, knowledge_citation,
                        canvas_state, analysis_payload, context_usage, provider_trace, context_authority, plan_payload
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        normalized["message_id"],
                        normalized["session_id"],
                        session_user_id,
                        session_user_id,
                        normalized["run_id"],
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
                        _json_dumps(normalized["canvas_state"]) if normalized["canvas_state"] is not None else None,
                        _json_dumps(normalized["analysis_payload"]) if normalized["analysis_payload"] is not None else None,
                        _json_dumps(normalized["context_usage"]) if normalized["context_usage"] is not None else None,
                        _json_dumps(normalized["provider_trace"]) if normalized["provider_trace"] is not None else None,
                        _json_dumps(normalized["context_authority"]) if normalized["context_authority"] is not None else None,
                        _json_dumps(normalized["plan_payload"]) if normalized["plan_payload"] is not None else None,
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
