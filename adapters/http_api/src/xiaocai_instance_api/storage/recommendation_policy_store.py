"""推荐策略管理存储（instance 侧，无UI）。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import asyncio
import json

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_scalar(text: str, key: str, default: str = "") -> str:
    prefix = f"{key}:"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped.split(":", 1)[1].strip().strip('"').strip("'")
    return default


def _resolve_shared_root() -> Path:
    settings = get_settings()
    raw_root = Path(settings.flare_domain_pack_root).expanduser()
    candidates = [
        raw_root / "domain-packs" / "shared",
        raw_root.parent / "domain-packs" / "shared",
        raw_root / "shared",
        Path("domain-packs") / "shared",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


@dataclass
class RecommendationPolicyProfile:
    tenant_id: str
    overrides: dict[str, Any]
    updated_at: str
    updated_by: str


class RecommendationPolicyStore:
    def __init__(self, db_path: str, db_url: str = ""):
        self._lock = asyncio.Lock()
        config = resolve_db_config(storage_db_url=db_url, storage_db_path=db_path)
        self._runtime = SQLRuntime(config)
        self._init_schema()

    def _init_schema(self) -> None:
        self._runtime.execute(
            """
            CREATE TABLE IF NOT EXISTS tenant_recommendation_policies (
                tenant_id TEXT PRIMARY KEY,
                overrides_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by TEXT NOT NULL
            )
            """
        )
        self._runtime.commit()

    @staticmethod
    def _row_to_profile(row: dict) -> RecommendationPolicyProfile:
        try:
            overrides = json.loads(str(row.get("overrides_json") or "{}"))
            if not isinstance(overrides, dict):
                overrides = {}
        except json.JSONDecodeError:
            overrides = {}
        return RecommendationPolicyProfile(
            tenant_id=str(row["tenant_id"]),
            overrides=overrides,
            updated_at=str(row["updated_at"]),
            updated_by=str(row["updated_by"]),
        )

    def _default_profile(self, tenant_id: str) -> RecommendationPolicyProfile:
        now = _now_iso()
        return RecommendationPolicyProfile(
            tenant_id=tenant_id,
            overrides={
                "rule_overrides": [],
                "global_overrides": {},
                "temporary": True,
            },
            updated_at=now,
            updated_by="system",
        )

    async def get_policy(self, tenant_id: str) -> RecommendationPolicyProfile:
        async with self._lock:
            row = self._runtime.fetchone(
                """
                SELECT * FROM tenant_recommendation_policies
                WHERE tenant_id = ?
                LIMIT 1
                """,
                (tenant_id,),
            )
            if row:
                return self._row_to_profile(row)

            default = self._default_profile(tenant_id)
            self._runtime.execute(
                """
                INSERT INTO tenant_recommendation_policies
                (tenant_id, overrides_json, updated_at, updated_by)
                VALUES (?, ?, ?, ?)
                """,
                (
                    default.tenant_id,
                    json.dumps(default.overrides, ensure_ascii=False),
                    default.updated_at,
                    default.updated_by,
                ),
            )
            self._runtime.commit()
            return default

    async def upsert_policy(
        self,
        tenant_id: str,
        *,
        overrides: dict[str, Any],
        updated_by: str,
    ) -> RecommendationPolicyProfile:
        async with self._lock:
            now = _now_iso()
            row = self._runtime.fetchone(
                "SELECT tenant_id FROM tenant_recommendation_policies WHERE tenant_id = ? LIMIT 1",
                (tenant_id,),
            )
            overrides_json = json.dumps(overrides or {}, ensure_ascii=False)
            if row:
                self._runtime.execute(
                    """
                    UPDATE tenant_recommendation_policies
                    SET overrides_json = ?, updated_at = ?, updated_by = ?
                    WHERE tenant_id = ?
                    """,
                    (overrides_json, now, updated_by, tenant_id),
                )
            else:
                self._runtime.execute(
                    """
                    INSERT INTO tenant_recommendation_policies
                    (tenant_id, overrides_json, updated_at, updated_by)
                    VALUES (?, ?, ?, ?)
                    """,
                    (tenant_id, overrides_json, now, updated_by),
                )
            self._runtime.commit()
            latest = self._runtime.fetchone(
                "SELECT * FROM tenant_recommendation_policies WHERE tenant_id = ? LIMIT 1",
                (tenant_id,),
            )
            return self._row_to_profile(
                latest
                or {
                    "tenant_id": tenant_id,
                    "overrides_json": overrides_json,
                    "updated_at": now,
                    "updated_by": updated_by,
                }
            )

    def load_base_assets(self) -> dict[str, Any]:
        shared_root = _resolve_shared_root()
        rules_path = shared_root / "rules" / "template_recommendation_rules.yaml"
        registry_path = shared_root / "rules" / "recommendation_policy_registry.yaml"
        audit_schema_path = shared_root / "artifacts" / "recommendation_audit_schema.yaml"

        rules_yaml = rules_path.read_text(encoding="utf-8") if rules_path.exists() else ""
        registry_yaml = registry_path.read_text(encoding="utf-8") if registry_path.exists() else ""
        audit_schema_yaml = audit_schema_path.read_text(encoding="utf-8") if audit_schema_path.exists() else ""

        return {
            "shared_root": str(shared_root),
            "rules_path": str(rules_path),
            "registry_path": str(registry_path),
            "audit_schema_path": str(audit_schema_path),
            "registry": {
                "policy_id": _extract_scalar(registry_yaml, "policy_id"),
                "version": _extract_scalar(registry_yaml, "version"),
                "status": _extract_scalar(registry_yaml, "status"),
                "effective_at": _extract_scalar(registry_yaml, "effective_at"),
                "owner": _extract_scalar(registry_yaml, "owner"),
                "change_reason": _extract_scalar(registry_yaml, "change_reason"),
            },
            "raw": {
                "template_recommendation_rules_yaml": rules_yaml,
                "recommendation_policy_registry_yaml": registry_yaml,
                "recommendation_audit_schema_yaml": audit_schema_yaml,
            },
        }


_store: RecommendationPolicyStore | None = None
_store_key: tuple[str, str] | None = None


def get_recommendation_policy_store(db_path: str | None = None) -> RecommendationPolicyStore:
    global _store, _store_key
    settings = get_settings()
    resolved_db_path = db_path or settings.storage_db_path
    resolved_db_url = settings.storage_db_url
    key = (resolved_db_path, resolved_db_url)
    if _store is None or _store_key != key:
        _store = RecommendationPolicyStore(db_path=resolved_db_path, db_url=resolved_db_url)
        _store_key = key
    return _store
