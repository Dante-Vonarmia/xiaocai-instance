"""
分析产物存储
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List
import asyncio
import json
import uuid

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _artifact_access_clause(alias: str = "a") -> str:
    return f"""
        (
            {alias}.owner_user_id = ?
            OR (
                {alias}.visibility = 'project_shared'
                AND EXISTS (
                    SELECT 1 FROM project_members pm
                    WHERE pm.project_id = {alias}.project_id
                      AND pm.user_id = ?
                      AND pm.status = 'active'
                )
            )
        )
    """


def _artifact_write_clause(alias: str = "a") -> str:
    return f"""
        (
            {alias}.owner_user_id = ?
            OR (
                {alias}.visibility = 'project_shared'
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
class ArtifactRecord:
    artifact_id: str
    project_id: str
    conversation_id: str | None
    user_id: str
    owner_user_id: str
    visibility: str
    artifact_type: str
    content: dict
    created_at: str
    updated_at: str


class ArtifactStore:
    def __init__(self, db_path: str, db_url: str = ""):
        config = resolve_db_config(storage_db_url=db_url, storage_db_path=db_path)
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
        self._runtime.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_artifacts_project_owner_created
            ON artifacts (project_id, owner_user_id, created_at DESC)
            """
        )
        self._runtime.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_artifacts_conversation_created
            ON artifacts (conversation_id, created_at DESC)
            """
        )
        self._runtime.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_artifacts_project_visibility_created
            ON artifacts (project_id, visibility, created_at DESC)
            """
        )
        self._sync_legacy_columns()
        self._runtime.commit()

    def _sync_legacy_columns(self) -> None:
        if self._runtime.backend == "sqlite":
            columns = self._runtime.fetchall("PRAGMA table_info(artifacts)")
            names = {str(row["name"]) for row in columns}
            if "owner_user_id" not in names:
                self._runtime.execute("ALTER TABLE artifacts ADD COLUMN owner_user_id TEXT NULL")
            if "visibility" not in names:
                self._runtime.execute("ALTER TABLE artifacts ADD COLUMN visibility TEXT NOT NULL DEFAULT 'private'")
            self._runtime.execute(
                """
                UPDATE artifacts
                SET owner_user_id = COALESCE(owner_user_id, user_id)
                WHERE owner_user_id IS NULL OR owner_user_id = ''
                """
            )
            return

        columns = self._runtime.fetchall(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = 'artifacts'
            """
        )
        names = {str(row["column_name"]) for row in columns}
        if "owner_user_id" not in names:
            self._runtime.execute("ALTER TABLE artifacts ADD COLUMN owner_user_id TEXT NULL")
        if "visibility" not in names:
            self._runtime.execute("ALTER TABLE artifacts ADD COLUMN visibility TEXT NOT NULL DEFAULT 'private'")
        self._runtime.execute(
            """
            UPDATE artifacts
            SET owner_user_id = COALESCE(owner_user_id, user_id)
            WHERE owner_user_id IS NULL OR owner_user_id = ''
            """
        )

    @staticmethod
    def _row_to_record(row: dict) -> ArtifactRecord:
        owner_user_id = str(row.get("owner_user_id") or row.get("user_id") or "")
        content_json = row.get("content_json")
        if isinstance(content_json, str):
            try:
                content = json.loads(content_json)
            except json.JSONDecodeError:
                content = {"raw": content_json}
        elif isinstance(content_json, dict):
            content = content_json
        else:
            content = {}
        return ArtifactRecord(
            artifact_id=str(row["artifact_id"]),
            project_id=str(row["project_id"]),
            conversation_id=row.get("conversation_id"),
            user_id=owner_user_id,
            owner_user_id=owner_user_id,
            visibility=str(row.get("visibility") or "private"),
            artifact_type=str(row["artifact_type"]),
            content=content,
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    async def create_artifact(
        self,
        user_id: str,
        project_id: str,
        conversation_id: str | None,
        artifact_type: str,
        content: dict,
        visibility: str = "private",
    ) -> ArtifactRecord:
        async with self._lock:
            now = _now_iso()
            record = ArtifactRecord(
                artifact_id=_new_id("art"),
                project_id=project_id,
                conversation_id=conversation_id,
                user_id=user_id,
                owner_user_id=user_id,
                visibility=visibility,
                artifact_type=artifact_type,
                content=content,
                created_at=now,
                updated_at=now,
            )
            self._runtime.execute(
                """
                INSERT INTO artifacts
                (artifact_id, project_id, conversation_id, user_id, owner_user_id, visibility, artifact_type, content_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.artifact_id,
                    record.project_id,
                    record.conversation_id,
                    record.user_id,
                    record.owner_user_id,
                    record.visibility,
                    record.artifact_type,
                    json.dumps(record.content, ensure_ascii=False),
                    record.created_at,
                    record.updated_at,
                ),
            )
            self._runtime.commit()
            return record

    async def list_artifacts(
        self,
        user_id: str,
        project_id: str | None = None,
        conversation_id: str | None = None,
        artifact_type: str | None = None,
    ) -> List[ArtifactRecord]:
        async with self._lock:
            sql = f"""
                SELECT a.* FROM artifacts a
                WHERE {_artifact_access_clause("a")}
            """
            params: list[str] = [user_id, user_id]
            if project_id:
                sql += " AND a.project_id = ?"
                params.append(project_id)
            if conversation_id:
                sql += " AND a.conversation_id = ?"
                params.append(conversation_id)
            if artifact_type:
                sql += " AND a.artifact_type = ?"
                params.append(artifact_type)
            sql += " ORDER BY a.created_at DESC"
            rows = self._runtime.fetchall(sql, tuple(params))
            return [self._row_to_record(row) for row in rows]

    async def get_artifact_for_user(self, user_id: str, artifact_id: str) -> ArtifactRecord | None:
        async with self._lock:
            row = self._runtime.fetchone(
                f"""
                SELECT a.* FROM artifacts a
                WHERE a.artifact_id = ?
                  AND {_artifact_access_clause("a")}
                LIMIT 1
                """,
                (artifact_id, user_id, user_id),
            )
            if row is None:
                return None
            return self._row_to_record(row)

    async def can_write_artifact(self, user_id: str, artifact_id: str) -> bool:
        async with self._lock:
            row = self._runtime.fetchone(
                f"""
                SELECT 1 FROM artifacts a
                WHERE a.artifact_id = ?
                  AND {_artifact_write_clause("a")}
                LIMIT 1
                """,
                (artifact_id, user_id, user_id),
            )
            return row is not None

    async def delete_artifact(self, user_id: str, artifact_id: str) -> bool:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT 1 FROM artifacts
                WHERE artifact_id = ? AND owner_user_id = ?
                LIMIT 1
                """,
                (artifact_id, user_id),
            )
            if row is None:
                return False
            self._runtime.execute(
                "DELETE FROM artifacts WHERE artifact_id = ? AND owner_user_id = ?",
                (artifact_id, user_id),
            )
            self._runtime.commit()
            return True


_store: ArtifactStore | None = None
_store_key: tuple[str, str] | None = None


def get_artifact_store() -> ArtifactStore:
    global _store, _store_key
    settings = get_settings()
    key = (settings.storage_db_path, settings.storage_db_url)
    if _store is None or _store_key != key:
        _store = ArtifactStore(db_path=settings.storage_db_path, db_url=settings.storage_db_url)
        _store_key = key
    return _store
