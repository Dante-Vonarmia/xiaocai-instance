from __future__ import annotations

from xiaocai_instance_api.storage.connector_registry_store import get_connector_registry_store
from xiaocai_instance_api.storage.search_source_policy_store import get_search_source_policy_store


async def resolve_enabled_search_source_policy(mode: str | None) -> dict | None:
    normalized_mode = mode.strip() if isinstance(mode, str) else ""
    if not normalized_mode:
        return None

    policy_store = get_search_source_policy_store()
    policy = await policy_store.get_policy(normalized_mode)
    if policy is None:
        return None

    registry_store = get_connector_registry_store()
    enabled_connectors = {
        item.key
        for item in await registry_store.list_connectors()
        if item.enabled
    }
    if policy.default_connector_key not in enabled_connectors:
        return None

    fallback_connector_keys = [
        key
        for key in policy.fallback_connector_keys
        if key in enabled_connectors and key != policy.default_connector_key
    ]
    return {
        "mode": policy.mode,
        "default_connector_key": policy.default_connector_key,
        "allow_fallback": policy.allow_fallback,
        "fallback_connector_keys": fallback_connector_keys,
        "routing_rules": policy.routing_rules,
    }
