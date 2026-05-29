from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
from typing import Any

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


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _to_text(value: object) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _resolve_domain_packs_root() -> Path:
    settings = get_settings()
    raw_root = Path(settings.flare_domain_pack_root).expanduser()
    candidates = [
        raw_root,
        raw_root / "domain-packs",
        raw_root.parent / "domain-packs",
    ]
    for candidate in candidates:
        if (candidate / "xiaocai" / "workflow.yaml").exists():
            return candidate
    return raw_root / "domain-packs"


def _field_metadata(fields_data: dict[str, Any]) -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    for item in _as_list(fields_data.get("field_definitions")):
        if not isinstance(item, dict):
            continue
        key = _to_text(item.get("key")) or _to_text(item.get("label"))
        if not key:
            continue
        metadata[key] = {
            str(name): str(value)
            for name, value in item.items()
            if isinstance(name, str) and isinstance(value, (str, int, float, bool))
        }
    for key, item in (fields_data.get("field_semantics") or {}).items():
        field_key = _to_text(key)
        if not field_key or not isinstance(item, dict):
            continue
        current = dict(metadata.get(field_key, {}))
        current.update({
            str(name): str(value)
            for name, value in item.items()
            if isinstance(name, str) and isinstance(value, (str, int, float, bool))
        })
        current.setdefault("key", field_key)
        current.setdefault("label", field_key)
        metadata[field_key] = current
    return metadata


def _field_aliases(fields_data: dict[str, Any]) -> dict[str, dict[str, object]]:
    aliases = fields_data.get("field_aliases")
    if not isinstance(aliases, list):
        return {}
    result: dict[str, dict[str, object]] = {}
    for item in aliases:
        if not isinstance(item, dict):
            continue
        external_name = _to_text(item.get("external_name"))
        if external_name:
            result[external_name] = dict(item)
    return result


def _category_options(taxonomy_data: dict[str, Any]) -> tuple[list[str], list[str]]:
    categories = taxonomy_data.get("procurement_categories")
    if not isinstance(categories, dict):
        return [], []
    level1 = [_to_text(key) for key in categories.keys()]
    level2: list[str] = []
    seen: set[str] = set()
    for children in categories.values():
        if not isinstance(children, dict):
            continue
        for key in children.keys():
            value = _to_text(key)
            if value and value not in seen:
                seen.add(value)
                level2.append(value)
    return [item for item in level1 if item], level2


def _module_required(fields_data: dict[str, Any], module_name: str) -> list[str]:
    module_sets = fields_data.get("module_field_sets")
    if not isinstance(module_sets, dict):
        return []
    module = module_sets.get(module_name)
    if not isinstance(module, dict):
        return []
    return [_to_text(item) for item in _as_list(module.get("required_fields")) if _to_text(item)]


def _workflow_required(workflow_data: dict[str, Any], key: str) -> list[str]:
    policy = workflow_data.get("blocker_policies")
    if not isinstance(policy, dict):
        return []
    return [_to_text(item) for item in _as_list(policy.get(key)) if _to_text(item)]


def _stage_required(fields_data: dict[str, Any], workflow_data: dict[str, Any]) -> dict[str, list[str]]:
    intake_required = (
        _workflow_required(workflow_data, "required_fields")
        + _workflow_required(workflow_data, "confirmation_fields")
    )
    return {
        "requirement-collection": intake_required,
        "requirement-analysis": _module_required(fields_data, "需求分析"),
        "rfx-strategy": _module_required(fields_data, "RFX策略"),
    }


def _rfx_template_required(fields_data: dict[str, Any]) -> dict[str, list[str]]:
    required = _module_required(fields_data, "RFX策略")
    return {"default": required} if required else {}


@lru_cache(maxsize=1)
def load_pack_mount_snapshot() -> PackMountSnapshot:
    root = _resolve_domain_packs_root()
    return PackMountSnapshot(domain_packs_root=str(root))


@lru_cache(maxsize=1)
def load_contracts() -> OrchestrationContracts:
    root = _resolve_domain_packs_root()
    xiaocai_root = root / "xiaocai"
    fields_data = _read_json(xiaocai_root / "fields.yaml")
    workflow_data = _read_json(xiaocai_root / "workflow.yaml")
    taxonomy_data = _read_json(xiaocai_root / "taxonomy.yaml")
    level1_options, level2_options = _category_options(taxonomy_data)

    return OrchestrationContracts(
        stage_order=[
            "requirement-collection",
            "requirement-analysis",
            "rfx-strategy",
        ],
        stage_required=_stage_required(fields_data, workflow_data),
        sourcing_required_fields=_module_required(fields_data, "智能寻源"),
        rfx_allowed_types=[],
        rfx_template_required=_rfx_template_required(fields_data),
        field_metadata=_field_metadata(fields_data),
        field_aliases=_field_aliases(fields_data),
        category_level1_options=level1_options,
        category_level2_options=level2_options,
    )
