from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status

from xiaocai_instance_api.settings import get_settings


router = APIRouter(prefix="/v1/domains", tags=["domains"])


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _resolve_domain_packs_root() -> Path:
    settings = get_settings()
    raw_root = Path(settings.flare_domain_pack_root).expanduser()
    candidates = [
        raw_root,
        raw_root / "domain-packs",
        raw_root.parent / "domain-packs",
    ]
    for candidate in candidates:
        if (candidate / "xiaocai" / "fields.yaml").exists():
            return candidate
        if (candidate / "activity_procurement" / "fields.yaml").exists():
            return candidate
    return raw_root / "domain-packs"


def _parse_inline_list(value: str) -> list[str]:
    text = value.strip()
    if not (text.startswith("[") and text.endswith("]")):
        return []
    inner = text[1:-1].strip()
    if not inner:
        return []
    return [item.strip().strip("'").strip('"') for item in inner.split(",") if item.strip()]


def _parse_activity_fields_yaml(text: str) -> dict[str, Any]:
    pack_id = ""
    version = ""
    groups: dict[str, list[dict[str, Any]]] = {
        "required": [],
        "recommended": [],
        "optional": [],
    }

    current_group = ""
    current_item: dict[str, Any] | None = None

    lines = text.splitlines()
    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("pack_id:"):
            pack_id = stripped.split(":", 1)[1].strip().strip("'").strip('"')
            continue
        if stripped.startswith("version:"):
            version = stripped.split(":", 1)[1].strip().strip("'").strip('"')
            continue

        indent = _line_indent(line)

        if indent == 2 and stripped.endswith(":"):
            key = stripped[:-1].strip()
            if key in groups:
                current_group = key
                current_item = None
            continue

        if not current_group:
            continue

        if indent == 4 and stripped.startswith("- key:"):
            key_value = stripped.split(":", 1)[1].strip().strip("'").strip('"')
            current_item = {
                "key": key_value,
                "label": "",
                "type": "",
                "required_level": current_group,
                "description": "",
                "options": [],
                "example_values": [],
            }
            groups[current_group].append(current_item)
            continue

        if current_item is None or ":" not in stripped:
            continue

        field_name, field_value = stripped.split(":", 1)
        field_name = field_name.strip()
        field_value = field_value.strip()

        if field_name in {"label", "type", "required_level", "description"}:
            current_item[field_name] = field_value.strip("'").strip('"')
        elif field_name in {"options", "example_values"}:
            current_item[field_name] = _parse_inline_list(field_value)

    flat_fields: list[dict[str, Any]] = []
    for group_name in ("required", "recommended", "optional"):
        flat_fields.extend(groups[group_name])

    return {
        "domain": "procurement",
        "pack_id": pack_id or "activity_procurement",
        "version": version or "v1",
        "field_groups": groups,
        "fields": flat_fields,
    }


def _field_semantic_description(semantics: dict[str, Any]) -> str:
    meaning = semantics.get("business_meaning")
    standard = semantics.get("data_standard")
    parts = [str(item).strip() for item in (meaning, standard) if str(item or "").strip()]
    return "；".join(parts)


def _to_domain_field(
    definition: dict[str, Any],
    *,
    group_name: str,
    field_semantics: dict[str, Any],
) -> dict[str, Any]:
    key = str(definition.get("key") or "").strip()
    semantics = field_semantics.get(key)
    semantic_map = semantics if isinstance(semantics, dict) else {}
    example = str(semantic_map.get("example") or "").strip()
    options = definition.get("options")
    return {
        "key": key,
        "label": str(definition.get("label") or key).strip(),
        "type": str(semantic_map.get("value_type") or "string").strip(),
        "required_level": group_name,
        "description": _field_semantic_description(semantic_map)
        or str(definition.get("question") or "").strip(),
        "options": options if isinstance(options, list) else [],
        "example_values": [example] if example else [],
    }


def _parse_xiaocai_fields_yaml(text: str) -> dict[str, Any] | None:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(raw, dict):
        return None

    definitions = raw.get("field_definitions")
    if not isinstance(definitions, list):
        return None
    field_semantics = raw.get("field_semantics")
    semantic_map = field_semantics if isinstance(field_semantics, dict) else {}

    required = {str(item).strip() for item in raw.get("required_fields", []) if str(item).strip()}
    recommended = {str(item).strip() for item in raw.get("recommended_fields", []) if str(item).strip()}
    groups: dict[str, list[dict[str, Any]]] = {
        "required": [],
        "recommended": [],
        "optional": [],
    }
    for item in definitions:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        if not key:
            continue
        if key in required:
            group_name = "required"
        elif key in recommended:
            group_name = "recommended"
        else:
            group_name = "optional"
        groups[group_name].append(
            _to_domain_field(item, group_name=group_name, field_semantics=semantic_map)
        )

    flat_fields: list[dict[str, Any]] = []
    for group_name in ("required", "recommended", "optional"):
        flat_fields.extend(groups[group_name])

    return {
        "domain": "procurement",
        "pack_id": "xiaocai",
        "version": "default",
        "field_groups": groups,
        "fields": flat_fields,
    }


@lru_cache(maxsize=1)
def _load_procurement_fields_payload() -> dict[str, Any]:
    root = _resolve_domain_packs_root()
    xiaocai_fields_path = root / "xiaocai" / "fields.yaml"
    if xiaocai_fields_path.exists():
        parsed = _parse_xiaocai_fields_yaml(xiaocai_fields_path.read_text(encoding="utf-8"))
        if parsed is not None:
            return parsed

    fields_path = root / "activity_procurement" / "fields.yaml"
    if not fields_path.exists():
        return {
            "domain": "procurement",
            "pack_id": "activity_procurement",
            "version": "v1",
            "field_groups": {"required": [], "recommended": [], "optional": []},
            "fields": [],
        }
    text = fields_path.read_text(encoding="utf-8")
    return _parse_activity_fields_yaml(text)


@router.get("/{domain}/fields")
async def get_domain_fields(domain: str) -> dict[str, Any]:
    normalized = (domain or "").strip().lower()
    if normalized != "procurement":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="domain not found")
    return _load_procurement_fields_payload()
