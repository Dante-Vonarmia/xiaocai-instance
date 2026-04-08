"""
归属存储 - Project/Knowledge 归属管理
"""

from typing import List
import asyncio

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config


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
        self._runtime.commit()

    async def add_project_ownership(self, user_id: str, project_id: str) -> None:
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
            row = self._runtime.fetchone(
                """
                SELECT 1 FROM project_ownership
                WHERE user_id = ? AND project_id = ?
                LIMIT 1
                """,
                (user_id, project_id),
            )
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
                SELECT project_id FROM project_ownership
                WHERE user_id = ?
                ORDER BY project_id ASC
                """,
                (user_id,),
            )
            return [str(row["project_id"]) for row in rows]

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
