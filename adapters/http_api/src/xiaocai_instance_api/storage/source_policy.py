"""
Source retrieval policy helpers (instance-side signal generation).

职责:
1. 基于 source 元数据生成 retrieval policy 输入信号
2. 输出 preferred_sources / source_weights / context_refs
"""

from __future__ import annotations

from typing import Any

from xiaocai_instance_api.storage.source_store import SourceRecord


def _base_weight_for_source_type(source_type: str) -> float:
    normalized = (source_type or "").strip().lower()
    if normalized == "knowledge_base":
        return 0.70
    if normalized == "upload_attachment":
        return 0.50
    if normalized == "external_search":
        return 0.20
    return 0.30


def _priority_boost(context_priority: int) -> float:
    # 数值越小优先级越高，奖励越大
    if context_priority <= 20:
        return 0.30
    if context_priority <= 50:
        return 0.20
    if context_priority <= 100:
        return 0.10
    return 0.0


def build_retrieval_policy_signal(
    records: list[SourceRecord],
    *,
    limit: int = 20,
) -> dict[str, Any]:
    considered = records[: max(1, limit)]
    weights_by_type: dict[str, float] = {}
    context_refs: list[dict[str, Any]] = []

    for item in considered:
        source_type = item.source_type or "upload_attachment"
        score = _base_weight_for_source_type(source_type) + _priority_boost(item.context_priority)
        weights_by_type[source_type] = weights_by_type.get(source_type, 0.0) + score
        context_refs.append(
            {
                "source_id": item.source_id,
                "file_name": item.file_name,
                "source_type": source_type,
                "context_priority": item.context_priority,
                "date_bucket": item.date_bucket,
                "time_bucket": item.time_bucket,
                "weight_score": round(score, 4),
            }
        )

    total = sum(weights_by_type.values()) or 1.0
    source_weights = {
        key: round(value / total, 4)
        for key, value in sorted(weights_by_type.items(), key=lambda kv: kv[1], reverse=True)
    }
    preferred_sources = list(source_weights.keys())

    return {
        "preferred_sources": preferred_sources,
        "source_weights": source_weights,
        "context_refs": context_refs,
    }

