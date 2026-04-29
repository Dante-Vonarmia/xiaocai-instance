from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio
import json
import uuid

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_connector_id() -> str:
    return f"conn_{uuid.uuid4().hex[:12]}"


def _as_dict(value: object) -> dict:
    if isinstance(value, dict):
        return value
    return {}


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


@dataclass
class ConnectorRegistryItem:
    connector_id: str
    key: str
    name: str
    connector_type: str
    driver: str
    enabled: bool
    priority: int
    scope: str
    config_json: dict
    tags_json: list[str]
    created_at: str
    updated_at: str
    updated_by: str


class ConnectorRegistryStore:
    def __init__(self, db_path: str, db_url: str = ""):
        self._lock = asyncio.Lock()
        config = resolve_db_config(storage_db_url=db_url, storage_db_path=db_path)
        self._runtime = SQLRuntime(config)

    @staticmethod
    def _loads_dict(raw: object) -> dict:
        try:
            return _as_dict(json.loads(str(raw or "{}")))
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _loads_str_list(raw: object) -> list[str]:
        try:
            return _as_str_list(json.loads(str(raw or "[]")))
        except json.JSONDecodeError:
            return []

    @classmethod
    def _to_item(cls, row: dict) -> ConnectorRegistryItem:
        return ConnectorRegistryItem(
            connector_id=str(row["connector_id"]),
            key=str(row["key"]),
            name=str(row["name"]),
            connector_type=str(row["connector_type"]),
            driver=str(row["driver"]),
            enabled=bool(row["enabled"]),
            priority=int(row.get("priority") or 100),
            scope=str(row.get("scope") or "read"),
            config_json=cls._loads_dict(row.get("config_json")),
            tags_json=cls._loads_str_list(row.get("tags_json")),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            updated_by=str(row["updated_by"]),
        )

    async def list_connectors(self) -> list[ConnectorRegistryItem]:
        async with self._lock:
            rows = self._runtime.fetchall(
                """
                SELECT
                    connector_id, key, name, connector_type, driver,
                    enabled, priority, scope, config_json, tags_json,
                    created_at, updated_at, updated_by
                FROM connector_registry
                ORDER BY priority ASC, key ASC
                """
            )
            return [self._to_item(row) for row in rows]

    async def get_connector_by_id(self, connector_id: str) -> ConnectorRegistryItem | None:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT
                    connector_id, key, name, connector_type, driver,
                    enabled, priority, scope, config_json, tags_json,
                    created_at, updated_at, updated_by
                FROM connector_registry
                WHERE connector_id = ?
                LIMIT 1
                """,
                (connector_id,),
            )
            return self._to_item(row) if row else None

    async def get_connector_by_key(self, key: str) -> ConnectorRegistryItem | None:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT
                    connector_id, key, name, connector_type, driver,
                    enabled, priority, scope, config_json, tags_json,
                    created_at, updated_at, updated_by
                FROM connector_registry
                WHERE key = ?
                LIMIT 1
                """,
                (key,),
            )
            return self._to_item(row) if row else None

    async def create_connector(
        self,
        *,
        key: str,
        name: str,
        connector_type: str,
        driver: str,
        enabled: bool,
        priority: int,
        scope: str,
        config_json: dict,
        tags_json: list[str],
        updated_by: str,
    ) -> ConnectorRegistryItem:
        async with self._lock:
            now = _now_iso()
            connector_id = _new_connector_id()
            self._runtime.execute(
                """
                INSERT INTO connector_registry (
                    connector_id, key, name, connector_type, driver,
                    enabled, priority, scope, config_json, tags_json,
                    created_at, updated_at, updated_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    connector_id,
                    key,
                    name,
                    connector_type,
                    driver,
                    1 if enabled else 0,
                    priority,
                    scope,
                    json.dumps(config_json or {}, ensure_ascii=False),
                    json.dumps(tags_json or [], ensure_ascii=False),
                    now,
                    now,
                    updated_by,
                ),
            )
            self._runtime.commit()
        created = await self.get_connector_by_id(connector_id)
        if created is None:
            raise RuntimeError(f"failed to create connector {key}")
        return created

    async def update_connector(
        self,
        connector_id: str,
        *,
        name: str | None,
        enabled: bool | None,
        priority: int | None,
        scope: str | None,
        config_json: dict | None,
        tags_json: list[str] | None,
        updated_by: str,
    ) -> ConnectorRegistryItem | None:
        updates: list[str] = []
        params: list[object] = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if enabled else 0)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        if scope is not None:
            updates.append("scope = ?")
            params.append(scope)
        if config_json is not None:
            updates.append("config_json = ?")
            params.append(json.dumps(config_json, ensure_ascii=False))
        if tags_json is not None:
            updates.append("tags_json = ?")
            params.append(json.dumps(tags_json, ensure_ascii=False))
        if not updates:
            return await self.get_connector_by_id(connector_id)

        async with self._lock:
            updates.extend(["updated_at = ?", "updated_by = ?"])
            params.extend([_now_iso(), updated_by, connector_id])
            self._runtime.execute(
                f"UPDATE connector_registry SET {', '.join(updates)} WHERE connector_id = ?",
                tuple(params),
            )
            self._runtime.commit()
        return await self.get_connector_by_id(connector_id)

    async def reorder_connectors(
        self,
        ordered_connector_ids: list[str],
        *,
        updated_by: str,
    ) -> list[ConnectorRegistryItem]:
        async with self._lock:
            now = _now_iso()
            for index, connector_id in enumerate(ordered_connector_ids):
                self._runtime.execute(
                    """
                    UPDATE connector_registry
                    SET priority = ?, updated_at = ?, updated_by = ?
                    WHERE connector_id = ?
                    """,
                    ((index + 1) * 10, now, updated_by, connector_id),
                )
            self._runtime.commit()
        return await self.list_connectors()


_store: ConnectorRegistryStore | None = None
_store_key: tuple[str, str] | None = None


def get_connector_registry_store(db_path: str | None = None) -> ConnectorRegistryStore:
    global _store, _store_key
    settings = get_settings()
    resolved_db_path = db_path or settings.storage_db_path
    resolved_db_url = settings.storage_db_url
    key = (resolved_db_path, resolved_db_url)
    if _store is None or _store_key != key:
        _store = ConnectorRegistryStore(db_path=resolved_db_path, db_url=resolved_db_url)
        _store_key = key
    return _store
