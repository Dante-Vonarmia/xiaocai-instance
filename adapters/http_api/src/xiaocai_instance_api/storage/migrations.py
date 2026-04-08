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

    runtime.commit()
    return 2

