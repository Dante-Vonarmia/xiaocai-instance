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
    field_metadata: dict[str, dict[str, str]]
    field_aliases: dict[str, dict[str, object]]
    category_level1_options: list[str]
    category_level2_options: list[str]


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


def _extract_field_metadata(text: str) -> dict[str, dict[str, str]]:
    fields: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- 字段名称:"):
            key = stripped.split(":", 1)[1].strip().strip("'").strip('"')
            current = {"字段名称": key}
            fields[key] = current
            continue
        if current is None or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        current[key.strip()] = value.strip().strip("'").strip('"')

    return fields


def _extract_field_aliases(text: str) -> dict[str, dict[str, object]]:
    aliases: dict[str, dict[str, object]] = {}
    current: dict[str, object] | None = None
    in_aliases = False
    in_canonical_fields = False

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        indent = _line_indent(raw_line)
        if stripped == "field_aliases:":
            in_aliases = True
            continue
        if in_aliases and indent == 0 and not stripped.startswith("- "):
            break
        if not in_aliases:
            continue
        if stripped.startswith("- external_name:"):
            external_name = stripped.split(":", 1)[1].strip().strip("'").strip('"')
            current = {"external_name": external_name, "canonical_fields": []}
            aliases[external_name] = current
            in_canonical_fields = False
            continue
        if current is None:
            continue
        if stripped == "canonical_fields:":
            in_canonical_fields = True
            continue
        if in_canonical_fields and stripped.startswith("- "):
            current_fields = current.setdefault("canonical_fields", [])
            if isinstance(current_fields, list):
                current_fields.append(stripped[2:].strip().strip("'").strip('"'))
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        normalized_value = value.strip().strip("'").strip('"')
        current[key.strip()] = normalized_value
        in_canonical_fields = False

    return aliases


def _extract_category_options(text: str) -> tuple[list[str], list[str]]:
    level1: list[str] = []
    level2: list[str] = []
    seen_l1: set[str] = set()
    seen_l2: set[str] = set()
    in_owner_section = False

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "采购负责类:":
            in_owner_section = True
            continue
        if not in_owner_section:
            continue

        indent = _line_indent(raw_line)
        if indent == 6 and stripped.startswith("- 名称:"):
            value = stripped.split(":", 1)[1].strip().strip("'").strip('"')
            if value and value not in seen_l1:
                seen_l1.add(value)
                level1.append(value)
        if indent == 10 and stripped.startswith("- 名称:"):
            value = stripped.split(":", 1)[1].strip().strip("'").strip('"')
            if value and value != "/" and value not in seen_l2:
                seen_l2.add(value)
                level2.append(value)

    return level1, level2


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
    field_dictionary_text = (root / "schema" / "procurement-field-dictionary.yaml").read_text(encoding="utf-8")
    category_text = (root / "category-fields" / "procurement-category-fields.yaml").read_text(encoding="utf-8")
    workflow_text = (root / "workflows" / "procurement-workflow-nodes.yaml").read_text(encoding="utf-8")
    sourcing_text = (root / "contracts" / "procurement-search-sourcing-replace.yaml").read_text(encoding="utf-8")
    analysis_rfx_text = (root / "contracts" / "procurement-analysis-rfx-templates.yaml").read_text(encoding="utf-8")
    category_level1_options, category_level2_options = _extract_category_options(category_text)

    stage_required = {
        "requirement-collection": _extract_nested_list_block(schema_text, "stage_field_sets", "需求梳理必填集"),
        "requirement-analysis": _extract_nested_list_block(schema_text, "stage_field_sets", "需求分析必填集"),
        "rfx-strategy": _extract_nested_list_block(schema_text, "stage_field_sets", "RFX策略必填集"),
    }

    return OrchestrationContracts(
        stage_order=_extract_list_block(workflow_text, "stage_order"),
        stage_required=stage_required,
        sourcing_required_fields=_extract_nested_list_block(
            sourcing_text,
            "sourcing_rules",
            "required_requirement_fields",
        ),
        rfx_allowed_types=_extract_nested_list_block(analysis_rfx_text, "rfx_templates", "allowed_types"),
        rfx_template_required=_extract_rfx_template_required(analysis_rfx_text),
        field_metadata=_extract_field_metadata(field_dictionary_text),
        field_aliases=_extract_field_aliases(field_dictionary_text),
        category_level1_options=category_level1_options,
        category_level2_options=category_level2_options,
    )
