"""智能寻源投影 - xiaocai procurement sourcing contract."""

from __future__ import annotations

from typing import Any

from xiaocai_instance_api.chat.orchestration.extractor import extract_slots

SOURCING_TERMS = ("寻源", "供应商", "找供应商", "候选", "推荐供应商", "智能寻源")
BASE_FIELDS = ("产品/服务", "一级品类", "二级品类", "交付地点", "预算金额", "交付时间", "数量", "单位")
MINIMUM_INPUT_FIELDS = ("产品/服务", "二级品类", "一级品类")
PLACEHOLDER_POOLS = (
    ("internal_pool", "内部供应商库候选池", "instance_db"),
    ("backup_pool", "备用供应商库候选池", "local"),
    ("external_pool", "外部检索候选池", "web"),
)

def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _to_text(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return ""


def _should_project_sourcing(*, mode: str | None, user_message: str) -> bool:
    if (mode or "").strip() == "intelligent_sourcing":
        return True
    text = user_message.strip()
    return bool(text and any(term in text for term in SOURCING_TERMS))


def _collect_field_values(kernel_context: dict[str, Any], user_message: str) -> dict[str, str]:
    values: dict[str, str] = {}
    domain_prior = _as_dict(kernel_context.get("domain_prior"))
    sources = (
        _as_dict(kernel_context.get("confirmed_fields")),
        kernel_context,
        _as_dict(domain_prior.get("message_extracted_fields")),
        extract_slots(user_message),
    )
    for source in sources:
        for key, value in source.items():
            text = _to_text(value)
            if text and key not in values:
                values[str(key)] = text

    category_path = _as_list(_as_dict(domain_prior.get("category_prior")).get("resolved_path"))
    if category_path:
        values.setdefault("一级品类", _to_text(category_path[0]))
    if len(category_path) > 1:
        values.setdefault("二级品类", _to_text(category_path[1]))
    return values


def _field_rows(field_values: dict[str, str], status: str) -> list[dict[str, str]]:
    if status == "collected":
        return [
            {"field_key": field, "label": field, "value": field_values[field]}
            for field in BASE_FIELDS
            if _to_text(field_values.get(field))
        ]
    return [
        {"field_key": field, "label": field, "value": ""}
        for field in BASE_FIELDS
        if not _to_text(field_values.get(field))
    ]


def _query_text(field_values: dict[str, str], user_message: str) -> str:
    product = _to_text(field_values.get("产品/服务"))
    category = _to_text(field_values.get("二级品类")) or _to_text(field_values.get("一级品类"))
    region = _to_text(field_values.get("交付地点"))
    return " ".join(item for item in (product or category or user_message[:80], region, "供应商") if item).strip()


def _source_candidates(kernel_context: dict[str, Any], query: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for index, item in enumerate(_as_list(kernel_context.get("context_refs"))[:5]):
        ref = _as_dict(item)
        source_id = _to_text(ref.get("source_id")) or f"source_{index + 1}"
        title = _to_text(ref.get("file_name")) or _to_text(ref.get("title")) or source_id
        candidates.append(
            {
                "id": f"source-candidate-{index + 1}",
                "supplier_id": source_id,
                "supplier_name": title,
                "title": title,
                "result_role": "candidate",
                "candidate_kind": "project_source",
                "list_group": "project_context",
                "source_type": _to_text(ref.get("source_type")) or "local",
                "match_score": round(0.82 - index * 0.04, 4),
                "confidence": "medium",
                "summary": f"来自项目资料「{title}」，可作为候选供应商或供应商线索继续核验。",
                "match_reasons": ["命中项目上下文资料", f"匹配查询：{query}"],
                "evidence_refs": [{"id": source_id, "title": title, "source_type": _to_text(ref.get("source_type"))}],
                "unresolved_checks": ["需核验主体资质、历史案例、风险与诉讼、售后质保"],
            }
        )
    return candidates


def _placeholder_candidates(query: str) -> list[dict[str, Any]]:
    return [
        {
            "id": key,
            "supplier_id": key,
            "supplier_name": title,
            "title": title,
            "result_role": "candidate",
            "candidate_kind": "pool_placeholder",
            "list_group": "pending_verify",
            "source_type": source_type,
            "match_score": 0.5,
            "confidence": "low",
            "summary": "候选池占位，不代表真实供应商；需接入检索结果后替换为具体企业。",
            "match_reasons": [f"根据「{query}」生成待检索候选池"],
            "unresolved_checks": ["待检索企业主体", "待核验资质", "待核验案例", "待核验风险"],
        }
        for key, title, source_type in PLACEHOLDER_POOLS
    ]


def _source_meta(kernel_context: dict[str, Any], returned_count: int, has_source_candidates: bool) -> dict[str, Any]:
    policy = _as_dict(kernel_context.get("retrieval_policy"))
    route_plan = _as_dict(policy.get("route_plan"))
    return {
        "returned_count": returned_count,
        "source_breakdown": {"instance_db": 0, "local": returned_count if has_source_candidates else 0, "mcp": 0, "web": 0},
        "current_stage": "candidate_projection",
        "current_status": "projected",
        "selected_source": _to_text(route_plan.get("selected_connector_key")),
        "source_priority": _as_list(policy.get("selected_connector_keys")),
        "attempt_results": _as_list(policy.get("attempt_results")),
        "observations": ["缺失字段不阻断寻源入口；候选置信度随字段完整度调整。"],
    }


def build_sourcing_candidates_projection(
    *,
    kernel_context: dict[str, Any],
    mode: str | None,
    session_id: str,
    user_message: str,
) -> dict[str, Any] | None:
    """Project sourcing candidates without treating placeholders as domain truth."""
    if not _should_project_sourcing(mode=mode, user_message=user_message):
        return None

    field_values = _collect_field_values(kernel_context, user_message)
    collected = _field_rows(field_values, "collected")
    missing = _field_rows(field_values, "missing")
    query = _query_text(field_values, user_message)
    source_candidates = _source_candidates(kernel_context, query)
    candidates = source_candidates or _placeholder_candidates(query)
    base_ready = bool(query and any(_to_text(field_values.get(field)) for field in MINIMUM_INPUT_FIELDS))

    return {
        "run_id": f"sourcing-{session_id}",
        "mode_key": "intelligent_sourcing",
        "project_id": _to_text(kernel_context.get("project_id")),
        "session_id": session_id,
        "query": query,
        "message_excerpt": user_message[:120],
        "base_fields": list(BASE_FIELDS),
        "base_collected": collected,
        "base_missing": missing,
        "base_total": len(BASE_FIELDS),
        "base_progress": round(len(collected) / len(BASE_FIELDS), 4),
        "base_ready_for_matching": base_ready,
        "required_missing": [],
        "recommended_missing": [item["field_key"] for item in missing],
        "optional_missing": [],
        "requested_top_k": 5,
        "returned_count": len(candidates),
        "candidate_count": len(candidates),
        "has_more": False,
        "is_placeholder": not bool(source_candidates),
        "candidates": candidates,
        "source_meta": _source_meta(kernel_context, len(candidates), bool(source_candidates)),
        "summary": {
            "title": "候选供应商初筛",
            "text": "已按当前字段生成寻源结果投影；占位候选需要被真实检索结果替换。",
        },
        "actions": [
            {"action_key": "refine_sourcing_fields", "label": "补充寻源字段", "status": "available"},
            {"action_key": "generate_rfx", "label": "进入 RFX 策略", "status": "available"},
        ],
        "render_hint": "sourcing_candidates",
    }
