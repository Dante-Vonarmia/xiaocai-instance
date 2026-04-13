"""
会话存储 - Conversation/Message 管理
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List
import asyncio
import uuid

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _session_access_clause(alias: str = "s") -> str:
    return f"""
        (
            {alias}.owner_user_id = ?
            OR (
                {alias}.visibility = 'project_shared'
                AND {alias}.project_id IS NOT NULL
                AND EXISTS (
                    SELECT 1 FROM project_members pm
                    WHERE pm.project_id = {alias}.project_id
                      AND pm.user_id = ?
                      AND pm.status = 'active'
                )
            )
        )
    """


def _session_write_clause(alias: str = "s") -> str:
    return f"""
        (
            {alias}.owner_user_id = ?
            OR (
                {alias}.visibility = 'project_shared'
                AND {alias}.project_id IS NOT NULL
                AND EXISTS (
                    SELECT 1 FROM project_members pm
                    WHERE pm.project_id = {alias}.project_id
                      AND pm.user_id = ?
                      AND pm.status = 'active'
                      AND pm.role IN ('owner', 'editor')
                )
            )
        )
    """


@dataclass
class SessionRecord:
    session_id: str
    function_type: str
    project_id: str | None
    user_id: str
    owner_user_id: str
    visibility: str
    mode: str | None
    title: str
    status: str
    preview: str
    created_at: str
    updated_at: str


@dataclass
class MessageRecord:
    message_id: str
    session_id: str
    sender_user_id: str
    role: str
    content: str
    created_at: str


class ConversationStore:
    def __init__(self, db_path: str, db_url: str = ""):
        config = resolve_db_config(storage_db_url=db_url, storage_db_path=db_path)
        self._db_path = config.dsn
        self._runtime = SQLRuntime(config)
        self._lock = asyncio.Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        self._runtime.execute(
            """
            CREATE TABLE IF NOT EXISTS project_members (
                project_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'owner',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (project_id, user_id)
            )
            """
        )
        self._runtime.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                function_type TEXT NOT NULL,
                project_id TEXT NULL,
                user_id TEXT NOT NULL,
                owner_user_id TEXT NOT NULL,
                visibility TEXT NOT NULL DEFAULT 'private',
                mode TEXT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                preview TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._runtime.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                sender_user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._runtime.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sessions_user_updated
            ON sessions (user_id, updated_at DESC)
            """
        )
        self._runtime.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sessions_owner_updated
            ON sessions (owner_user_id, updated_at DESC)
            """
        )
        self._runtime.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sessions_project_owner_updated
            ON sessions (project_id, owner_user_id, updated_at DESC)
            """
        )
        self._runtime.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sessions_project_visibility_updated
            ON sessions (project_id, visibility, updated_at DESC)
            """
        )
        self._runtime.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_messages_session_created
            ON messages (session_id, created_at ASC)
            """
        )
        self._runtime.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_messages_sender_created
            ON messages (sender_user_id, created_at ASC)
            """
        )
        self._sync_legacy_columns()
        self._runtime.commit()

    def _sync_legacy_columns(self) -> None:
        if self._runtime.backend == "sqlite":
            session_columns = self._runtime.fetchall("PRAGMA table_info(sessions)")
            session_names = {str(row["name"]) for row in session_columns}
            if "mode" not in session_names:
                self._runtime.execute("ALTER TABLE sessions ADD COLUMN mode TEXT NULL")
            if "owner_user_id" not in session_names:
                self._runtime.execute("ALTER TABLE sessions ADD COLUMN owner_user_id TEXT NULL")
            if "visibility" not in session_names:
                self._runtime.execute("ALTER TABLE sessions ADD COLUMN visibility TEXT NOT NULL DEFAULT 'private'")
            self._runtime.execute(
                """
                UPDATE sessions
                SET owner_user_id = COALESCE(owner_user_id, user_id)
                WHERE owner_user_id IS NULL OR owner_user_id = ''
                """
            )

            message_columns = self._runtime.fetchall("PRAGMA table_info(messages)")
            message_names = {str(row["name"]) for row in message_columns}
            if "sender_user_id" not in message_names:
                self._runtime.execute("ALTER TABLE messages ADD COLUMN sender_user_id TEXT NULL")
            self._runtime.execute(
                """
                UPDATE messages
                SET sender_user_id = COALESCE(sender_user_id, user_id)
                WHERE sender_user_id IS NULL OR sender_user_id = ''
                """
            )
            return

        session_columns = self._runtime.fetchall(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = 'sessions'
            """
        )
        session_names = {str(row["column_name"]) for row in session_columns}
        if "mode" not in session_names:
            self._runtime.execute("ALTER TABLE sessions ADD COLUMN mode TEXT NULL")
        if "owner_user_id" not in session_names:
            self._runtime.execute("ALTER TABLE sessions ADD COLUMN owner_user_id TEXT NULL")
        if "visibility" not in session_names:
            self._runtime.execute("ALTER TABLE sessions ADD COLUMN visibility TEXT NOT NULL DEFAULT 'private'")
        self._runtime.execute(
            """
            UPDATE sessions
            SET owner_user_id = COALESCE(owner_user_id, user_id)
            WHERE owner_user_id IS NULL OR owner_user_id = ''
            """
        )

        message_columns = self._runtime.fetchall(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = 'messages'
            """
        )
        message_names = {str(row["column_name"]) for row in message_columns}
        if "sender_user_id" not in message_names:
            self._runtime.execute("ALTER TABLE messages ADD COLUMN sender_user_id TEXT NULL")
        self._runtime.execute(
            """
            UPDATE messages
            SET sender_user_id = COALESCE(sender_user_id, user_id)
            WHERE sender_user_id IS NULL OR sender_user_id = ''
            """
        )

    @staticmethod
    def _row_to_session(row: dict) -> SessionRecord:
        owner_user_id = str(row.get("owner_user_id") or row.get("user_id") or "")
        return SessionRecord(
            session_id=str(row["session_id"]),
            function_type=str(row["function_type"]),
            project_id=row["project_id"],
            user_id=owner_user_id,  # 兼容旧响应字段
            owner_user_id=owner_user_id,
            visibility=str(row.get("visibility") or "private"),
            mode=row.get("mode"),
            title=str(row["title"]),
            status=str(row["status"]),
            preview=str(row["preview"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    @staticmethod
    def _row_to_message(row: dict) -> MessageRecord:
        sender_user_id = str(row.get("sender_user_id") or row.get("user_id") or "")
        return MessageRecord(
            message_id=str(row["message_id"]),
            session_id=str(row["session_id"]),
            sender_user_id=sender_user_id,
            role=str(row["role"]),
            content=str(row["content"]),
            created_at=str(row["created_at"]),
        )

    async def list_sessions(
        self,
        user_id: str,
        function_type: str | None = None,
        project_id: str | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> List[SessionRecord]:
        async with self._lock:
            sql = f"""
                SELECT s.* FROM sessions s
                WHERE {_session_access_clause("s")}
            """
            params: list[object] = [user_id, user_id]
            if function_type:
                sql += " AND s.function_type = ?"
                params.append(function_type)
            if project_id:
                sql += " AND s.project_id = ?"
                params.append(project_id)
            sql += " ORDER BY s.updated_at DESC"
            if limit is not None:
                sql += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            rows = self._runtime.fetchall(sql, params)
            return [self._row_to_session(row) for row in rows]

    async def count_sessions(
        self,
        user_id: str,
        function_type: str | None = None,
        project_id: str | None = None,
    ) -> int:
        async with self._lock:
            sql = f"""
                SELECT COUNT(*) AS cnt FROM sessions s
                WHERE {_session_access_clause("s")}
            """
            params: list[object] = [user_id, user_id]
            if function_type:
                sql += " AND s.function_type = ?"
                params.append(function_type)
            if project_id:
                sql += " AND s.project_id = ?"
                params.append(project_id)
            row = self._runtime.fetchone(sql, params)
            return int(row["cnt"]) if row else 0

    async def get_session_for_user(self, user_id: str, session_id: str) -> SessionRecord | None:
        async with self._lock:
            row = self._runtime.fetchone(
                f"""
                SELECT s.* FROM sessions s
                WHERE s.session_id = ?
                  AND {_session_access_clause("s")}
                LIMIT 1
                """,
                (session_id, user_id, user_id),
            )
            if row is None:
                return None
            return self._row_to_session(row)

    async def get_session(self, user_id: str, session_id: str) -> SessionRecord | None:
        return await self.get_session_for_user(user_id=user_id, session_id=session_id)

    async def get_session_owner(self, session_id: str) -> str | None:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT owner_user_id, user_id FROM sessions
                WHERE session_id = ?
                LIMIT 1
                """,
                (session_id,),
            )
            if row is None:
                return None
            owner_user_id = row.get("owner_user_id") or row.get("user_id")
            return str(owner_user_id) if owner_user_id else None

    async def can_write_session(self, user_id: str, session_id: str) -> bool:
        async with self._lock:
            row = self._runtime.fetchone(
                f"""
                SELECT 1 FROM sessions s
                WHERE s.session_id = ?
                  AND {_session_write_clause("s")}
                LIMIT 1
                """,
                (session_id, user_id, user_id),
            )
            return row is not None

    async def create_session(
        self,
        user_id: str,
        function_type: str,
        title: str,
        project_id: str | None,
        mode: str | None = None,
        session_id: str | None = None,
        visibility: str = "private",
    ) -> SessionRecord:
        async with self._lock:
            now = _now_iso()
            resolved_session_id = session_id or _new_id("sess")
            record = SessionRecord(
                session_id=resolved_session_id,
                function_type=function_type,
                project_id=project_id,
                user_id=user_id,
                owner_user_id=user_id,
                visibility=visibility,
                mode=mode,
                title=title,
                status="active",
                preview="",
                created_at=now,
                updated_at=now,
            )
            if self._runtime.backend == "postgres":
                self._runtime.execute(
                    """
                    INSERT INTO sessions
                    (session_id, function_type, project_id, user_id, owner_user_id, visibility, mode, title, status, preview, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (session_id) DO UPDATE SET
                        function_type = EXCLUDED.function_type,
                        project_id = EXCLUDED.project_id,
                        user_id = EXCLUDED.user_id,
                        owner_user_id = EXCLUDED.owner_user_id,
                        visibility = EXCLUDED.visibility,
                        mode = EXCLUDED.mode,
                        title = EXCLUDED.title,
                        status = EXCLUDED.status,
                        preview = EXCLUDED.preview,
                        created_at = EXCLUDED.created_at,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        record.session_id,
                        record.function_type,
                        record.project_id,
                        record.user_id,
                        record.owner_user_id,
                        record.visibility,
                        record.mode,
                        record.title,
                        record.status,
                        record.preview,
                        record.created_at,
                        record.updated_at,
                    ),
                )
            else:
                self._runtime.execute(
                    """
                    INSERT OR REPLACE INTO sessions
                    (session_id, function_type, project_id, user_id, owner_user_id, visibility, mode, title, status, preview, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.session_id,
                        record.function_type,
                        record.project_id,
                        record.user_id,
                        record.owner_user_id,
                        record.visibility,
                        record.mode,
                        record.title,
                        record.status,
                        record.preview,
                        record.created_at,
                        record.updated_at,
                    ),
                )
            self._runtime.commit()
            return record

    async def update_session_title(
        self,
        user_id: str,
        session_id: str,
        title: str,
    ) -> SessionRecord | None:
        async with self._lock:
            row = self._runtime.fetchone(
                f"""
                SELECT s.* FROM sessions s
                WHERE s.session_id = ?
                  AND {_session_write_clause("s")}
                LIMIT 1
                """,
                (session_id, user_id, user_id),
            )
            if row is None:
                return None
            updated_at = _now_iso()
            self._runtime.execute(
                """
                UPDATE sessions
                SET title = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (title, updated_at, session_id),
            )
            self._runtime.commit()
            row = self._runtime.fetchone(
                """
                SELECT * FROM sessions
                WHERE session_id = ?
                LIMIT 1
                """,
                (session_id,),
            )
            return self._row_to_session(row) if row else None

    async def update_session_mode(
        self,
        user_id: str,
        session_id: str,
        mode: str,
    ) -> SessionRecord | None:
        async with self._lock:
            row = self._runtime.fetchone(
                f"""
                SELECT s.* FROM sessions s
                WHERE s.session_id = ?
                  AND {_session_write_clause("s")}
                LIMIT 1
                """,
                (session_id, user_id, user_id),
            )
            if row is None:
                return None
            updated_at = _now_iso()
            self._runtime.execute(
                """
                UPDATE sessions
                SET mode = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (mode, updated_at, session_id),
            )
            self._runtime.commit()
            updated = self._runtime.fetchone(
                """
                SELECT * FROM sessions
                WHERE session_id = ?
                LIMIT 1
                """,
                (session_id,),
            )
            return self._row_to_session(updated) if updated else None

    async def list_messages(self, user_id: str, session_id: str) -> List[MessageRecord]:
        async with self._lock:
            session = self._runtime.fetchone(
                f"""
                SELECT 1 FROM sessions s
                WHERE s.session_id = ?
                  AND {_session_access_clause("s")}
                LIMIT 1
                """,
                (session_id, user_id, user_id),
            )
            if session is None:
                return []
            rows = self._runtime.fetchall(
                """
                SELECT * FROM messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            )
            return [self._row_to_message(row) for row in rows]

    async def append_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
    ) -> MessageRecord | None:
        async with self._lock:
            session = self._runtime.fetchone(
                f"""
                SELECT 1 FROM sessions s
                WHERE s.session_id = ?
                  AND {_session_write_clause("s")}
                LIMIT 1
                """,
                (session_id, user_id, user_id),
            )
            if session is None:
                return None

            message = MessageRecord(
                message_id=_new_id("msg"),
                session_id=session_id,
                sender_user_id=user_id,
                role=role,
                content=content,
                created_at=_now_iso(),
            )
            self._runtime.execute(
                """
                INSERT INTO messages (message_id, session_id, user_id, sender_user_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.message_id,
                    message.session_id,
                    user_id,
                    message.sender_user_id,
                    message.role,
                    message.content,
                    message.created_at,
                ),
            )
            self._runtime.execute(
                """
                UPDATE sessions
                SET preview = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (content[:80], message.created_at, session_id),
            )
            self._runtime.commit()
            return message

    async def append_exchange(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> bool:
        async with self._lock:
            session = self._runtime.fetchone(
                f"""
                SELECT 1 FROM sessions s
                WHERE s.session_id = ?
                  AND {_session_write_clause("s")}
                LIMIT 1
                """,
                (session_id, user_id, user_id),
            )
            if session is None:
                return False

            now = _now_iso()
            self._runtime.execute(
                """
                INSERT INTO messages (message_id, session_id, user_id, sender_user_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (_new_id("msg_user"), session_id, user_id, user_id, "user", user_message, now),
            )
            assistant_created_at = _now_iso()
            self._runtime.execute(
                """
                INSERT INTO messages (message_id, session_id, user_id, sender_user_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _new_id("msg_assistant"),
                    session_id,
                    user_id,
                    user_id,
                    "assistant",
                    assistant_message,
                    assistant_created_at,
                ),
            )
            updated_at = _now_iso()
            self._runtime.execute(
                """
                UPDATE sessions
                SET preview = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (assistant_message[:80], updated_at, session_id),
            )
            self._runtime.commit()
            return True

    async def delete_session(self, user_id: str, session_id: str) -> bool:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT 1 FROM sessions
                WHERE session_id = ? AND owner_user_id = ?
                LIMIT 1
                """,
                (session_id, user_id),
            )
            if row is None:
                return False
            self._runtime.execute(
                "DELETE FROM messages WHERE session_id = ?",
                (session_id,),
            )
            self._runtime.execute(
                "DELETE FROM sessions WHERE session_id = ? AND owner_user_id = ?",
                (session_id, user_id),
            )
            self._runtime.commit()
            return True

    async def count_user_messages_since(self, user_id: str, since_iso: str) -> int:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT COUNT(*) AS cnt
                FROM messages
                WHERE sender_user_id = ? AND role = 'user' AND created_at >= ?
                """,
                (user_id, since_iso),
            )
            return int(row["cnt"]) if row else 0

    async def count_user_project_messages_since(self, user_id: str, project_id: str, since_iso: str) -> int:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT COUNT(*) AS cnt
                FROM messages m
                JOIN sessions s ON s.session_id = m.session_id
                WHERE m.sender_user_id = ?
                  AND m.role = 'user'
                  AND m.created_at >= ?
                  AND s.project_id = ?
                """,
                (user_id, since_iso, project_id),
            )
            return int(row["cnt"]) if row else 0


_store: ConversationStore | None = None
_store_db_key: tuple[str, str] | None = None


def get_conversation_store() -> ConversationStore:
    global _store, _store_db_key
    settings = get_settings()
    key = (settings.storage_db_path, settings.storage_db_url)
    if _store is None or _store_db_key != key:
        _store = ConversationStore(db_path=settings.storage_db_path, db_url=settings.storage_db_url)
        _store_db_key = key
    return _store
