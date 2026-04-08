"""
资料存储 - Source 文件管理
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List
import asyncio
import shutil
import uuid

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class SourceRecord:
    source_id: str
    project_id: str
    user_id: str
    session_id: str | None
    folder_name: str
    file_name: str
    file_size: int
    mime_type: str
    storage_path: str
    status: str
    created_at: str


@dataclass
class SourceFolderSummary:
    folder_name: str
    file_count: int
    referenced_count: int


class SourceStore:
    def __init__(self, upload_root: str, db_path: str, db_url: str = ""):
        self._lock = asyncio.Lock()
        config = resolve_db_config(storage_db_url=db_url, storage_db_path=db_path)
        self._runtime = SQLRuntime(config)
        self._upload_root = Path(upload_root)
        self._upload_root.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        self._runtime.execute(
            """
            CREATE TABLE IF NOT EXISTS project_sources (
                source_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                session_id TEXT NULL,
                folder_name TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        column_names = self._get_column_names()
        if "status" not in column_names:
            self._runtime.execute("ALTER TABLE project_sources ADD COLUMN status TEXT NOT NULL DEFAULT 'available'")
        if "folder_name" not in column_names:
            self._runtime.execute("ALTER TABLE project_sources ADD COLUMN folder_name TEXT NOT NULL DEFAULT '默认文件夹'")
        self._runtime.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_project_sources_project_user
            ON project_sources (project_id, user_id, created_at DESC)
            """
        )
        self._runtime.commit()

    def _get_column_names(self) -> set[str]:
        if self._runtime.backend == "sqlite":
            rows = self._runtime.fetchall("PRAGMA table_info(project_sources)")
            return {str(row["name"]) for row in rows}
        rows = self._runtime.fetchall(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'project_sources'
            """
        )
        return {str(row["column_name"]) for row in rows}

    @staticmethod
    def _row_to_record(row: dict) -> SourceRecord:
        return SourceRecord(
            source_id=str(row["source_id"]),
            project_id=str(row["project_id"]),
            user_id=str(row["user_id"]),
            session_id=row["session_id"],
            folder_name=str(row.get("folder_name") or "默认文件夹"),
            file_name=str(row["file_name"]),
            file_size=int(row["file_size"]),
            mime_type=str(row["mime_type"]),
            storage_path=str(row["storage_path"]),
            status=str(row["status"]),
            created_at=str(row["created_at"]),
        )

    async def list_project_sources(
        self,
        user_id: str,
        project_id: str,
        query: str | None = None,
        folder_name: str | None = None,
    ) -> List[SourceRecord]:
        async with self._lock:
            sql = """
                SELECT * FROM project_sources
                WHERE project_id = ? AND user_id = ?
            """
            params: list[str] = [project_id, user_id]
            if folder_name and folder_name.strip():
                sql += " AND folder_name = ?"
                params.append(folder_name.strip())
            if query and query.strip():
                sql += " AND LOWER(file_name) LIKE LOWER(?)"
                params.append(f"%{query.strip()}%")
            sql += " ORDER BY created_at DESC"
            rows = self._runtime.fetchall(
                sql,
                tuple(params),
            )
            return [self._row_to_record(row) for row in rows]

    async def list_project_folders(self, user_id: str, project_id: str) -> List[SourceFolderSummary]:
        async with self._lock:
            rows = self._runtime.fetchall(
                """
                SELECT
                    folder_name,
                    COUNT(*) AS file_count,
                    SUM(CASE WHEN status = 'referenced' THEN 1 ELSE 0 END) AS referenced_count
                FROM project_sources
                WHERE project_id = ? AND user_id = ?
                GROUP BY folder_name
                ORDER BY folder_name ASC
                """,
                (project_id, user_id),
            )
            return [
                SourceFolderSummary(
                    folder_name=str(row.get("folder_name") or "默认文件夹"),
                    file_count=int(row.get("file_count") or 0),
                    referenced_count=int(row.get("referenced_count") or 0),
                )
                for row in rows
            ]

    async def save_source_file(
        self,
        user_id: str,
        project_id: str,
        session_id: str | None,
        folder_name: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        source_file_path: Path,
    ) -> SourceRecord:
        async with self._lock:
            source_id = _new_id("src")
            target_dir = self._upload_root / project_id
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / f"{source_id}_{file_name}"
            shutil.move(str(source_file_path), target_path)

            record = SourceRecord(
                source_id=source_id,
                project_id=project_id,
                user_id=user_id,
                session_id=session_id,
                folder_name=folder_name,
                file_name=file_name,
                file_size=file_size,
                mime_type=mime_type,
                storage_path=str(target_path),
                status="available",
                created_at=_now_iso(),
            )
            self._runtime.execute(
                """
                INSERT INTO project_sources
                (source_id, project_id, user_id, session_id, folder_name, file_name, file_size, mime_type, storage_path, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.source_id,
                    record.project_id,
                    record.user_id,
                    record.session_id,
                    record.folder_name,
                    record.file_name,
                    record.file_size,
                    record.mime_type,
                    record.storage_path,
                    record.status,
                    record.created_at,
                ),
            )
            self._runtime.commit()
            return record

    async def mark_source_referenced(self, user_id: str, project_id: str, source_id: str) -> bool:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT source_id FROM project_sources
                WHERE source_id = ? AND project_id = ? AND user_id = ?
                LIMIT 1
                """,
                (source_id, project_id, user_id),
            )
            if row is None:
                return False
            self._runtime.execute(
                """
                UPDATE project_sources
                SET status = 'referenced'
                WHERE source_id = ? AND project_id = ? AND user_id = ?
                """,
                (source_id, project_id, user_id),
            )
            self._runtime.commit()
            return True

    async def delete_project_source(self, user_id: str, project_id: str, source_id: str) -> bool:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT storage_path FROM project_sources
                WHERE source_id = ? AND project_id = ? AND user_id = ?
                LIMIT 1
                """,
                (source_id, project_id, user_id),
            )
            if row is None:
                return False
            path = Path(str(row["storage_path"]))
            if path.exists():
                path.unlink()
            self._runtime.execute(
                """
                DELETE FROM project_sources
                WHERE source_id = ? AND project_id = ? AND user_id = ?
                """,
                (source_id, project_id, user_id),
            )
            self._runtime.commit()
            return True


_store: SourceStore | None = None
_store_key: tuple[str, str, str] | None = None


def get_source_store(upload_root: str, db_path: str | None = None) -> SourceStore:
    global _store, _store_key
    settings = get_settings()
    resolved_db_path = db_path or settings.storage_db_path
    resolved_db_url = settings.storage_db_url
    key = (upload_root, resolved_db_path, resolved_db_url)
    if _store is None or _store_key != key:
        _store = SourceStore(upload_root=upload_root, db_path=resolved_db_path, db_url=resolved_db_url)
        _store_key = key
    return _store
