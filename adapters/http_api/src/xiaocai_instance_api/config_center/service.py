from __future__ import annotations

from typing import Any

from xiaocai_instance_api.storage.config_draft_store import (
    ConfigDraft,
    get_config_draft_store,
    normalize_config_key,
    normalize_scope,
)


def to_config_draft_contract(draft: ConfigDraft) -> dict[str, Any]:
    return {
        "config_key": draft.config_key,
        "scope": draft.scope,
        "payload": draft.payload,
        "base_version": draft.base_version,
        "status": draft.status,
        "updated_at": draft.updated_at,
        "updated_by": draft.updated_by,
    }


class ConfigCenterService:
    async def get_draft(self, *, config_key: str, scope: str) -> dict[str, Any] | None:
        store = get_config_draft_store()
        draft = await store.get_draft(
            config_key=normalize_config_key(config_key),
            scope=normalize_scope(scope),
        )
        return to_config_draft_contract(draft) if draft else None

    async def upsert_draft(
        self,
        *,
        config_key: str,
        scope: str,
        payload: dict[str, Any],
        base_version: str,
        updated_by: str,
    ) -> dict[str, Any]:
        store = get_config_draft_store()
        draft = await store.upsert_draft(
            config_key=normalize_config_key(config_key),
            scope=normalize_scope(scope),
            payload=payload,
            base_version=base_version.strip(),
            updated_by=updated_by,
        )
        return to_config_draft_contract(draft)

    async def delete_draft(self, *, config_key: str, scope: str) -> bool:
        store = get_config_draft_store()
        return await store.delete_draft(
            config_key=normalize_config_key(config_key),
            scope=normalize_scope(scope),
        )


_service = ConfigCenterService()


def get_config_center_service() -> ConfigCenterService:
    return _service
