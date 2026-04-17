"""
Chat kernel context policy helpers.

职责:
1. 在 instance 侧补充 retrieval policy signal 到 kernel context
2. 不修改 FLARE Core 执行逻辑，仅提供输入信号
"""

from __future__ import annotations

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.source_policy import build_retrieval_policy_signal
from xiaocai_instance_api.storage.source_store import get_source_store


async def enrich_kernel_context_with_retrieval_policy(
    *,
    claims: AuthClaims,
    kernel_context: dict,
    limit: int = 20,
) -> dict:
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
    policy = build_retrieval_policy_signal(records, limit=limit)
    kernel_context["retrieval_policy"] = policy
    kernel_context["context_refs"] = policy.get("context_refs", [])
    return kernel_context

