from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config


DEFAULT_DOMAIN_INJECTION_MODE = "assist"
@dataclass
class ConnectorStatus:
    key: str
    name: str
    enabled: bool
    status: str
    health: str
    latency_ms: int | None
    last_success_at: str | None
    last_error: str
    scope: str
    updated_at: str
    updated_by: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class IntegrationStore:
    def __init__(self, db_path: str, db_url: str = ""):
        self._lock = asyncio.Lock()
        config = resolve_db_config(storage_db_url=db_url, storage_db_path=db_path)
        self._runtime = SQLRuntime(config)

    @staticmethod
    def _to_connector(row: dict) -> ConnectorStatus:
        return ConnectorStatus(
            key=str(row["key"]),
            name=str(row["name"]),
            enabled=bool(row["enabled"]),
            status=str(row["status"]),
            health=str(row["health"]),
            latency_ms=int(row["latency_ms"]) if row.get("latency_ms") is not None else None,
            last_success_at=str(row["last_success_at"]) if row.get("last_success_at") else None,
            last_error=str(row.get("last_error") or ""),
            scope=str(row.get("scope") or "read"),
            updated_at=str(row["updated_at"]),
            updated_by=str(row["updated_by"]),
        )

    async def get_domain_injection_mode(self) -> str:
        async with self._lock:
            row = self._runtime.fetchone(
                "SELECT setting_value FROM instance_settings WHERE setting_key = ? LIMIT 1",
                ("domain_injection_mode",),
            )
            return str(row["setting_value"]) if row and row.get("setting_value") else DEFAULT_DOMAIN_INJECTION_MODE

    async def set_domain_injection_mode(self, mode: str, *, updated_by: str) -> str:
        async with self._lock:
            now = _now_iso()
            existing = self._runtime.fetchone(
                "SELECT setting_key FROM instance_settings WHERE setting_key = ? LIMIT 1",
                ("domain_injection_mode",),
            )
            if existing:
                self._runtime.execute(
                    """
                    UPDATE instance_settings
                    SET setting_value = ?, updated_at = ?, updated_by = ?
                    WHERE setting_key = ?
                    """,
                    (mode, now, updated_by, "domain_injection_mode"),
                )
            else:
                self._runtime.execute(
                    """
                    INSERT INTO instance_settings (setting_key, setting_value, updated_at, updated_by)
                    VALUES (?, ?, ?, ?)
                    """,
                    ("domain_injection_mode", mode, now, updated_by),
                )
            self._runtime.commit()
            return mode

    async def list_connectors(self) -> list[ConnectorStatus]:
        async with self._lock:
            rows = self._runtime.fetchall(
                """
                SELECT
                    key, name, enabled, status, health,
                    latency_ms, last_success_at, last_error,
                    scope, updated_at, updated_by
                FROM connector_status
                ORDER BY key ASC
                """
            )
            return [self._to_connector(row) for row in rows]

    async def get_connector(self, key: str) -> ConnectorStatus | None:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT
                    key, name, enabled, status, health,
                    latency_ms, last_success_at, last_error,
                    scope, updated_at, updated_by
                FROM connector_status
                WHERE key = ?
                LIMIT 1
                """,
                (key,),
            )
            if row is None:
                return None
            return self._to_connector(row)

    async def set_connector_enabled(self, key: str, *, enabled: bool, updated_by: str) -> ConnectorStatus | None:
        async with self._lock:
            now = _now_iso()
            row = self._runtime.fetchone("SELECT key FROM connector_status WHERE key = ? LIMIT 1", (key,))
            if row is None:
                return None
            status = "connected" if enabled else "disconnected"
            health = "up" if enabled else "down"
            self._runtime.execute(
                """
                UPDATE connector_status
                SET enabled = ?, status = ?, health = ?, updated_at = ?, updated_by = ?
                WHERE key = ?
                """,
                (1 if enabled else 0, status, health, now, updated_by, key),
            )
            self._runtime.commit()

        return await self.get_connector(key)

    async def upsert_connector_status(self, connector: ConnectorStatus) -> ConnectorStatus:
        async with self._lock:
            existing = self._runtime.fetchone("SELECT key FROM connector_status WHERE key = ? LIMIT 1", (connector.key,))
            params = (
                connector.name,
                1 if connector.enabled else 0,
                connector.status,
                connector.health,
                connector.latency_ms,
                connector.last_success_at,
                connector.last_error,
                connector.scope,
                connector.updated_at,
                connector.updated_by,
                connector.key,
            )
            if existing:
                self._runtime.execute(
                    """
                    UPDATE connector_status
                    SET
                        name = ?,
                        enabled = ?,
                        status = ?,
                        health = ?,
                        latency_ms = ?,
                        last_success_at = ?,
                        last_error = ?,
                        scope = ?,
                        updated_at = ?,
                        updated_by = ?
                    WHERE key = ?
                    """,
                    params,
                )
            else:
                self._runtime.execute(
                    """
                    INSERT INTO connector_status (
                        key, name, enabled, status, health,
                        latency_ms, last_success_at, last_error,
                        scope, updated_at, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        connector.key,
                        connector.name,
                        1 if connector.enabled else 0,
                        connector.status,
                        connector.health,
                        connector.latency_ms,
                        connector.last_success_at,
                        connector.last_error,
                        connector.scope,
                        connector.updated_at,
                        connector.updated_by,
                    ),
                )
            self._runtime.commit()

        refreshed = await self.get_connector(connector.key)
        if refreshed is None:
            raise RuntimeError(f"failed to upsert connector {connector.key}")
        return refreshed


_store: IntegrationStore | None = None
_store_key: tuple[str, str] | None = None


def get_integration_store(db_path: str | None = None) -> IntegrationStore:
    global _store, _store_key
    settings = get_settings()
    resolved_db_path = db_path or settings.storage_db_path
    resolved_db_url = settings.storage_db_url
    key = (resolved_db_path, resolved_db_url)
    if _store is None or _store_key != key:
        _store = IntegrationStore(db_path=resolved_db_path, db_url=resolved_db_url)
        _store_key = key
    return _store
