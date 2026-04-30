from __future__ import annotations


def _round_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def build_missing_field_priorities(
    *,
    required_fields: list[str],
    missing_fields: list[str],
    template_recommendation: dict,
) -> list[dict]:
    if not missing_fields:
        return []

    candidate_pool = template_recommendation.get("candidate_pool", [])
    ordered_missing = {field: index for index, field in enumerate(missing_fields)}
    required_positions = {field: index for index, field in enumerate(required_fields)}
    max_required_index = max(len(required_fields) - 1, 1)

    scored_fields: list[dict] = []
    for field in missing_fields:
        position_index = required_positions.get(field, ordered_missing.get(field, 0))
        stage_priority = 1.0 - (position_index / max_required_index)
        template_score = 0.0
        blocking_hits = 0
        influencing_templates: list[str] = []

        for candidate in candidate_pool:
            candidate_score = float(candidate.get("score") or 0.0)
            if field in candidate.get("missing_required_fields", []):
                template_score += candidate_score * 0.7
                template_key = str(candidate.get("template_key") or "")
                if template_key and template_key not in influencing_templates:
                    influencing_templates.append(template_key)
            if field in candidate.get("missing_blocking_fields", []):
                template_score += candidate_score
                blocking_hits += 1
                template_key = str(candidate.get("template_key") or "")
                if template_key and template_key not in influencing_templates:
                    influencing_templates.append(template_key)

        priority_score = _round_score(stage_priority * 0.4 + min(template_score, 1.0) * 0.6)
        scored_fields.append(
            {
                "field_key": field,
                "priority_score": priority_score,
                "stage_priority": _round_score(stage_priority),
                "template_score": _round_score(template_score),
                "blocking_hits": blocking_hits,
                "influencing_templates": influencing_templates,
            }
        )

    scored_fields.sort(
        key=lambda item: (
            item.get("priority_score", 0.0),
            item.get("blocking_hits", 0),
            item.get("stage_priority", 0.0),
        ),
        reverse=True,
    )
    return scored_fields
