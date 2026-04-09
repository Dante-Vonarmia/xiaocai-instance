"""
存储迁移管理

职责:
1. 管理 SQLite / PostgreSQL 的 schema 版本
2. 提供显式迁移入口（部署脚本/启动钩子调用）
"""

from __future__ import annotations

from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config


def _table_exists(runtime: SQLRuntime, table_name: str) -> bool:
    if runtime.backend == "postgres":
        row = runtime.fetchone(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = ?
            LIMIT 1
            """,
            (table_name,),
        )
    else:
        row = runtime.fetchone(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
            LIMIT 1
            """,
            (table_name,),
        )
    return row is not None


def _column_exists(runtime: SQLRuntime, table_name: str, column_name: str) -> bool:
    if runtime.backend == "postgres":
        row = runtime.fetchone(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = ? AND column_name = ?
            LIMIT 1
            """,
            (table_name, column_name),
        )
        return row is not None

    rows = runtime.fetchall(f"PRAGMA table_info({table_name})")
    names = {str(item["name"]) for item in rows}
    return column_name in names


def _ensure_schema_version(runtime: SQLRuntime) -> None:
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )


def _current_version(runtime: SQLRuntime) -> int:
    row = runtime.fetchone("SELECT MAX(version) AS version FROM schema_version")
    if row is None or row.get("version") is None:
        return 0
    return int(row["version"])


def _mark_version(runtime: SQLRuntime, version: int) -> None:
    runtime.execute(
        """
        INSERT INTO schema_version (version, applied_at)
        VALUES (?, CURRENT_TIMESTAMP)
        """,
        (version,),
    )


def _apply_v1(runtime: SQLRuntime) -> None:
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS project_ownership (
            user_id TEXT NOT NULL,
            project_id TEXT NOT NULL,
            PRIMARY KEY (user_id, project_id)
        )
        """
    )
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_ownership (
            user_id TEXT NOT NULL,
            knowledge_id TEXT NOT NULL,
            PRIMARY KEY (user_id, knowledge_id)
        )
        """
    )
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            function_type TEXT NOT NULL,
            project_id TEXT NULL,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            preview TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS project_sources (
            source_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            session_id TEXT NULL,
            file_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    runtime.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sessions_user_updated
        ON sessions (user_id, updated_at DESC)
        """
    )
    runtime.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_session_created
        ON messages (session_id, created_at ASC)
        """
    )
    runtime.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_project_sources_project_user
        ON project_sources (project_id, user_id, created_at DESC)
        """
    )


def _apply_v2(runtime: SQLRuntime) -> None:
    if _table_exists(runtime, "sessions") and not _column_exists(runtime, "sessions", "mode"):
        runtime.execute("ALTER TABLE sessions ADD COLUMN mode TEXT NULL")
    if _table_exists(runtime, "project_sources") and not _column_exists(runtime, "project_sources", "status"):
        runtime.execute("ALTER TABLE project_sources ADD COLUMN status TEXT NOT NULL DEFAULT 'available'")


def _apply_v3(runtime: SQLRuntime) -> None:
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            tenant_id TEXT NULL,
            org_id TEXT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            tenant_id TEXT NULL,
            org_id TEXT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS project_members (
            project_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (project_id, user_id)
        )
        """
    )
    runtime.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_project_members_user_status
        ON project_members (user_id, status, project_id)
        """
    )
    runtime.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_project_members_project_status
        ON project_members (project_id, status, user_id)
        """
    )
    if _table_exists(runtime, "sessions") and not _column_exists(runtime, "sessions", "owner_user_id"):
        runtime.execute("ALTER TABLE sessions ADD COLUMN owner_user_id TEXT NULL")
    if _table_exists(runtime, "sessions") and not _column_exists(runtime, "sessions", "visibility"):
        runtime.execute("ALTER TABLE sessions ADD COLUMN visibility TEXT NOT NULL DEFAULT 'private'")
    if _table_exists(runtime, "sessions"):
        runtime.execute(
            """
            UPDATE sessions
            SET owner_user_id = COALESCE(owner_user_id, user_id)
            WHERE owner_user_id IS NULL OR owner_user_id = ''
            """
        )
    if _table_exists(runtime, "messages") and not _column_exists(runtime, "messages", "sender_user_id"):
        runtime.execute("ALTER TABLE messages ADD COLUMN sender_user_id TEXT NULL")
    if _table_exists(runtime, "messages"):
        runtime.execute(
            """
            UPDATE messages
            SET sender_user_id = COALESCE(sender_user_id, user_id)
            WHERE sender_user_id IS NULL OR sender_user_id = ''
            """
        )
    if _table_exists(runtime, "project_sources") and not _column_exists(runtime, "project_sources", "owner_user_id"):
        runtime.execute("ALTER TABLE project_sources ADD COLUMN owner_user_id TEXT NULL")
    if _table_exists(runtime, "project_sources") and not _column_exists(runtime, "project_sources", "visibility"):
        runtime.execute("ALTER TABLE project_sources ADD COLUMN visibility TEXT NOT NULL DEFAULT 'private'")
    if _table_exists(runtime, "project_sources"):
        runtime.execute(
            """
            UPDATE project_sources
            SET owner_user_id = COALESCE(owner_user_id, user_id)
            WHERE owner_user_id IS NULL OR owner_user_id = ''
            """
        )
    runtime.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sessions_owner_updated
        ON sessions (owner_user_id, updated_at DESC)
        """
    )
    runtime.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sessions_project_owner_updated
        ON sessions (project_id, owner_user_id, updated_at DESC)
        """
    )
    runtime.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sessions_project_visibility_updated
        ON sessions (project_id, visibility, updated_at DESC)
        """
    )
    runtime.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_sender_created
        ON messages (sender_user_id, created_at ASC)
        """
    )
    runtime.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_project_sources_project_owner
        ON project_sources (project_id, owner_user_id, created_at DESC)
        """
    )
    runtime.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_project_sources_project_visibility
        ON project_sources (project_id, visibility, created_at DESC)
        """
    )
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS artifacts (
            artifact_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            conversation_id TEXT NULL,
            user_id TEXT NOT NULL,
            owner_user_id TEXT NOT NULL,
            visibility TEXT NOT NULL DEFAULT 'private',
            artifact_type TEXT NOT NULL,
            content_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    runtime.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_artifacts_project_owner_created
        ON artifacts (project_id, owner_user_id, created_at DESC)
        """
    )
    runtime.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_artifacts_conversation_created
        ON artifacts (conversation_id, created_at DESC)
        """
    )
    runtime.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_artifacts_project_visibility_created
        ON artifacts (project_id, visibility, created_at DESC)
        """
    )
    if _table_exists(runtime, "project_ownership"):
        runtime.execute(
            """
            INSERT INTO project_members (project_id, user_id, role, status, created_at, updated_at)
            SELECT po.project_id, po.user_id, 'owner', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM project_ownership po
            WHERE NOT EXISTS (
                SELECT 1 FROM project_members pm
                WHERE pm.project_id = po.project_id AND pm.user_id = po.user_id
            )
            """
        )


def run_storage_migrations(*, db_path: str, db_url: str = "") -> int:
    config = resolve_db_config(storage_db_url=db_url, storage_db_path=db_path)
    runtime = SQLRuntime(config)

    _ensure_schema_version(runtime)
    current = _current_version(runtime)

    if current < 1:
        _apply_v1(runtime)
        _mark_version(runtime, 1)
    if current < 2:
        _apply_v2(runtime)
        _mark_version(runtime, 2)
    if current < 3:
        _apply_v3(runtime)
        _mark_version(runtime, 3)

    runtime.commit()
    return 3
