from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import asyncio
import json
import re

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config


CONFIG_KEY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,80}$")
SCOPE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,80}$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _loads_payload(raw: object) -> dict[str, Any]:
    try:
        value = json.loads(str(raw or "{}"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def normalize_config_key(value: str) -> str:
    normalized = value.strip().lower()
    if not CONFIG_KEY_PATTERN.match(normalized):
        raise ValueError("config_key is invalid")
    return normalized


def normalize_scope(value: str) -> str:
    normalized = (value or "default").strip().lower()
    if not SCOPE_PATTERN.match(normalized):
        raise ValueError("scope is invalid")
    return normalized


@dataclass
class ConfigDraft:
    config_key: str
    scope: str
    payload: dict[str, Any]
    base_version: str
    status: str
    updated_at: str
    updated_by: str


class ConfigDraftStore:
    def __init__(self, db_path: str, db_url: str = ""):
        self._lock = asyncio.Lock()
        config = resolve_db_config(storage_db_url=db_url, storage_db_path=db_path)
        self._runtime = SQLRuntime(config)

    @classmethod
    def _to_draft(cls, row: dict[str, Any]) -> ConfigDraft:
        return ConfigDraft(
            config_key=str(row["config_key"]),
            scope=str(row["scope"]),
            payload=_loads_payload(row.get("payload_json")),
            base_version=str(row.get("base_version") or ""),
            status=str(row.get("status") or "draft"),
            updated_at=str(row["updated_at"]),
            updated_by=str(row["updated_by"]),
        )

    async def get_draft(self, *, config_key: str, scope: str) -> ConfigDraft | None:
        normalized_key = normalize_config_key(config_key)
        normalized_scope = normalize_scope(scope)
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT config_key, scope, payload_json, base_version, status, updated_at, updated_by
                FROM configuration_drafts
                WHERE config_key = ? AND scope = ?
                LIMIT 1
                """,
                (normalized_key, normalized_scope),
            )
            return self._to_draft(row) if row else None

    async def upsert_draft(
        self,
        *,
        config_key: str,
        scope: str,
        payload: dict[str, Any],
        base_version: str,
        updated_by: str,
    ) -> ConfigDraft:
        normalized_key = normalize_config_key(config_key)
        normalized_scope = normalize_scope(scope)
        async with self._lock:
            now = _now_iso()
            payload_json = json.dumps(payload or {}, ensure_ascii=False)
            existing = self._runtime.fetchone(
                "SELECT config_key FROM configuration_drafts WHERE config_key = ? AND scope = ? LIMIT 1",
                (normalized_key, normalized_scope),
            )
            if existing:
                self._runtime.execute(
                    """
                    UPDATE configuration_drafts
                    SET payload_json = ?, base_version = ?, status = 'draft', updated_at = ?, updated_by = ?
                    WHERE config_key = ? AND scope = ?
                    """,
                    (payload_json, base_version, now, updated_by, normalized_key, normalized_scope),
                )
            else:
                self._runtime.execute(
                    """
                    INSERT INTO configuration_drafts (
                        config_key, scope, payload_json, base_version,
                        status, created_at, updated_at, updated_by
                    ) VALUES (?, ?, ?, ?, 'draft', ?, ?, ?)
                    """,
                    (normalized_key, normalized_scope, payload_json, base_version, now, now, updated_by),
                )
            self._runtime.commit()
        draft = await self.get_draft(config_key=normalized_key, scope=normalized_scope)
        if draft is None:
            raise RuntimeError(f"failed to upsert config draft {normalized_key}/{normalized_scope}")
        return draft

    async def delete_draft(self, *, config_key: str, scope: str) -> bool:
        normalized_key = normalize_config_key(config_key)
        normalized_scope = normalize_scope(scope)
        async with self._lock:
            existing = self._runtime.fetchone(
                "SELECT config_key FROM configuration_drafts WHERE config_key = ? AND scope = ? LIMIT 1",
                (normalized_key, normalized_scope),
            )
            if not existing:
                return False
            self._runtime.execute(
                "DELETE FROM configuration_drafts WHERE config_key = ? AND scope = ?",
                (normalized_key, normalized_scope),
            )
            self._runtime.commit()
            return True


_store: ConfigDraftStore | None = None
_store_key: tuple[str, str] | None = None


def get_config_draft_store(db_path: str | None = None) -> ConfigDraftStore:
    global _store, _store_key
    settings = get_settings()
    resolved_db_path = db_path or settings.storage_db_path
    resolved_db_url = settings.storage_db_url
    key = (resolved_db_path, resolved_db_url)
    if _store is None or _store_key != key:
        _store = ConfigDraftStore(db_path=resolved_db_path, db_url=resolved_db_url)
        _store_key = key
    return _store
