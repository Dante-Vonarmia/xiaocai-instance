from __future__ import annotations


def _as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def _to_text(value: object) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _build_category_clarification_pending(
    *,
    confidence_policy: dict,
    category_prior: dict,
    session_id: str,
    mode: str | None,
) -> dict:
    options = []
    for candidate in _as_list(category_prior.get("candidate_pool"))[:3]:
        level1 = _to_text(_as_dict(candidate).get("level1_category"))
        if level1 and level1 not in options:
            options.append(level1)

    question_text = "为避免品类判断偏差，建议先确认更接近哪类采购方向。"
    return {
        "current_stage": "clarify_category",
        "command_type": "clarify_category_first",
        "missing_fields": ["一级品类"],
        "current_question": {
            "field_key": "一级品类",
            "field_label": "一级品类",
            "question_text": question_text,
            "options": options,
        },
        "question": {
            "field_key": "一级品类",
            "question_text": question_text,
            "options": options,
        },
        "chooser": {"field_key": "一级品类", "options": options},
        "interaction_node": {"id": "一级品类", "field_key": "一级品类", "title": question_text},
        "next_actions": [{
            "action_key": "clarify_category_first",
            "label": "先确认品类",
            "status": "available",
            "target_mode": mode or "requirement_canvas",
        }],
        "gate": {"status": "blocked", "reason": "low_category_confidence"},
        "summary_confirmed": False,
        "intake_session_id": session_id,
        "confidence_policy": confidence_policy,
    }


def _build_requirement_clarification_pending(
    *,
    confidence_policy: dict,
    clarification_policy: dict,
    session_id: str,
    mode: str | None,
) -> dict | None:
    top_missing_field = _to_text(confidence_policy.get("top_missing_field")) or _to_text(clarification_policy.get("top_missing_field"))
    if not top_missing_field:
        return None
    question_text = f"为先把当前需求分析做准，建议先补充：{top_missing_field}"
    return {
        "current_stage": "clarify_requirement",
        "command_type": "clarify_requirement_first",
        "missing_fields": [top_missing_field],
        "current_question": {
            "field_key": top_missing_field,
            "field_label": top_missing_field,
            "question_text": question_text,
            "options": [],
        },
        "question": {
            "field_key": top_missing_field,
            "question_text": question_text,
            "options": [],
        },
        "chooser": {},
        "interaction_node": {"id": top_missing_field, "field_key": top_missing_field, "title": question_text},
        "next_actions": [{
            "action_key": "clarify_requirement_first",
            "label": "先补关键字段",
            "status": "available",
            "target_mode": mode or "requirement_canvas",
        }],
        "gate": {"status": "blocked", "reason": "low_readiness_score"},
        "summary_confirmed": False,
        "intake_session_id": session_id,
        "confidence_policy": confidence_policy,
    }


def _build_canvas_defer_pending(
    *,
    confidence_policy: dict,
    clarification_policy: dict,
    session_id: str,
    mode: str | None,
) -> dict:
    question_text = "当前更适合先在 Canvas 中补充细节，我先不强制追问。"
    return {
        "current_stage": "defer_to_canvas",
        "command_type": "defer_to_canvas",
        "missing_fields": _as_list(clarification_policy.get("defer_to_canvas")),
        "current_question": {
            "field_key": "canvas_refine",
            "field_label": "Canvas补充",
            "question_text": question_text,
            "options": [],
        },
        "question": {
            "field_key": "canvas_refine",
            "question_text": question_text,
            "options": [],
        },
        "chooser": {},
        "interaction_node": {"id": "canvas_refine", "field_key": "canvas_refine", "title": question_text},
        "next_actions": [{
            "action_key": "defer_to_canvas",
            "label": "去 Canvas 补充",
            "status": "available",
            "target_mode": mode or "requirement_canvas",
        }],
        "gate": {"status": "collecting", "reason": "defer_to_canvas"},
        "summary_confirmed": False,
        "intake_session_id": session_id,
        "confidence_policy": confidence_policy,
    }


def apply_confidence_policy_to_pending_contract(
    *,
    pending_contract: dict | None,
    confidence_policy: dict | None,
    clarification_policy: dict | None,
    category_prior: dict | None,
    session_id: str,
    mode: str | None,
) -> dict | None:
    policy = _as_dict(confidence_policy)
    if not policy:
        return pending_contract
    if pending_contract:
        merged = dict(pending_contract)
        merged["confidence_policy"] = policy
        return merged

    action = _to_text(policy.get("action")) or "proceed"
    clarification = _as_dict(clarification_policy)
    category = _as_dict(category_prior)

    if action == "clarify_category_first":
        return _build_category_clarification_pending(
            confidence_policy=policy,
            category_prior=category,
            session_id=session_id,
            mode=mode,
        )
    if action == "clarify_requirement_first":
        built = _build_requirement_clarification_pending(
            confidence_policy=policy,
            clarification_policy=clarification,
            session_id=session_id,
            mode=mode,
        )
        return built or pending_contract
    if action == "defer_to_canvas":
        return _build_canvas_defer_pending(
            confidence_policy=policy,
            clarification_policy=clarification,
            session_id=session_id,
            mode=mode,
        )

    return pending_contract
