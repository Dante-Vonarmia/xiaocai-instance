from __future__ import annotations

from datetime import datetime, timezone
import time

import httpx

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.connector_registry_store import ConnectorRegistryItem
from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config
from xiaocai_instance_api.storage.integration_store import ConnectorStatus, get_integration_store
from xiaocai_instance_api.storage.search_source_policy_store import SearchSourcePolicy


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def to_status_seed(
    connector: ConnectorRegistryItem,
    current_status: ConnectorStatus | None = None,
) -> ConnectorStatus:
    return ConnectorStatus(
        key=connector.key,
        name=connector.name,
        enabled=connector.enabled,
        status=current_status.status if current_status else "disconnected",
        health=current_status.health if current_status else "down",
        latency_ms=current_status.latency_ms if current_status else None,
        last_success_at=current_status.last_success_at if current_status else None,
        last_error=current_status.last_error if current_status else "",
        scope=connector.scope,
        updated_at=current_status.updated_at if current_status else now_iso(),
        updated_by=current_status.updated_by if current_status else "system",
    )


def to_legacy_connector(item: dict) -> dict:
    return {
        "key": item["key"],
        "name": item["name"],
        "enabled": item["enabled"],
        "status": item["status"],
        "health": item["health"],
        "latency_ms": item["latency_ms"],
        "last_success_at": item["last_success_at"],
        "last_error": item["last_error"],
        "scope": item["scope"],
        "updated_at": item["updated_at"],
        "updated_by": item["updated_by"],
    }


def to_search_policy(item: SearchSourcePolicy) -> dict:
    return {
        "policy_id": item.policy_id,
        "mode": item.mode,
        "default_connector_key": item.default_connector_key,
        "allow_fallback": item.allow_fallback,
        "fallback_connector_keys": item.fallback_connector_keys,
        "routing_rules": item.routing_rules,
        "updated_at": item.updated_at,
        "updated_by": item.updated_by,
    }


async def build_connector_view(
    connector: ConnectorRegistryItem,
    *,
    status_override: ConnectorStatus | None = None,
) -> dict:
    store = get_integration_store()
    status = status_override or await store.get_connector(connector.key)
    seeded = to_status_seed(connector, status)
    return {
        "connector_id": connector.connector_id,
        "key": connector.key,
        "name": connector.name,
        "connector_type": connector.connector_type,
        "driver": connector.driver,
        "enabled": connector.enabled,
        "priority": connector.priority,
        "scope": connector.scope,
        "config_json": connector.config_json,
        "tags_json": connector.tags_json,
        "status": seeded.status,
        "health": seeded.health,
        "latency_ms": seeded.latency_ms,
        "last_success_at": seeded.last_success_at,
        "last_error": seeded.last_error,
        "updated_at": connector.updated_at,
        "updated_by": connector.updated_by,
    }


async def sync_connector_status_seed(connector: ConnectorRegistryItem, *, updated_by: str) -> None:
    store = get_integration_store()
    current_status = await store.get_connector(connector.key)
    seeded = to_status_seed(connector, current_status)
    if not connector.enabled:
        seeded.enabled = False
        seeded.status = "disconnected"
        seeded.health = "down"
        seeded.last_error = "connector is disabled"
    else:
        seeded.enabled = True
        if not current_status:
            seeded.status = "disconnected"
            seeded.health = "down"
            seeded.last_error = ""
    seeded.updated_at = now_iso()
    seeded.updated_by = updated_by
    await store.upsert_connector_status(seeded)


def resolve_healthcheck_url(connector: ConnectorRegistryItem) -> str:
    config_url = str(connector.config_json.get("healthcheck_url") or "").strip()
    if config_url:
        return config_url
    settings = get_settings()
    if connector.driver == "mcp_gateway":
        return settings.mcp_healthcheck_url
    if connector.driver == "external_search":
        return settings.external_search_healthcheck_url
    return ""


async def test_xiaocai_db(*, connector: ConnectorStatus, updated_by: str) -> ConnectorStatus:
    store = get_integration_store()
    settings = get_settings()
    start = time.perf_counter()
    try:
        config = resolve_db_config(storage_db_url=settings.storage_db_url, storage_db_path=settings.storage_db_path)
        runtime = SQLRuntime(config)
        runtime.fetchone("SELECT 1 AS ok")
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        current_now = now_iso()
        return await store.upsert_connector_status(
            ConnectorStatus(
                key=connector.key,
                name=connector.name,
                enabled=connector.enabled,
                status="connected",
                health="up",
                latency_ms=elapsed_ms,
                last_success_at=current_now,
                last_error="",
                scope=connector.scope,
                updated_at=current_now,
                updated_by=updated_by,
            )
        )
    except Exception as exc:
        return await store.upsert_connector_status(
            ConnectorStatus(
                key=connector.key,
                name=connector.name,
                enabled=connector.enabled,
                status="error",
                health="down",
                latency_ms=None,
                last_success_at=connector.last_success_at,
                last_error=str(exc),
                scope=connector.scope,
                updated_at=now_iso(),
                updated_by=updated_by,
            )
        )


async def test_http_connector(*, connector: ConnectorStatus, updated_by: str, healthcheck_url: str) -> ConnectorStatus:
    store = get_integration_store()
    target_url = (healthcheck_url or "").strip()
    if not target_url:
        return await store.upsert_connector_status(
            ConnectorStatus(
                key=connector.key,
                name=connector.name,
                enabled=connector.enabled,
                status="disconnected",
                health="down",
                latency_ms=None,
                last_success_at=connector.last_success_at,
                last_error="healthcheck url is not configured",
                scope=connector.scope,
                updated_at=now_iso(),
                updated_by=updated_by,
            )
        )

    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(target_url)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        if response.status_code >= 400:
            return await store.upsert_connector_status(
                ConnectorStatus(
                    key=connector.key,
                    name=connector.name,
                    enabled=connector.enabled,
                    status="error",
                    health="down",
                    latency_ms=elapsed_ms,
                    last_success_at=connector.last_success_at,
                    last_error=f"healthcheck failed: HTTP {response.status_code}",
                    scope=connector.scope,
                    updated_at=now_iso(),
                    updated_by=updated_by,
                )
            )

        current_now = now_iso()
        return await store.upsert_connector_status(
            ConnectorStatus(
                key=connector.key,
                name=connector.name,
                enabled=connector.enabled,
                status="connected",
                health="up",
                latency_ms=elapsed_ms,
                last_success_at=current_now,
                last_error="",
                scope=connector.scope,
                updated_at=current_now,
                updated_by=updated_by,
            )
        )
    except Exception as exc:
        return await store.upsert_connector_status(
            ConnectorStatus(
                key=connector.key,
                name=connector.name,
                enabled=connector.enabled,
                status="error",
                health="down",
                latency_ms=None,
                last_success_at=connector.last_success_at,
                last_error=str(exc),
                scope=connector.scope,
                updated_at=now_iso(),
                updated_by=updated_by,
            )
        )
