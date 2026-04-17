"""
租户品牌配置存储（instance 侧）。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio
import json

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TenantProfile:
    tenant_id: str
    product_name: str
    logo_url: str
    theme_primary: str
    theme_secondary: str
    feature_flags: dict
    updated_at: str
    updated_by: str


class TenantProfileStore:
    def __init__(self, db_path: str, db_url: str = ""):
        self._lock = asyncio.Lock()
        config = resolve_db_config(storage_db_url=db_url, storage_db_path=db_path)
        self._runtime = SQLRuntime(config)
        self._init_schema()

    def _init_schema(self) -> None:
        self._runtime.execute(
            """
            CREATE TABLE IF NOT EXISTS tenant_profiles (
                tenant_id TEXT PRIMARY KEY,
                product_name TEXT NOT NULL,
                logo_url TEXT NOT NULL,
                theme_primary TEXT NOT NULL,
                theme_secondary TEXT NOT NULL,
                feature_flags_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by TEXT NOT NULL
            )
            """
        )
        self._runtime.commit()

    @staticmethod
    def _row_to_profile(row: dict) -> TenantProfile:
        try:
            feature_flags = json.loads(str(row.get("feature_flags_json") or "{}"))
            if not isinstance(feature_flags, dict):
                feature_flags = {}
        except json.JSONDecodeError:
            feature_flags = {}
        return TenantProfile(
            tenant_id=str(row["tenant_id"]),
            product_name=str(row["product_name"]),
            logo_url=str(row["logo_url"]),
            theme_primary=str(row["theme_primary"]),
            theme_secondary=str(row["theme_secondary"]),
            feature_flags=feature_flags,
            updated_at=str(row["updated_at"]),
            updated_by=str(row["updated_by"]),
        )

    async def get_profile(self, tenant_id: str) -> TenantProfile:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT * FROM tenant_profiles
                WHERE tenant_id = ?
                LIMIT 1
                """,
                (tenant_id,),
            )
            if row:
                return self._row_to_profile(row)

            now = _now_iso()
            default = TenantProfile(
                tenant_id=tenant_id,
                product_name="xiaocai",
                logo_url="",
                theme_primary="#2563EB",
                theme_secondary="#0EA5E9",
                feature_flags={},
                updated_at=now,
                updated_by="system",
            )
            self._runtime.execute(
                """
                INSERT INTO tenant_profiles
                (tenant_id, product_name, logo_url, theme_primary, theme_secondary, feature_flags_json, updated_at, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    default.tenant_id,
                    default.product_name,
                    default.logo_url,
                    default.theme_primary,
                    default.theme_secondary,
                    json.dumps(default.feature_flags, ensure_ascii=False),
                    default.updated_at,
                    default.updated_by,
                ),
            )
            self._runtime.commit()
            return default

    async def upsert_profile(
        self,
        tenant_id: str,
        *,
        product_name: str,
        logo_url: str,
        theme_primary: str,
        theme_secondary: str,
        feature_flags: dict,
        updated_by: str,
    ) -> TenantProfile:
        async with self._lock:
            now = _now_iso()
            existing = self._runtime.fetchone(
                "SELECT tenant_id FROM tenant_profiles WHERE tenant_id = ? LIMIT 1",
                (tenant_id,),
            )
            feature_flags_json = json.dumps(feature_flags or {}, ensure_ascii=False)
            if existing:
                self._runtime.execute(
                    """
                    UPDATE tenant_profiles
                    SET product_name = ?, logo_url = ?, theme_primary = ?, theme_secondary = ?,
                        feature_flags_json = ?, updated_at = ?, updated_by = ?
                    WHERE tenant_id = ?
                    """,
                    (
                        product_name,
                        logo_url,
                        theme_primary,
                        theme_secondary,
                        feature_flags_json,
                        now,
                        updated_by,
                        tenant_id,
                    ),
                )
            else:
                self._runtime.execute(
                    """
                    INSERT INTO tenant_profiles
                    (tenant_id, product_name, logo_url, theme_primary, theme_secondary, feature_flags_json, updated_at, updated_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tenant_id,
                        product_name,
                        logo_url,
                        theme_primary,
                        theme_secondary,
                        feature_flags_json,
                        now,
                        updated_by,
                    ),
                )
            self._runtime.commit()
            row = self._runtime.fetchone("SELECT * FROM tenant_profiles WHERE tenant_id = ? LIMIT 1", (tenant_id,))
            return self._row_to_profile(row or {
                "tenant_id": tenant_id,
                "product_name": product_name,
                "logo_url": logo_url,
                "theme_primary": theme_primary,
                "theme_secondary": theme_secondary,
                "feature_flags_json": feature_flags_json,
                "updated_at": now,
                "updated_by": updated_by,
            })


_store: TenantProfileStore | None = None
_store_key: tuple[str, str] | None = None


def get_tenant_profile_store(db_path: str | None = None) -> TenantProfileStore:
    global _store, _store_key
    settings = get_settings()
    resolved_db_path = db_path or settings.storage_db_path
    resolved_db_url = settings.storage_db_url
    key = (resolved_db_path, resolved_db_url)
    if _store is None or _store_key != key:
        _store = TenantProfileStore(db_path=resolved_db_path, db_url=resolved_db_url)
        _store_key = key
    return _store
