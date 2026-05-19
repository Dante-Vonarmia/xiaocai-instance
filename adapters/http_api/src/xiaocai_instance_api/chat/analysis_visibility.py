"""User-visible sanitization for analysis projection payloads."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


INTERNAL_LINE_TERMS = (
    "produce_output",
    "workflow",
    "node_",
    "debug",
    "pending_contract",
    "next_actions",
    "analysis_payload",
    "artifact_template_result",
    "response_strategy_result",
    "module_prompt_registry",
    "session_id",
    "trace_id",
)


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _to_text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _contains_internal_line_term(line: str) -> bool:
    lowered = line.lower()
    return any(term in lowered for term in INTERNAL_LINE_TERMS)


def sanitize_visible_text(text: str) -> str:
    normalized = _to_text(text)
    if not normalized:
        return ""
    replacements = (
        ("produce_output", "生成分析报告"),
        ("当前步骤", "当前建议"),
        ("最终目标", "交付目标"),
        ("任务推进状态", "执行状态"),
        ("正文/结构", "正文结构"),
    )
    for source, target in replacements:
        normalized = normalized.replace(source, target)
    lines = [line for line in normalized.splitlines() if not _contains_internal_line_term(line)]
    return "\n".join(lines).strip()


def _sanitize_section(section: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(section)
    sanitized["title"] = sanitize_visible_text(_to_text(section.get("title")))
    sanitized["content"] = sanitize_visible_text(_to_text(section.get("content")))
    info = [sanitize_visible_text(_to_text(item)) for item in _as_list(section.get("info"))]
    sanitized["info"] = [item for item in info if item]
    return sanitized


def sanitize_analysis_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = deepcopy(payload)
    sanitized["markdown"] = sanitize_visible_text(_to_text(sanitized.get("markdown")))
    document = _as_dict(sanitized.get("document"))
    summary = _as_dict(document.get("summary"))
    for key in ("problem", "judgement", "recommendation", "rationale"):
        summary[key] = sanitize_visible_text(_to_text(summary.get(key)))
    document["summary"] = summary
    document["sections"] = [_sanitize_section(_as_dict(item)) for item in _as_list(document.get("sections"))]

    next_steps: list[dict[str, Any]] = []
    for item in _as_list(document.get("next_steps")):
        record = dict(_as_dict(item))
        record["label"] = sanitize_visible_text(_to_text(record.get("label")))
        next_steps.append(record)
    document["next_steps"] = next_steps
    sanitized["document"] = document
    return sanitized
