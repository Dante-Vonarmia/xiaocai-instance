from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import time

import httpx

from xiaocai_instance_api.integrations.contracts import IntegrationStatusSummaryItem
from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.db_runtime import SQLRuntime, resolve_db_config
from xiaocai_instance_api.storage.integration_store import ConnectorStatus, get_integration_store


VALID_DOMAIN_MODES = {"off", "assist", "enforce"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class IntegrationService:
    async def get_integrations(self) -> dict:
        store = get_integration_store()
        domain_mode = await store.get_domain_injection_mode()
        connectors = await store.list_connectors()
        return {
            "domain_injection_mode": domain_mode,
            "connectors": [asdict(item) for item in connectors],
        }

    async def set_domain_injection_mode(self, mode: str, *, updated_by: str) -> str:
        normalized_mode = mode.strip().lower()
        if normalized_mode not in VALID_DOMAIN_MODES:
            raise ValueError("domain_injection_mode must be one of off|assist|enforce")
        store = get_integration_store()
        return await store.set_domain_injection_mode(normalized_mode, updated_by=updated_by)

    async def set_connector_enabled(self, key: str, *, enabled: bool, updated_by: str) -> dict | None:
        store = get_integration_store()
        connector = await store.set_connector_enabled(key=key, enabled=enabled, updated_by=updated_by)
        if connector is None:
            return None
        return asdict(connector)

    async def test_connector(self, key: str, *, updated_by: str) -> dict | None:
        store = get_integration_store()
        connector = await store.get_connector(key)
        if connector is None:
            return None

        if not connector.enabled:
            updated = await store.upsert_connector_status(
                ConnectorStatus(
                    key=connector.key,
                    name=connector.name,
                    enabled=False,
                    status="disconnected",
                    health="down",
                    latency_ms=None,
                    last_success_at=connector.last_success_at,
                    last_error="connector is disabled",
                    scope=connector.scope,
                    updated_at=_now_iso(),
                    updated_by=updated_by,
                )
            )
            return asdict(updated)

        if key == "xiaocai_db":
            updated = await self._test_xiaocai_db(connector=connector, updated_by=updated_by)
            return asdict(updated)

        if key == "mcp_gateway":
            updated = await self._test_http_connector(
                connector=connector,
                updated_by=updated_by,
                healthcheck_url=get_settings().mcp_healthcheck_url,
            )
            return asdict(updated)

        if key == "external_search":
            updated = await self._test_http_connector(
                connector=connector,
                updated_by=updated_by,
                healthcheck_url=get_settings().external_search_healthcheck_url,
            )
            return asdict(updated)

        return asdict(connector)

    async def get_integration_status_summary(self) -> dict:
        store = get_integration_store()
        connectors = await store.list_connectors()
        summary = [
            IntegrationStatusSummaryItem(
                key=item.key,
                enabled=item.enabled,
                status=item.status,
                health=item.health,
                latency_ms=item.latency_ms,
                updated_at=item.updated_at,
            ).model_dump()
            for item in connectors
        ]
        return {
            "connectors": summary,
            "generated_at": _now_iso(),
        }

    async def _test_xiaocai_db(self, *, connector: ConnectorStatus, updated_by: str) -> ConnectorStatus:
        store = get_integration_store()
        settings = get_settings()
        start = time.perf_counter()
        try:
            config = resolve_db_config(storage_db_url=settings.storage_db_url, storage_db_path=settings.storage_db_path)
            runtime = SQLRuntime(config)
            runtime.fetchone("SELECT 1 AS ok")
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            now_iso = _now_iso()
            return await store.upsert_connector_status(
                ConnectorStatus(
                    key=connector.key,
                    name=connector.name,
                    enabled=connector.enabled,
                    status="connected",
                    health="up",
                    latency_ms=elapsed_ms,
                    last_success_at=now_iso,
                    last_error="",
                    scope=connector.scope,
                    updated_at=now_iso,
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
                    updated_at=_now_iso(),
                    updated_by=updated_by,
                )
            )

    async def _test_http_connector(self, *, connector: ConnectorStatus, updated_by: str, healthcheck_url: str) -> ConnectorStatus:
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
                    updated_at=_now_iso(),
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
                        updated_at=_now_iso(),
                        updated_by=updated_by,
                    )
                )

            now_iso = _now_iso()
            return await store.upsert_connector_status(
                ConnectorStatus(
                    key=connector.key,
                    name=connector.name,
                    enabled=connector.enabled,
                    status="connected",
                    health="up",
                    latency_ms=elapsed_ms,
                    last_success_at=now_iso,
                    last_error="",
                    scope=connector.scope,
                    updated_at=now_iso,
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
                    updated_at=_now_iso(),
                    updated_by=updated_by,
                )
            )


_service: IntegrationService | None = None


def get_integration_service() -> IntegrationService:
    global _service
    if _service is None:
        _service = IntegrationService()
    return _service
