"""
归属存储 - Project/Knowledge 归属管理
"""

from datetime import datetime, timezone
from typing import List
import asyncio

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class OwnershipStore:
    """归属存储（SQLite 持久化）"""

    def __init__(self, db_path: str, db_url: str = ""):
        config = resolve_db_config(storage_db_url=db_url, storage_db_path=db_path)
        self._db_path = config.dsn
        self._runtime = SQLRuntime(config)
        self._lock = asyncio.Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        self._runtime.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                tenant_id TEXT NULL,
                org_id TEXT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._runtime.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                tenant_id TEXT NULL,
                org_id TEXT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._runtime.execute(
            """
            CREATE TABLE IF NOT EXISTS project_members (
                project_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (project_id, user_id)
            )
            """
        )
        self._runtime.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_project_members_user_status
            ON project_members (user_id, status, project_id)
            """
        )
        self._runtime.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_project_members_project_status
            ON project_members (project_id, status, user_id)
            """
        )
        self._runtime.execute(
            """
            CREATE TABLE IF NOT EXISTS project_ownership (
                user_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                PRIMARY KEY (user_id, project_id)
            )
            """
        )
        self._runtime.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_ownership (
                user_id TEXT NOT NULL,
                knowledge_id TEXT NOT NULL,
                PRIMARY KEY (user_id, knowledge_id)
            )
            """
        )
        self._backfill_project_members_from_ownership()
        self._runtime.commit()

    def _upsert_user(self, user_id: str) -> None:
        now = _now_iso()
        if self._runtime.backend == "postgres":
            self._runtime.execute(
                """
                INSERT INTO users (user_id, created_at, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT (user_id) DO UPDATE SET updated_at = EXCLUDED.updated_at
                """,
                (user_id, now, now),
            )
            return
        self._runtime.execute(
            """
            INSERT INTO users (user_id, created_at, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT (user_id) DO UPDATE SET updated_at = excluded.updated_at
            """,
            (user_id, now, now),
        )

    def _upsert_project(self, project_id: str) -> None:
        now = _now_iso()
        if self._runtime.backend == "postgres":
            self._runtime.execute(
                """
                INSERT INTO projects (project_id, created_at, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT (project_id) DO UPDATE SET updated_at = EXCLUDED.updated_at
                """,
                (project_id, now, now),
            )
            return
        self._runtime.execute(
            """
            INSERT INTO projects (project_id, created_at, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT (project_id) DO UPDATE SET updated_at = excluded.updated_at
            """,
            (project_id, now, now),
        )

    def _backfill_project_members_from_ownership(self) -> None:
        rows = self._runtime.fetchall(
            """
            SELECT user_id, project_id FROM project_ownership
            """
        )
        for row in rows:
            user_id = str(row["user_id"])
            project_id = str(row["project_id"])
            self._upsert_user(user_id=user_id)
            self._upsert_project(project_id=project_id)
            now = _now_iso()
            if self._runtime.backend == "postgres":
                self._runtime.execute(
                    """
                    INSERT INTO project_members (project_id, user_id, role, status, created_at, updated_at)
                    VALUES (?, ?, 'owner', 'active', ?, ?)
                    ON CONFLICT (project_id, user_id) DO NOTHING
                    """,
                    (project_id, user_id, now, now),
                )
            else:
                self._runtime.execute(
                    """
                    INSERT OR IGNORE INTO project_members (project_id, user_id, role, status, created_at, updated_at)
                    VALUES (?, ?, 'owner', 'active', ?, ?)
                    """,
                    (project_id, user_id, now, now),
                )

    async def add_project_membership(
        self,
        user_id: str,
        project_id: str,
        role: str = "owner",
        status: str = "active",
    ) -> None:
        async with self._lock:
            self._upsert_user(user_id=user_id)
            self._upsert_project(project_id=project_id)
            now = _now_iso()
            row = self._runtime.fetchone(
                """
                SELECT 1 FROM project_members
                WHERE project_id = ? AND user_id = ?
                LIMIT 1
                """,
                (project_id, user_id),
            )
            if row is None:
                self._runtime.execute(
                    """
                    INSERT INTO project_members (project_id, user_id, role, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (project_id, user_id, role, status, now, now),
                )
            else:
                self._runtime.execute(
                    """
                    UPDATE project_members
                    SET role = ?, status = ?, updated_at = ?
                    WHERE project_id = ? AND user_id = ?
                    """,
                    (role, status, now, project_id, user_id),
                )
            self._runtime.commit()

    async def add_project_ownership(self, user_id: str, project_id: str) -> None:
        await self.add_project_membership(
            user_id=user_id,
            project_id=project_id,
            role="owner",
            status="active",
        )
        async with self._lock:
            if self._runtime.backend == "postgres":
                self._runtime.execute(
                    """
                    INSERT INTO project_ownership (user_id, project_id)
                    VALUES (?, ?)
                    ON CONFLICT (user_id, project_id) DO NOTHING
                    """,
                    (user_id, project_id),
                )
            else:
                self._runtime.execute(
                    """
                    INSERT OR IGNORE INTO project_ownership (user_id, project_id)
                    VALUES (?, ?)
                    """,
                    (user_id, project_id),
                )
            self._runtime.commit()

    async def add_knowledge_ownership(self, user_id: str, knowledge_id: str) -> None:
        async with self._lock:
            if self._runtime.backend == "postgres":
                self._runtime.execute(
                    """
                    INSERT INTO knowledge_ownership (user_id, knowledge_id)
                    VALUES (?, ?)
                    ON CONFLICT (user_id, knowledge_id) DO NOTHING
                    """,
                    (user_id, knowledge_id),
                )
            else:
                self._runtime.execute(
                    """
                    INSERT OR IGNORE INTO knowledge_ownership (user_id, knowledge_id)
                    VALUES (?, ?)
                    """,
                    (user_id, knowledge_id),
                )
            self._runtime.commit()

    async def check_project_access(self, user_id: str, project_id: str) -> bool:
        async with self._lock:
            member = self._runtime.fetchone(
                """
                SELECT 1 FROM project_members
                WHERE user_id = ? AND project_id = ? AND status = 'active'
                LIMIT 1
                """,
                (user_id, project_id),
            )
            if member is not None:
                return True
            row = self._runtime.fetchone(
                """
                SELECT 1 FROM project_ownership
                WHERE user_id = ? AND project_id = ?
                LIMIT 1
                """,
                (user_id, project_id),
            )
            if row is not None:
                # 兼容旧数据：发现旧 ownership 记录时自动补齐 project_members
                self._upsert_user(user_id=user_id)
                self._upsert_project(project_id=project_id)
                now = _now_iso()
                if self._runtime.backend == "postgres":
                    self._runtime.execute(
                        """
                        INSERT INTO project_members (project_id, user_id, role, status, created_at, updated_at)
                        VALUES (?, ?, 'owner', 'active', ?, ?)
                        ON CONFLICT (project_id, user_id) DO NOTHING
                        """,
                        (project_id, user_id, now, now),
                    )
                else:
                    self._runtime.execute(
                        """
                        INSERT OR IGNORE INTO project_members (project_id, user_id, role, status, created_at, updated_at)
                        VALUES (?, ?, 'owner', 'active', ?, ?)
                        """,
                        (project_id, user_id, now, now),
                    )
                self._runtime.commit()
            return row is not None

    async def check_knowledge_access(self, user_id: str, knowledge_id: str) -> bool:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT 1 FROM knowledge_ownership
                WHERE user_id = ? AND knowledge_id = ?
                LIMIT 1
                """,
                (user_id, knowledge_id),
            )
            return row is not None

    async def list_user_projects(self, user_id: str) -> List[str]:
        async with self._lock:
            rows = self._runtime.fetchall(
                """
                SELECT DISTINCT project_id FROM project_members
                WHERE user_id = ? AND status = 'active'
                UNION
                SELECT DISTINCT project_id FROM project_ownership
                WHERE user_id = ?
                ORDER BY project_id ASC
                """,
                (user_id, user_id),
            )
            return [str(row["project_id"]) for row in rows]

    async def get_project_member_role(self, user_id: str, project_id: str) -> str | None:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT role FROM project_members
                WHERE user_id = ? AND project_id = ? AND status = 'active'
                LIMIT 1
                """,
                (user_id, project_id),
            )
            if row is None:
                return None
            role = row.get("role")
            return str(role) if role is not None else None

    async def list_user_knowledge(self, user_id: str) -> List[str]:
        async with self._lock:
            rows = self._runtime.fetchall(
                """
                SELECT knowledge_id FROM knowledge_ownership
                WHERE user_id = ?
                ORDER BY knowledge_id ASC
                """,
                (user_id,),
            )
            return [str(row["knowledge_id"]) for row in rows]


# 全局单例
_store: OwnershipStore | None = None
_store_db_key: tuple[str, str] | None = None


def get_ownership_store() -> OwnershipStore:
    global _store, _store_db_key
    settings = get_settings()
    key = (settings.storage_db_path, settings.storage_db_url)
    if _store is None or _store_db_key != key:
        _store = OwnershipStore(db_path=settings.storage_db_path, db_url=settings.storage_db_url)
        _store_db_key = key
    return _store
