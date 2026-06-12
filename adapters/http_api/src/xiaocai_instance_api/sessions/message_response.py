"""Session message response projection."""

from __future__ import annotations


def message_response(item) -> dict:
    """Preserve FLARE message artifacts so history reload keeps workbench state."""
    plan_payload = item.plan_payload if isinstance(item.plan_payload, dict) else None
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
