from __future__ import annotations

import re
from typing import Any


HEADING_PATTERN = re.compile(r"^(#{1,4})\s+(.+?)\s*$")
MAX_STRUCTURE_HEADINGS = 24
STRUCTURED_REASONING_CANVAS_REASON = "structured_reasoning_artifact_document"


def _object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _artifact_document_from_event(event: dict[str, Any]) -> dict[str, Any]:
    payload = _object(event.get("payload"))
    structured_reasoning = _object(payload.get("structured_reasoning") or event.get("structured_reasoning"))
    return _object(structured_reasoning.get("artifact_document"))


def _markdown_headings(content: str) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    for line in content.splitlines():
        match = HEADING_PATTERN.match(line.strip())
        if not match:
            continue
        label = match.group(2).strip().strip("#").strip()
        if label:
            headings.append({"level": len(match.group(1)), "label": label})
        if len(headings) >= MAX_STRUCTURE_HEADINGS:
            break
    return headings


def _structure_id(index: int, label: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", label).strip("-")
    return f"section:{index}:{normalized or 'item'}"


def _document_structure(title: str, content: str) -> dict[str, Any]:
    headings = _markdown_headings(content)
    if headings and headings[0]["label"] == title:
        headings = headings[1:]
    root = {"id": "root", "label": title or "采购需求文档", "type": "requirement_document"}
    if not headings:
        return {"root": root, "branches": []}

    base_level = min(int(item["level"]) for item in headings)
    branches: list[dict[str, Any]] = []
    current_branch: dict[str, Any] | None = None
    for index, heading in enumerate(headings):
        label = _text(heading.get("label"))
        node = {"id": _structure_id(index, label), "label": label, "type": "section"}
        if int(heading.get("level") or 0) <= base_level:
            current_branch = {**node, "nodes": []}
            branches.append(current_branch)
            continue
        if current_branch is None:
            current_branch = {"id": "section:0:overview", "label": "需求结构", "type": "section", "nodes": []}
            branches.append(current_branch)
        current_branch["nodes"].append(node)
    return {"root": root, "branches": branches}


def _artifact_views() -> list[dict[str, Any]]:
    return [
        {"key": "smart_structure", "label": "需求结构", "kind": "derived_semantic_map", "default": True},
        {"key": "document", "label": "原文", "kind": "markdown", "default": False},
    ]


def _workspace_capabilities() -> dict[str, Any]:
    return {"artifact_views": _artifact_views()}


def build_structured_reasoning_canvas_event(event: dict[str, Any]) -> dict[str, Any] | None:
    """Project FLARE structured reasoning output into xiaocai canvas state.

    FLARE owns the reasoning event. xiaocai only adds the product workbench
    projection required by the local canvas/view contract.
    """
    artifact_document = _artifact_document_from_event(event)
    artifact_type = _text(artifact_document.get("artifact_type"))
    content = _text(artifact_document.get("content"))
    if artifact_type != "requirements_document" or not content:
        return None

    title = _text(artifact_document.get("title")) or "采购需求整理"
    run_id = _text(event.get("run_id"))
    session_id = _text(event.get("session_id"))
    artifact_id = _text(artifact_document.get("artifact_id")) or f"artifact::requirement_intake::{session_id or run_id or 'latest'}"
    semantic_map = {
        "status": "ready",
        "source": STRUCTURED_REASONING_CANVAS_REASON,
        "tree": _document_structure(title, content),
    }
    revision = {
        "version": artifact_document.get("version") or 1,
        "active_tab": "requirement",
        "content": content,
        "status": "accepted",
        "accepted": True,
        "diff": "model_generated",
        "source_kind": STRUCTURED_REASONING_CANVAS_REASON,
    }
    projected_document = {
        **artifact_document,
        "kind": "ArtifactDocument",
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "title": title,
        "active_tab": "requirement",
        "content": content,
        "content_format": _text(artifact_document.get("content_format")) or "markdown",
        "semantic_map": semantic_map,
        "latest_revision": revision,
    }
    capabilities = _workspace_capabilities()
    canvas_state = {
        "active_tab": "requirement",
        "artifact_document": projected_document,
        "versions": [revision],
        "workspace_capabilities": capabilities,
    }
    return {
        "type": "canvas_state",
        "mode_key": "requirement_intake",
        "run_id": run_id,
        "session_id": session_id,
        "artifact_document": projected_document,
        "canvas_state": canvas_state,
        "workspace_capabilities": capabilities,
        "ui_signal": {
            "open_canvas_panel": True,
            "active_tab": "requirement",
            "reason": STRUCTURED_REASONING_CANVAS_REASON,
        },
    }
