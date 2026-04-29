from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio
import json

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_policy_id(mode: str) -> str:
    return f"search_policy_{mode.strip().lower().replace('-', '_')}"


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _as_dict_list(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


@dataclass
class SearchSourcePolicy:
    policy_id: str
    mode: str
    default_connector_key: str
    allow_fallback: bool
    fallback_connector_keys: list[str]
    routing_rules: list[dict]
    updated_at: str
    updated_by: str


class SearchSourcePolicyStore:
    def __init__(self, db_path: str, db_url: str = ""):
        self._lock = asyncio.Lock()
        config = resolve_db_config(storage_db_url=db_url, storage_db_path=db_path)
        self._runtime = SQLRuntime(config)

    @staticmethod
    def _loads_str_list(raw: object) -> list[str]:
        try:
            return _as_str_list(json.loads(str(raw or "[]")))
        except json.JSONDecodeError:
            return []

    @staticmethod
    def _loads_dict_list(raw: object) -> list[dict]:
        try:
            return _as_dict_list(json.loads(str(raw or "[]")))
        except json.JSONDecodeError:
            return []

    @classmethod
    def _to_policy(cls, row: dict) -> SearchSourcePolicy:
        return SearchSourcePolicy(
            policy_id=str(row["policy_id"]),
            mode=str(row["mode"]),
            default_connector_key=str(row["default_connector_key"]),
            allow_fallback=bool(row["allow_fallback"]),
            fallback_connector_keys=cls._loads_str_list(row.get("fallback_connector_keys_json")),
            routing_rules=cls._loads_dict_list(row.get("routing_rules_json")),
            updated_at=str(row["updated_at"]),
            updated_by=str(row["updated_by"]),
        )

    async def list_policies(self) -> list[SearchSourcePolicy]:
        async with self._lock:
            rows = self._runtime.fetchall(
                """
                SELECT
                    policy_id, mode, default_connector_key, allow_fallback,
                    fallback_connector_keys_json, routing_rules_json,
                    updated_at, updated_by
                FROM search_source_policies
                ORDER BY mode ASC
                """
            )
            return [self._to_policy(row) for row in rows]

    async def get_policy(self, mode: str) -> SearchSourcePolicy | None:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT
                    policy_id, mode, default_connector_key, allow_fallback,
                    fallback_connector_keys_json, routing_rules_json,
                    updated_at, updated_by
                FROM search_source_policies
                WHERE mode = ?
                LIMIT 1
                """,
                (mode,),
            )
            return self._to_policy(row) if row else None

    async def upsert_policy(
        self,
        *,
        mode: str,
        default_connector_key: str,
        allow_fallback: bool,
        fallback_connector_keys: list[str],
        routing_rules: list[dict],
        updated_by: str,
    ) -> SearchSourcePolicy:
        async with self._lock:
            now = _now_iso()
            existing = self._runtime.fetchone(
                "SELECT policy_id FROM search_source_policies WHERE mode = ? LIMIT 1",
                (mode,),
            )
            if existing:
                self._runtime.execute(
                    """
                    UPDATE search_source_policies
                    SET
                        default_connector_key = ?,
                        allow_fallback = ?,
                        fallback_connector_keys_json = ?,
                        routing_rules_json = ?,
                        updated_at = ?,
                        updated_by = ?
                    WHERE mode = ?
                    """,
                    (
                        default_connector_key,
                        1 if allow_fallback else 0,
                        json.dumps(fallback_connector_keys or [], ensure_ascii=False),
                        json.dumps(routing_rules or [], ensure_ascii=False),
                        now,
                        updated_by,
                        mode,
                    ),
                )
            else:
                self._runtime.execute(
                    """
                    INSERT INTO search_source_policies (
                        policy_id, mode, default_connector_key, allow_fallback,
                        fallback_connector_keys_json, routing_rules_json,
                        updated_at, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        _new_policy_id(mode),
                        mode,
                        default_connector_key,
                        1 if allow_fallback else 0,
                        json.dumps(fallback_connector_keys or [], ensure_ascii=False),
                        json.dumps(routing_rules or [], ensure_ascii=False),
                        now,
                        updated_by,
                    ),
                )
            self._runtime.commit()
        policy = await self.get_policy(mode)
        if policy is None:
            raise RuntimeError(f"failed to upsert search source policy {mode}")
        return policy


_store: SearchSourcePolicyStore | None = None
_store_key: tuple[str, str] | None = None


def get_search_source_policy_store(db_path: str | None = None) -> SearchSourcePolicyStore:
    global _store, _store_key
    settings = get_settings()
    resolved_db_path = db_path or settings.storage_db_path
    resolved_db_url = settings.storage_db_url
    key = (resolved_db_path, resolved_db_url)
    if _store is None or _store_key != key:
        _store = SearchSourcePolicyStore(db_path=resolved_db_path, db_url=resolved_db_url)
        _store_key = key
    return _store
