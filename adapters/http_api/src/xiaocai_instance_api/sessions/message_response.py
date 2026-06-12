"""Session message response projection."""

from __future__ import annotations


def _compact_workflow_projection(value: object) -> dict | None:
    """Keep workflow state in message history without inlining bulky event logs."""
    if not isinstance(value, dict):
        return None
    run_events = value.get("run_events")
    compact = {
        key: item
        for key, item in value.items()
        if key not in {"run_events", "runEvents"}
    }
    if isinstance(run_events, list) and run_events:
        compact["run_events_count"] = len(run_events)
        compact["run_events_lazy"] = True
    return compact


def _compact_plan_payload(value: object) -> dict | None:
    """Project plan payload for history reload while keeping event details lazy."""
    if not isinstance(value, dict):
        return None
    compact = dict(value)
    workflow_projection = _compact_workflow_projection(compact.get("workflow_projection"))
    if workflow_projection is not None:
        compact["workflow_projection"] = workflow_projection
    return compact


def message_response(item) -> dict:
    """Preserve FLARE message artifacts so history reload keeps workbench state."""
    plan_payload = _compact_plan_payload(item.plan_payload)
    canvas_state = item.canvas_state if isinstance(item.canvas_state, dict) else None
    response = {
        "message_id": item.message_id,
        "role": item.role,
        "content": item.content,
        "created_at": item.created_at,
        "run_id": item.run_id,
        "attachments": item.attachments,
        "context_refs": item.context_refs,
        "knowledge_refs": item.knowledge_refs,
        "agent_status": item.agent_status,
        "thinking_trace": item.thinking_trace,
        "execution_trace": item.execution_trace,
        "knowledge_search": item.knowledge_search,
        "sourcing_candidates": item.sourcing_candidates,
        "knowledge_citation": item.knowledge_citation,
        "canvas_state": canvas_state,
        "analysis_payload": item.analysis_payload,
        "context_usage": item.context_usage,
        "provider_trace": item.provider_trace,
        "context_authority": item.context_authority,
        "plan_payload": plan_payload,
    }
    if plan_payload and isinstance(plan_payload.get("workflow_projection"), dict):
        response["workflow_projection"] = plan_payload["workflow_projection"]
    if plan_payload and isinstance(plan_payload.get("track_result"), dict):
        response["track_result"] = plan_payload["track_result"]
    if canvas_state and isinstance(canvas_state.get("artifact_edit_request"), dict):
        response["artifact_edit_request"] = canvas_state["artifact_edit_request"]
    return response
