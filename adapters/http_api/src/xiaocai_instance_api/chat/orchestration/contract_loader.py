from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from xiaocai_instance_api.settings import get_settings


@dataclass(frozen=True)
class OrchestrationContracts:
    stage_order: list[str]
    stage_required: dict[str, list[str]]
    sourcing_required_fields: list[str]
    rfx_allowed_types: list[str]
    rfx_template_required: dict[str, list[str]]


@dataclass(frozen=True)
class PackMountSnapshot:
    domain_packs_root: str


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _extract_list_block(text: str, key_name: str) -> list[str]:
    lines = text.splitlines()
    target_prefix = f"{key_name}:"
    start = -1
    base_indent = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped == target_prefix:
            start = idx + 1
            base_indent = _line_indent(line)
            break
    if start < 0:
        return []

    values: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped:
            continue
        indent = _line_indent(line)
        if indent <= base_indent and not stripped.startswith("- "):
            break
        if stripped.startswith("- "):
            values.append(stripped[2:].strip().strip("'").strip('"'))
    return values


def _extract_nested_list_block(text: str, parent_key: str, child_key: str) -> list[str]:
    lines = text.splitlines()
    parent_prefix = f"{parent_key}:"
    child_prefix = f"{child_key}:"
    in_parent = False
    parent_indent = 0
    child_indent = 0
    in_child = False
    values: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        indent = _line_indent(line)
        if not in_parent:
            if stripped == parent_prefix:
                in_parent = True
                parent_indent = indent
            continue
        if indent <= parent_indent and not stripped.startswith("- "):
            break
        if not in_child and stripped == child_prefix:
            in_child = True
            child_indent = indent
            continue
        if in_child:
            if indent <= child_indent and not stripped.startswith("- "):
                break
            if stripped.startswith("- "):
                values.append(stripped[2:].strip().strip("'").strip('"'))

    return values


def _extract_rfx_template_required(text: str) -> dict[str, list[str]]:
    lines = text.splitlines()
    mapping: dict[str, list[str]] = {}
    current_type: str | None = None
    in_required = False
    required_indent = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        indent = _line_indent(line)
        if stripped.startswith("- type:"):
            current_type = stripped.split(":", 1)[1].strip().strip("'").strip('"')
            mapping.setdefault(current_type, [])
            in_required = False
            continue
        if current_type and stripped == "required_fields:":
            in_required = True
            required_indent = indent
            continue
        if in_required:
            if indent <= required_indent and not stripped.startswith("- "):
                in_required = False
                continue
            if stripped.startswith("- "):
                mapping[current_type].append(stripped[2:].strip().strip("'").strip('"'))
    return mapping


def _resolve_domain_packs_root() -> Path:
    settings = get_settings()
    raw_root = Path(settings.flare_domain_pack_root).expanduser()
    candidates = [
        raw_root,
        raw_root / "domain-packs",
        raw_root.parent / "domain-packs",
    ]
    for candidate in candidates:
        if (candidate / "schema" / "procurement.yaml").exists():
            return candidate
    return raw_root / "domain-packs"


@lru_cache(maxsize=1)
def load_pack_mount_snapshot() -> PackMountSnapshot:
    root = _resolve_domain_packs_root()
    return PackMountSnapshot(domain_packs_root=str(root))


@lru_cache(maxsize=1)
def load_contracts() -> OrchestrationContracts:
    # 当前运行统一基于 domain-packs contract。
    _ = load_pack_mount_snapshot()

    root = _resolve_domain_packs_root()
    schema_text = (root / "schema" / "procurement.yaml").read_text(encoding="utf-8")
    workflow_text = (root / "workflows" / "procurement-workflow-nodes.yaml").read_text(encoding="utf-8")
    sourcing_text = (root / "contracts" / "procurement-search-sourcing-replace.yaml").read_text(encoding="utf-8")
    analysis_rfx_text = (root / "contracts" / "procurement-analysis-rfx-templates.yaml").read_text(encoding="utf-8")

    stage_required = {
        "requirement-collection": _extract_nested_list_block(schema_text, "stage_field_sets", "需求梳理必填集"),
        "requirement-analysis": _extract_nested_list_block(schema_text, "stage_field_sets", "需求分析必填集"),
        "rfx-strategy": _extract_nested_list_block(schema_text, "stage_field_sets", "RFX策略必填集"),
    }

    return OrchestrationContracts(
        stage_order=_extract_list_block(workflow_text, "stage_order"),
        stage_required=stage_required,
        sourcing_required_fields=_extract_nested_list_block(sourcing_text, "sourcing_rules", "required_requirement_fields"),
        rfx_allowed_types=_extract_nested_list_block(analysis_rfx_text, "rfx_templates", "allowed_types"),
        rfx_template_required=_extract_rfx_template_required(analysis_rfx_text),
    )
