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


def _apply_v4(runtime: SQLRuntime) -> None:
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS instance_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            updated_by TEXT NOT NULL
        )
        """
    )
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS connector_status (
            key TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            enabled INTEGER NOT NULL,
            status TEXT NOT NULL,
            health TEXT NOT NULL,
            latency_ms INTEGER NULL,
            last_success_at TEXT NULL,
            last_error TEXT NOT NULL DEFAULT '',
            scope TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            updated_by TEXT NOT NULL
        )
        """
    )

    mode_row = runtime.fetchone(
        "SELECT setting_key FROM instance_settings WHERE setting_key = ? LIMIT 1",
        ("domain_injection_mode",),
    )
    if mode_row is None:
        runtime.execute(
            """
            INSERT INTO instance_settings (setting_key, setting_value, updated_at, updated_by)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?)
            """,
            ("domain_injection_mode", "assist", "system"),
        )

    default_connectors = [
        ("xiaocai_db", "Xiaocai Database", 1, "disconnected", "down", "read_write"),
        ("mcp_gateway", "MCP Gateway", 0, "disconnected", "down", "read"),
        ("external_search", "External Search", 0, "disconnected", "down", "read"),
    ]
    for key, name, enabled, status, health, scope in default_connectors:
        row = runtime.fetchone(
            "SELECT key FROM connector_status WHERE key = ? LIMIT 1",
            (key,),
        )
        if row is not None:
            continue
        runtime.execute(
            """
            INSERT INTO connector_status (
                key, name, enabled, status, health,
                latency_ms, last_success_at, last_error,
                scope, updated_at, updated_by
            ) VALUES (?, ?, ?, ?, ?, NULL, NULL, '', ?, CURRENT_TIMESTAMP, ?)
            """,
            (key, name, enabled, status, health, scope, "system"),
        )


def _apply_v5(runtime: SQLRuntime) -> None:
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS connector_registry (
            connector_id TEXT PRIMARY KEY,
            key TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            connector_type TEXT NOT NULL,
            driver TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            priority INTEGER NOT NULL DEFAULT 100,
            scope TEXT NOT NULL DEFAULT 'read',
            config_json TEXT NOT NULL DEFAULT '{}',
            tags_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            updated_by TEXT NOT NULL
        )
        """
    )
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS search_source_policies (
            policy_id TEXT PRIMARY KEY,
            mode TEXT NOT NULL UNIQUE,
            default_connector_key TEXT NOT NULL,
            allow_fallback INTEGER NOT NULL DEFAULT 1,
            fallback_connector_keys_json TEXT NOT NULL DEFAULT '[]',
            routing_rules_json TEXT NOT NULL DEFAULT '[]',
            updated_at TEXT NOT NULL,
            updated_by TEXT NOT NULL
        )
        """
    )

    default_registry_rows = [
        ("conn_xiaocai_db", "xiaocai_db", "Xiaocai Database", "database", "xiaocai_db", 1, 10, "read_write"),
        ("conn_external_search", "external_search", "External Search", "search", "external_search", 0, 20, "read"),
        ("conn_mcp_gateway", "mcp_gateway", "MCP Gateway", "mcp", "mcp_gateway", 0, 30, "read"),
    ]
    for connector_id, key, name, connector_type, driver, enabled, priority, scope in default_registry_rows:
        existing = runtime.fetchone(
            "SELECT connector_id FROM connector_registry WHERE key = ? LIMIT 1",
            (key,),
        )
        if existing is not None:
            continue
        runtime.execute(
            """
            INSERT INTO connector_registry (
                connector_id, key, name, connector_type, driver,
                enabled, priority, scope, config_json, tags_json,
                created_at, updated_at, updated_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '{}', '[]', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
            """,
            (connector_id, key, name, connector_type, driver, enabled, priority, scope, "system"),
        )

    default_policy = runtime.fetchone(
        "SELECT policy_id FROM search_source_policies WHERE mode = ? LIMIT 1",
        ("intelligent_sourcing",),
    )
    if default_policy is None:
        runtime.execute(
            """
            INSERT INTO search_source_policies (
                policy_id, mode, default_connector_key, allow_fallback,
                fallback_connector_keys_json, routing_rules_json,
                updated_at, updated_by
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            """,
            (
                "search_policy_intelligent_sourcing",
                "intelligent_sourcing",
                "external_search",
                1,
                '["mcp_gateway","xiaocai_db"]',
                "[]",
                "system",
            ),
        )


def _apply_v6(runtime: SQLRuntime) -> None:
    session_context_default = (
        '{"context_revision_id":"","session_summary":"","user_focus":[],"response_priorities":[],"confirmed_fields":{},'
        '"missing_fields":[],"notes":[],"turns":[],"evidence":[],"facts":[],"inferences":[],"unknowns":[],'
        '"source_attributions":[],"artifact_context":[],"sourcing_results":[],"analysis_results":[],'
        '"rank_profile":{},"rank_feedback_log":[],"updated_at":""}'
    )
    if _table_exists(runtime, "sessions") and not _column_exists(runtime, "sessions", "title_source"):
        runtime.execute("ALTER TABLE sessions ADD COLUMN title_source TEXT NOT NULL DEFAULT 'default'")
    if _table_exists(runtime, "sessions") and not _column_exists(runtime, "sessions", "context"):
        runtime.execute(
            f"""
            ALTER TABLE sessions
            ADD COLUMN context TEXT NOT NULL DEFAULT '{session_context_default}'
            """
        )
    if _table_exists(runtime, "messages") and not _column_exists(runtime, "messages", "attachments"):
        runtime.execute("ALTER TABLE messages ADD COLUMN attachments TEXT NOT NULL DEFAULT '[]'")
    if _table_exists(runtime, "messages") and not _column_exists(runtime, "messages", "context_refs"):
        runtime.execute("ALTER TABLE messages ADD COLUMN context_refs TEXT NOT NULL DEFAULT '[]'")
    if _table_exists(runtime, "messages") and not _column_exists(runtime, "messages", "knowledge_refs"):
        runtime.execute("ALTER TABLE messages ADD COLUMN knowledge_refs TEXT NOT NULL DEFAULT '[]'")
    if _table_exists(runtime, "messages") and not _column_exists(runtime, "messages", "agent_status"):
        runtime.execute("ALTER TABLE messages ADD COLUMN agent_status TEXT NULL")
    if _table_exists(runtime, "messages") and not _column_exists(runtime, "messages", "thinking_trace"):
        runtime.execute("ALTER TABLE messages ADD COLUMN thinking_trace TEXT NOT NULL DEFAULT ''")
    if _table_exists(runtime, "messages") and not _column_exists(runtime, "messages", "execution_trace"):
        runtime.execute("ALTER TABLE messages ADD COLUMN execution_trace TEXT NULL")
    if _table_exists(runtime, "messages") and not _column_exists(runtime, "messages", "knowledge_search"):
        runtime.execute("ALTER TABLE messages ADD COLUMN knowledge_search TEXT NULL")
    if _table_exists(runtime, "messages") and not _column_exists(runtime, "messages", "sourcing_candidates"):
        runtime.execute("ALTER TABLE messages ADD COLUMN sourcing_candidates TEXT NULL")
    if _table_exists(runtime, "messages") and not _column_exists(runtime, "messages", "knowledge_citation"):
        runtime.execute("ALTER TABLE messages ADD COLUMN knowledge_citation TEXT NULL")
    if _table_exists(runtime, "messages") and not _column_exists(runtime, "messages", "context_usage"):
        runtime.execute("ALTER TABLE messages ADD COLUMN context_usage TEXT NULL")


def _apply_v7(runtime: SQLRuntime) -> None:
    if _table_exists(runtime, "projects") and not _column_exists(runtime, "projects", "project_name"):
        runtime.execute("ALTER TABLE projects ADD COLUMN project_name TEXT NOT NULL DEFAULT ''")
    if _table_exists(runtime, "projects"):
        runtime.execute(
            """
            UPDATE projects
            SET project_name = project_id
            WHERE project_name IS NULL OR project_name = ''
            """
        )


def _apply_v8(runtime: SQLRuntime) -> None:
    runtime.execute(
        """
        CREATE TABLE IF NOT EXISTS configuration_drafts (
            config_key TEXT NOT NULL,
            scope TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            base_version TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            PRIMARY KEY (config_key, scope)
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
    if current < 4:
        _apply_v4(runtime)
        _mark_version(runtime, 4)
    if current < 5:
        _apply_v5(runtime)
        _mark_version(runtime, 5)
    if current < 6:
        _apply_v6(runtime)
        _mark_version(runtime, 6)
    if current < 7:
        _apply_v7(runtime)
        _mark_version(runtime, 7)
    if current < 8:
        _apply_v8(runtime)
        _mark_version(runtime, 8)

    runtime.commit()
    return 8
