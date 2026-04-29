from __future__ import annotations

from xiaocai_instance_api.integrations.contracts import IntegrationStatusSummaryItem
from xiaocai_instance_api.integrations.connector_runtime import (
    build_connector_view,
    now_iso,
    resolve_healthcheck_url,
    sync_connector_status_seed,
    test_http_connector,
    test_xiaocai_db,
    to_legacy_connector,
    to_search_policy,
    to_status_seed,
)
from xiaocai_instance_api.storage.connector_registry_store import get_connector_registry_store
from xiaocai_instance_api.storage.integration_store import ConnectorStatus, get_integration_store
from xiaocai_instance_api.storage.search_source_policy_store import get_search_source_policy_store


VALID_DOMAIN_MODES = {"off", "assist", "enforce"}


class IntegrationService:
    async def get_integrations(self) -> dict:
        store = get_integration_store()
        domain_mode = await store.get_domain_injection_mode()
        connectors = await self.get_connector_registry()
        return {
            "domain_injection_mode": domain_mode,
            "connectors": [to_legacy_connector(item) for item in connectors],
        }

    async def set_domain_injection_mode(self, mode: str, *, updated_by: str) -> str:
        normalized_mode = mode.strip().lower()
        if normalized_mode not in VALID_DOMAIN_MODES:
            raise ValueError("domain_injection_mode must be one of off|assist|enforce")
        store = get_integration_store()
        return await store.set_domain_injection_mode(normalized_mode, updated_by=updated_by)

    async def set_connector_enabled(self, key: str, *, enabled: bool, updated_by: str) -> dict | None:
        registry_store = get_connector_registry_store()
        connector = await registry_store.get_connector_by_key(key)
        if connector is None:
            return None
        updated = await registry_store.update_connector(
            connector.connector_id,
            name=None,
            enabled=enabled,
            priority=None,
            scope=None,
            config_json=None,
            tags_json=None,
            updated_by=updated_by,
        )
        if updated is None:
            return None
        await sync_connector_status_seed(updated, updated_by=updated_by)
        view = await build_connector_view(updated)
        return to_legacy_connector(view)

    async def test_connector(self, key: str, *, updated_by: str) -> dict | None:
        registry_store = get_connector_registry_store()
        connector = await registry_store.get_connector_by_key(key)
        if connector is None:
            return None
        tested = await self.test_connector_registry_item(connector.connector_id, updated_by=updated_by)
        if tested is None:
            return None
        return to_legacy_connector(tested)

    async def get_connector_registry(self) -> list[dict]:
        registry_store = get_connector_registry_store()
        registry_items = await registry_store.list_connectors()
        return [await build_connector_view(item) for item in registry_items]

    async def create_connector_registry_item(
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
    ) -> dict:
        registry_store = get_connector_registry_store()
        if await registry_store.get_connector_by_key(key):
            raise ValueError(f"connector key already exists: {key}")
        created = await registry_store.create_connector(
            key=key,
            name=name,
            connector_type=connector_type,
            driver=driver,
            enabled=enabled,
            priority=priority,
            scope=scope,
            config_json=config_json,
            tags_json=tags_json,
            updated_by=updated_by,
        )
        await sync_connector_status_seed(created, updated_by=updated_by)
        return await build_connector_view(created)

    async def update_connector_registry_item(
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
    ) -> dict | None:
        registry_store = get_connector_registry_store()
        updated = await registry_store.update_connector(
            connector_id,
            name=name,
            enabled=enabled,
            priority=priority,
            scope=scope,
            config_json=config_json,
            tags_json=tags_json,
            updated_by=updated_by,
        )
        if updated is None:
            return None
        if enabled is not None:
            await sync_connector_status_seed(updated, updated_by=updated_by)
        return await build_connector_view(updated)

    async def reorder_connector_registry_items(
        self,
        ordered_connector_ids: list[str],
        *,
        updated_by: str,
    ) -> list[dict]:
        registry_store = get_connector_registry_store()
        existing = await registry_store.list_connectors()
        existing_ids = {item.connector_id for item in existing}
        if set(ordered_connector_ids) != existing_ids:
            raise ValueError("ordered_connector_ids must match the full connector registry set")
        reordered = await registry_store.reorder_connectors(ordered_connector_ids, updated_by=updated_by)
        return [await build_connector_view(item) for item in reordered]

    async def test_connector_registry_item(self, connector_id: str, *, updated_by: str) -> dict | None:
        registry_store = get_connector_registry_store()
        connector = await registry_store.get_connector_by_id(connector_id)
        if connector is None:
            return None

        store = get_integration_store()
        current_status = await store.get_connector(connector.key)
        seeded = to_status_seed(connector, current_status)
        if not connector.enabled:
            updated = await store.upsert_connector_status(
                ConnectorStatus(
                    key=seeded.key,
                    name=seeded.name,
                    enabled=False,
                    status="disconnected",
                    health="down",
                    latency_ms=None,
                    last_success_at=seeded.last_success_at,
                    last_error="connector is disabled",
                    scope=seeded.scope,
                    updated_at=now_iso(),
                    updated_by=updated_by,
                )
            )
            return await build_connector_view(connector, status_override=updated)

        if connector.driver == "xiaocai_db":
            updated = await test_xiaocai_db(connector=seeded, updated_by=updated_by)
            return await build_connector_view(connector, status_override=updated)

        if connector.driver in {"mcp_gateway", "external_search"}:
            updated = await test_http_connector(
                connector=seeded,
                updated_by=updated_by,
                healthcheck_url=resolve_healthcheck_url(connector),
            )
            return await build_connector_view(connector, status_override=updated)

        return await build_connector_view(connector, status_override=seeded)

    async def get_search_source_policies(self) -> dict:
        store = get_search_source_policy_store()
        policies = await store.list_policies()
        return {"policies": [to_search_policy(item) for item in policies]}

    async def upsert_search_source_policy(
        self,
        *,
        mode: str,
        default_connector_key: str,
        allow_fallback: bool,
        fallback_connector_keys: list[str],
        routing_rules: list[dict],
        updated_by: str,
    ) -> dict:
        await self._ensure_connector_keys_exist([default_connector_key, *fallback_connector_keys])
        store = get_search_source_policy_store()
        updated = await store.upsert_policy(
            mode=mode,
            default_connector_key=default_connector_key,
            allow_fallback=allow_fallback,
            fallback_connector_keys=fallback_connector_keys,
            routing_rules=routing_rules,
            updated_by=updated_by,
        )
        return to_search_policy(updated)

    async def get_integration_status_summary(self) -> dict:
        connectors = await self.get_connector_registry()
        summary = [
            IntegrationStatusSummaryItem(
                key=str(item["key"]),
                enabled=bool(item["enabled"]),
                status=str(item["status"]),
                health=str(item["health"]),
                latency_ms=item.get("latency_ms"),
                updated_at=str(item["updated_at"]),
            ).model_dump()
            for item in connectors
        ]
        return {
            "connectors": summary,
            "generated_at": now_iso(),
        }

    async def _ensure_connector_keys_exist(self, keys: list[str]) -> None:
        registry_store = get_connector_registry_store()
        missing: list[str] = []
        for key in keys:
            if not await registry_store.get_connector_by_key(key):
                missing.append(key)
        if missing:
            raise ValueError(f"unknown connector keys: {', '.join(missing)}")

_service: IntegrationService | None = None


def get_integration_service() -> IntegrationService:
    global _service
    if _service is None:
        _service = IntegrationService()
    return _service
