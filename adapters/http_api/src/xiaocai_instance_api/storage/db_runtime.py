"""
存储运行时

职责:
1. 在 SQLite / PostgreSQL 之间切换
2. 屏蔽占位符差异（? / %s）
3. 统一返回 dict 行结构
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import sqlite3


@dataclass(frozen=True)
class DBConfig:
    backend: str
    dsn: str


def resolve_db_config(storage_db_url: str, storage_db_path: str) -> DBConfig:
    normalized_url = (storage_db_url or "").strip()
    if normalized_url.startswith("postgresql://") or normalized_url.startswith("postgres://"):
        return DBConfig(backend="postgres", dsn=normalized_url)
    return DBConfig(backend="sqlite", dsn=storage_db_path)


class SQLRuntime:
    def __init__(self, config: DBConfig):
        self._config = config
        self.backend = config.backend
        self._conn: Any
        self._has_pending_write = False

        if self.backend == "postgres":
            self._conn = self._connect_postgres()
        else:
            Path(config.dsn).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(config.dsn, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row

    @property
    def dsn(self) -> str:
        return self._config.dsn

    def _sql(self, statement: str) -> str:
        if self.backend == "postgres":
            return statement.replace("?", "%s")
        return statement

    def _connect_postgres(self) -> Any:
        from psycopg import connect
        from psycopg.rows import dict_row

        return connect(self._config.dsn, row_factory=dict_row)

    def _ensure_connection(self) -> None:
        if self.backend != "postgres":
            return
        if getattr(self._conn, "closed", False):
            self._conn = self._connect_postgres()

    def _is_operational_error(self, error: Exception) -> bool:
        if self.backend != "postgres":
            return False
        from psycopg import OperationalError

        return isinstance(error, OperationalError)

    def _run_with_reconnect(self, operation: Any) -> Any:
        self._ensure_connection()
        try:
            return operation()
        except Exception as error:
            if self._has_pending_write or not self._is_operational_error(error):
                raise
            self._conn = self._connect_postgres()
            return operation()

    def _finish_read_if_needed(self) -> None:
        if self.backend != "postgres" or self._has_pending_write:
            return
        try:
            self._conn.commit()
        except Exception as error:
            if not self._is_operational_error(error):
                raise
            self._conn = self._connect_postgres()

    @staticmethod
    def _normalize_row(row: Any) -> dict[str, Any] | None:
        if row is None:
            return None
        if isinstance(row, dict):
            return row
        try:
            return dict(row)
        except Exception:
            return None

    def execute(self, statement: str, params: tuple[Any, ...] | list[Any] = ()) -> None:
        self._run_with_reconnect(lambda: self._conn.execute(self._sql(statement), params))
        self._has_pending_write = True

    def fetchone(
        self,
        statement: str,
        params: tuple[Any, ...] | list[Any] = (),
    ) -> dict[str, Any] | None:
        row = self._run_with_reconnect(
            lambda: self._conn.execute(self._sql(statement), params).fetchone()
        )
        self._finish_read_if_needed()
        return self._normalize_row(row)

    def fetchall(
        self,
        statement: str,
        params: tuple[Any, ...] | list[Any] = (),
    ) -> list[dict[str, Any]]:
        rows = self._run_with_reconnect(
            lambda: self._conn.execute(self._sql(statement), params).fetchall()
        )
        self._finish_read_if_needed()
        normalized: list[dict[str, Any]] = []
        for row in rows:
            item = self._normalize_row(row)
            if item is not None:
                normalized.append(item)
        return normalized

    def commit(self) -> None:
        self._run_with_reconnect(lambda: self._conn.commit())
        self._has_pending_write = False
