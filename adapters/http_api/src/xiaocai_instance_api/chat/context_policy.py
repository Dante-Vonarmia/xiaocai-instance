"""
Chat kernel context policy helpers.

职责:
1. 在 instance 侧补充 retrieval policy signal 到 kernel context
2. 不修改 FLARE Core 执行逻辑，仅提供输入信号
"""

from __future__ import annotations

from xiaocai_instance_api.retrieval.policy_resolver import resolve_enabled_search_source_policy
from xiaocai_instance_api.chat.orchestration.prior_context import build_procurement_prior_context
from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.source_policy import build_retrieval_policy_signal
from xiaocai_instance_api.storage.source_store import get_source_store


async def enrich_kernel_context_with_retrieval_policy(
    *,
    claims: AuthClaims,
    kernel_context: dict,
    user_message: str | None = None,
    limit: int = 20,
) -> dict:
    project_id = kernel_context.get("project_id")
    if isinstance(project_id, str) and project_id.strip():
        settings = get_settings()
        store = get_source_store(upload_root=settings.upload_root)
        records = await store.list_project_sources(
            user_id=claims.user_id,
            project_id=project_id.strip(),
            query=None,
        )
        search_source_policy = await resolve_enabled_search_source_policy(kernel_context.get("mode"))
        policy = build_retrieval_policy_signal(
            records,
            limit=limit,
            search_source_policy=search_source_policy,
        )
        kernel_context["retrieval_policy"] = policy
        kernel_context["context_refs"] = policy.get("context_refs", [])

    # 领域模板先验不依赖 project source，需稳定注入给 kernel，
    # 让分析 / RFX 输出尽量贴近 procurement domain-pack 模板约束。
    try:
        prior = build_procurement_prior_context(
            kernel_context=kernel_context,
            mode=kernel_context.get("mode") if isinstance(kernel_context.get("mode"), str) else None,
            user_message=user_message,
        )
    except Exception:
        return kernel_context

    kernel_context["analysis_template"] = prior.analysis_template
    kernel_context["rfx_template"] = prior.rfx_template
    kernel_context["domain_prior"] = prior.domain_prior
    kernel_context["clarification_policy"] = prior.domain_prior.get("clarification_policy", {})
    kernel_context["category_prior"] = prior.domain_prior.get("category_prior", {})
    kernel_context["confidence_policy"] = prior.domain_prior.get("confidence_policy", {})
    return kernel_context
