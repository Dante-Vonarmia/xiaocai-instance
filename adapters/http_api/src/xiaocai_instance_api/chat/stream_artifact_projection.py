"""Project FLARE stream artifacts onto the canvas_state stream contract."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _first_text(*values: Any) -> str:
    for value in values:
        resolved = _text(value)
        if resolved:
            return resolved
    return ""


def _field_item(field_key: str, payload: dict[str, Any], *, status: str) -> dict[str, Any]:
    value = payload.get("value", payload.get("normalized_value"))
    return {
        "field_key": field_key,
        "key": field_key,
        "label": _first_text(payload.get("label"), field_key),
        "value": value,
        "display_value": _text(value),
        "status": status,
        "confidence": payload.get("confidence"),
        "needs_confirmation": payload.get("needs_confirmation") is True,
    }


def _confirmed_from_structured_reasoning(reasoning: dict[str, Any]) -> list[dict[str, Any]]:
    node_fields = _as_dict(_as_dict(reasoning.get("node_result")).get("confirmed_fields"))
    if node_fields:
        return [
            _field_item(field_key, _as_dict(payload), status="confirmed")
            for field_key, payload in node_fields.items()
            if _text(_as_dict(payload).get("value"))
        ]

    extraction_fields = _as_list(_as_dict(reasoning.get("field_extraction")).get("confirmed_fields"))
    return [
        _field_item(_text(item.get("field_key")), _as_dict(item), status="confirmed")
        for item in extraction_fields
        if isinstance(item, dict) and _text(item.get("field_key")) and _text(item.get("value"))
    ]


def _missing_from_structured_reasoning(reasoning: dict[str, Any]) -> list[dict[str, Any]]:
    patches = _as_list(_as_dict(reasoning.get("field_extraction")).get("field_state_patches"))
    missing: list[dict[str, Any]] = []
    for item in patches:
        payload = _as_dict(item)
        field_key = _text(payload.get("field_key"))
        if not field_key or _text(payload.get("value")):
            continue
        missing.append(_field_item(field_key, payload, status="missing"))
    return missing


def _question_texts(reasoning: dict[str, Any]) -> list[str]:
    planner = _as_dict(reasoning.get("question_planner"))
    questions = [
        _text(_as_dict(planner.get("next_question")).get("question_text")),
        *[
            _text(_as_dict(item).get("question_text"))
            for item in _as_list(planner.get("question_plan"))
        ],
    ]
    gaps = [
        _text(_as_dict(item).get("reason"))
        for item in _as_list(_as_dict(reasoning.get("gap_detection")).get("candidate_information_gaps"))
    ]
    seen: set[str] = set()
    result: list[str] = []
    for item in [*questions, *gaps]:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _fields_by_group(structured_package: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in _as_list(structured_package.get("fields")):
        payload = _as_dict(item)
        group_key = _text(payload.get("group_key")) or "default"
        grouped.setdefault(group_key, []).append(payload)
    return grouped


def _procurement_packages(structured_package: dict[str, Any]) -> list[dict[str, Any]]:
    grouped_fields = _fields_by_group(structured_package)
    packages: list[dict[str, Any]] = []
    for index, group in enumerate(_as_list(structured_package.get("field_groups"))):
        item = _as_dict(group)
        group_key = _text(item.get("key")) or f"group_{index + 1}"
        fields = grouped_fields.get(group_key, [])
        missing = [
            _first_text(field.get("label"), field.get("field_key"))
            for field in fields
            if not _text(field.get("value"))
        ]
        confirmed = [
            f"{_first_text(field.get('label'), field.get('field_key'))}：{_text(field.get('value'))}"
            for field in fields
            if _text(field.get("value"))
        ]
        packages.append({
            "package_id": group_key,
            "title": _first_text(item.get("label"), group_key),
            "scope": "；".join(confirmed[:3]),
            "open_questions": [value for value in missing if value],
            "requirement_fields": [value for value in missing if value],
        })
    return [item for item in packages if item["title"]]


def _merge_artifact_document(
    base: dict[str, Any],
    incoming: dict[str, Any],
    structured_package: dict[str, Any],
) -> dict[str, Any]:
    content = _first_text(incoming.get("content"), base.get("content"))
    packages = _as_list(incoming.get("procurement_packages")) or _as_list(base.get("procurement_packages"))
    packages = packages or _procurement_packages(structured_package)
    return {
        **base,
        **incoming,
        "title": _first_text(incoming.get("title"), base.get("title"), "需求梳理"),
        "artifact_type": _first_text(
            incoming.get("artifact_type"),
            base.get("artifact_type"),
            "requirements_document",
        ),
        "content": content,
        "content_format": _first_text(incoming.get("content_format"), base.get("content_format"), "markdown"),
        "sections": _as_list(incoming.get("sections")) or _as_list(base.get("sections")),
        "procurement_packages": packages,
        "missing_questions": _as_list(incoming.get("missing_questions")) or _as_list(base.get("missing_questions")),
        "open_questions": _as_list(incoming.get("open_questions")) or _as_list(base.get("open_questions")),
    }


def _revision_for(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "active_tab": "requirement",
        "content": _text(document.get("content")),
        "content_format": _first_text(document.get("content_format"), "markdown"),
        "source": "structured_reasoning",
        "status": "accepted",
    }


class StreamArtifactProjector:
    """Stateful stream contract bridge for one FLARE response."""

    def __init__(self) -> None:
        self._latest_canvas_state: dict[str, Any] = {}
        self._latest_structured_package: dict[str, Any] = {}

    def project(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        event_type = _text(event.get("type"))
        payload = _as_dict(event.get("payload"))
        if event_type == "canvas_state":
            canvas_state = _as_dict(event.get("canvas_state")) or _as_dict(payload.get("canvas_state"))
            if canvas_state:
                self._latest_canvas_state = deepcopy(canvas_state)
            return []
        if event_type == "structured_package":
            structured_package = _as_dict(event.get("structured_package")) or _as_dict(payload.get("structured_package"))
            if structured_package:
                self._latest_structured_package = deepcopy(structured_package)
            return []

        reasoning = _as_dict(payload.get("structured_reasoning"))
        artifact_document = _as_dict(reasoning.get("artifact_document"))
        if event_type != "patch_event" or not artifact_document:
            return []

        canvas_state = self._build_canvas_state(reasoning=reasoning, artifact_document=artifact_document)
        self._latest_canvas_state = deepcopy(canvas_state)
        return [self._canvas_state_event(event, canvas_state)]

    def _build_canvas_state(
        self,
        *,
        reasoning: dict[str, Any],
        artifact_document: dict[str, Any],
    ) -> dict[str, Any]:
        canvas_state = deepcopy(self._latest_canvas_state)
        document = _merge_artifact_document(
            _as_dict(canvas_state.get("artifact_document")),
            artifact_document,
            self._latest_structured_package,
        )
        confirmed = _confirmed_from_structured_reasoning(reasoning) or _as_list(canvas_state.get("collected"))
        missing = _missing_from_structured_reasoning(reasoning) or _as_list(canvas_state.get("missing"))
        questions = _question_texts(reasoning)
        if questions:
            document["missing_questions"] = questions
            document["open_questions"] = questions
        total = len(confirmed) + len(missing)
        progress = (len(confirmed) / total) if total else canvas_state.get("progress", 0)
        return {
            **canvas_state,
            "artifact_document": document,
            "collected": confirmed,
            "missing": missing,
            "progress": progress,
            "current_question": _as_dict(_as_dict(reasoning.get("question_planner")).get("next_question")),
            "question_plan": _as_list(_as_dict(reasoning.get("question_planner")).get("question_plan")),
            "next_actions": _as_list(_as_dict(reasoning.get("node_result")).get("next_actions"))
                or _as_list(canvas_state.get("next_actions")),
            "versions": [*_as_list(canvas_state.get("versions")), _revision_for(document)],
        }

    def _canvas_state_event(self, source_event: dict[str, Any], canvas_state: dict[str, Any]) -> dict[str, Any]:
        payload = _as_dict(source_event.get("payload"))
        mode_key = _first_text(payload.get("mode_key"), source_event.get("mode_key"), "requirement_intake")
        return {
            "type": "canvas_state",
            "mode_key": mode_key,
            "session_id": source_event.get("session_id") or payload.get("session_id"),
            "run_id": source_event.get("run_id") or payload.get("run_id"),
            "canvas_state": canvas_state,
            "payload": {
                "mode_key": mode_key,
                "canvas_state": canvas_state,
                "artifact_document": canvas_state.get("artifact_document"),
                "projection_source": "structured_reasoning",
            },
        }

