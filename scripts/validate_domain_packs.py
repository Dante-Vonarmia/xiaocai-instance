#!/usr/bin/env python3
"""Validate the active xiaocai domain-pack only."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ACTIVE_PACK = "xiaocai"
EXPECTED_MODULES = {"requirement_intake", "analysis_mode"}
DISABLED_INTENT_ALIASES = {"寻源", "供应商"}


def _load_yaml_with_ruby(path: Path) -> Any:
    cmd = [
        "ruby",
        "-ryaml",
        "-rjson",
        "-e",
        "require 'date'; print JSON.generate(YAML.safe_load(File.read(ARGV[0]), permitted_classes: [Date, Time], aliases: true))",
        str(path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise ValueError(f"YAML parse failed via ruby: {res.stderr.strip()}")
    return json.loads(res.stdout)


def load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore

        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ModuleNotFoundError:
        return _load_yaml_with_ruby(path)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _field_names(fields: dict[str, Any]) -> set[str]:
    names = set(str(item) for item in _as_list(fields.get("required_fields")) if str(item).strip())
    names.update(str(item) for item in _as_list(fields.get("recommended_fields")) if str(item).strip())
    names.update(str(item) for item in _as_list(fields.get("optional_fields")) if str(item).strip())
    names.update(
        str(item.get("key"))
        for item in _as_list(fields.get("field_definitions"))
        if isinstance(item, dict) and str(item.get("key") or "").strip()
    )
    semantics = fields.get("field_semantics")
    if isinstance(semantics, dict):
        names.update(str(key) for key in semantics.keys())
    return names


def _collect_field_refs(workflow: dict[str, Any]) -> dict[str, list[Any]]:
    refs: dict[str, list[Any]] = {}
    blocker_policies = _as_dict(workflow.get("blocker_policies"))
    for key in ("required_fields", "confirmation_fields", "candidate_only_fields"):
        refs[f"blocker_policies.{key}"] = _as_list(blocker_policies.get(key))

    intake_strategy = _as_dict(workflow.get("intake_strategy"))
    for key in ("framework_fields", "candidate_fields", "pre_workspace_required_fields"):
        refs[f"intake_strategy.{key}"] = _as_list(intake_strategy.get(key))

    field_value_policy = _as_dict(workflow.get("field_value_policy"))
    question_policy = _as_dict(field_value_policy.get("question_policy"))
    refs["field_value_policy.question_policy.suppressed_question_fields"] = _as_list(
        question_policy.get("suppressed_question_fields")
    )
    for key in ("candidate_before_question_fields", "high_value_confirmation_fields"):
        refs[f"field_value_policy.{key}"] = _as_list(field_value_policy.get(key))

    for key, values in _as_dict(field_value_policy.get("field_value_roles")).items():
        if key == "adapter_authoritative_when_available":
            continue
        refs[f"field_value_policy.field_value_roles.{key}"] = _as_list(values)

    for key, values in _as_dict(workflow.get("analysis_slot_field_mapping")).items():
        refs[f"analysis_slot_field_mapping.{key}"] = _as_list(values)
    return refs


def _validate_required_files(pack_root: Path, errors: list[str]) -> None:
    required = [
        "fields.yaml",
        "workflow.yaml",
        "taxonomy.yaml",
        "replace-rules.yaml",
        "search-mapping.yaml",
        "templates/requirements-document.md",
        "templates/analysis.md",
    ]
    for item in required:
        if not (pack_root / item).exists():
            errors.append(f"{ACTIVE_PACK}: missing required file {item}")


def _validate_fields(fields: dict[str, Any], errors: list[str]) -> None:
    definitions = _as_list(fields.get("field_definitions"))
    keys = [str(item.get("key")) for item in definitions if isinstance(item, dict) and item.get("key")]
    if len(definitions) != 81:
        errors.append(f"xiaocai fields.yaml: expected 81 field_definitions, got {len(definitions)}")
    if len(keys) != len(set(keys)):
        errors.append("xiaocai fields.yaml: duplicate field_definitions keys")
    if len(_as_list(fields.get("required_fields"))) != 14:
        errors.append("xiaocai fields.yaml: required_fields count must be 14")


def _validate_taxonomy(taxonomy: dict[str, Any], errors: list[str]) -> None:
    aliases = _as_dict(taxonomy.get("intent_aliases"))
    for key in sorted(DISABLED_INTENT_ALIASES):
        if key in aliases:
            errors.append(f"xiaocai taxonomy.yaml: '{key}' must not alias to intelligent_sourcing")
    if not _as_dict(taxonomy.get("procurement_categories")):
        errors.append("xiaocai taxonomy.yaml: procurement_categories must be non-empty")


def _validate_workflow(workflow: dict[str, Any], fields: dict[str, Any], pack_root: Path, errors: list[str]) -> None:
    defined_fields = _field_names(fields)
    for path, values in _collect_field_refs(workflow).items():
        missing = [str(field) for field in values if str(field) not in defined_fields]
        if missing:
            errors.append(f"xiaocai workflow.yaml: {path} references undefined fields {missing}")

    registry = {
        item.get("module_key"): item
        for item in _as_list(workflow.get("module_prompt_registry"))
        if isinstance(item, dict) and item.get("module_key")
    }
    if set(registry) != EXPECTED_MODULES:
        errors.append(f"xiaocai workflow.yaml: module_prompt_registry must be {sorted(EXPECTED_MODULES)}")

    artifact_templates = _as_dict(workflow.get("artifact_templates"))
    for key, template in artifact_templates.items():
        if not isinstance(template, dict):
            continue
        template_file = template.get("template")
        if isinstance(template_file, str) and template_file and not (pack_root / "templates" / template_file).exists():
            errors.append(f"xiaocai workflow.yaml: artifact_templates.{key} missing template {template_file}")


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    pack_root = root / ACTIVE_PACK
    _validate_required_files(pack_root, errors)
    if errors:
        return errors

    try:
        fields = load_yaml(pack_root / "fields.yaml")
        workflow = load_yaml(pack_root / "workflow.yaml")
        taxonomy = load_yaml(pack_root / "taxonomy.yaml")
    except Exception as exc:  # noqa: BLE001
        return [f"xiaocai domain-pack parse failed: {exc}"]

    _validate_fields(_as_dict(fields), errors)
    _validate_taxonomy(_as_dict(taxonomy), errors)
    _validate_workflow(_as_dict(workflow), _as_dict(fields), pack_root, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate active xiaocai domain-pack")
    parser.add_argument("--root", default="domain-packs", help="domain-packs root path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[FAIL] domain-packs root not found: {root}")
        return 1

    errors = validate(root)
    if errors:
        print("[FAIL] xiaocai domain-pack validation errors:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"[OK] active xiaocai domain-pack validation passed: {root / ACTIVE_PACK}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
