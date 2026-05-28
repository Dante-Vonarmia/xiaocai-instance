"""
Chat kernel context policy helpers.

职责:
1. 在 instance 侧补充 retrieval policy signal 到 kernel context
2. 不修改 FLARE Core 执行逻辑，仅提供输入信号
"""

from __future__ import annotations

from xiaocai_instance_api.retrieval.policy_resolver import resolve_enabled_search_source_policy
from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.source_policy import build_retrieval_policy_signal
from xiaocai_instance_api.storage.source_store import get_source_store


def _extract_source_id(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return str(value.get("source_id") or value.get("id") or "").strip()
    return ""


def _source_ids_from_refs(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [source_id for source_id in (_extract_source_id(item) for item in values) if source_id]


def _selected_source_ids(kernel_context: dict) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()
    source_ids = (
        _source_ids_from_refs(kernel_context.get("context_refs"))
        + _source_ids_from_refs(kernel_context.get("knowledge_refs"))
    )
    for source_id in source_ids:
        if source_id not in seen:
            seen.add(source_id)
            selected.append(source_id)
    return selected


def _filter_records_by_selected_sources(records: list, selected_source_ids: list[str]) -> list:
    if not selected_source_ids:
        return records
    records_by_id = {item.source_id: item for item in records}
    return [records_by_id[source_id] for source_id in selected_source_ids if source_id in records_by_id]


async def enrich_kernel_context_with_retrieval_policy(
    *,
    claims: AuthClaims,
    kernel_context: dict,
    user_message: str | None = None,
    limit: int = 20,
) -> dict:
    _ = user_message
    project_id = kernel_context.get("project_id")
    if not isinstance(project_id, str) or not project_id.strip():
        return kernel_context

    settings = get_settings()
    store = get_source_store(upload_root=settings.upload_root)
    records = await store.list_project_sources(
        user_id=claims.user_id,
        project_id=project_id.strip(),
        query=None,
    )
    selected_source_ids = _selected_source_ids(kernel_context)
    records = _filter_records_by_selected_sources(records, selected_source_ids)
    search_source_policy = await resolve_enabled_search_source_policy(kernel_context.get("mode"))
    policy = build_retrieval_policy_signal(
        records,
        limit=limit,
        search_source_policy=search_source_policy,
    )
    kernel_context["retrieval_policy"] = policy
    kernel_context["context_refs"] = policy.get("context_refs", [])
    return kernel_context
