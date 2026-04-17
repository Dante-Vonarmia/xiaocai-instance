#!/usr/bin/env python3
"""Validate xiaocai domain-packs (P0 minimal checks)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


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


def expect_keys(obj: dict[str, Any], keys: list[str], path: Path, errors: list[str]) -> None:
    for k in keys:
        if k not in obj:
            errors.append(f"{path}: missing required key '{k}'")


def build_field_set(common_fields: dict[str, Any], pack_fields: dict[str, Any], pack_name: str, errors: list[str]) -> set[str]:
    keys: list[str] = []

    common_list = common_fields.get("fields", [])
    if not isinstance(common_list, list):
        errors.append("shared common_fields.yaml: 'fields' must be list")
        common_list = []
    for f in common_list:
        if isinstance(f, dict) and f.get("key"):
            keys.append(str(f["key"]))

    field_groups = pack_fields.get("field_groups", {}) if isinstance(pack_fields, dict) else {}
    if not isinstance(field_groups, dict):
        errors.append(f"{pack_name} fields.yaml: 'field_groups' must be dict")
        field_groups = {}

    for bucket in ("required", "recommended", "optional"):
        group = field_groups.get(bucket, [])
        if not isinstance(group, list):
            errors.append(f"{pack_name} fields.yaml: field_groups.{bucket} must be list")
            continue
        for f in group:
            if isinstance(f, dict) and f.get("key"):
                keys.append(str(f["key"]))

    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        errors.append(f"{pack_name}: duplicate field keys found: {dup}")

    return set(keys)


def validate_question_flow(qf: dict[str, Any], field_keys: set[str], pack_name: str, errors: list[str]) -> None:
    expect_keys(
        qf,
        [
            "stage",
            "ask_order",
            "field_dependencies",
            "blocking_conditions",
            "followup_question_templates",
            "stop_asking_conditions",
            "fallback_defaults",
            "escalation_rules",
        ],
        Path(f"{pack_name}/question_flow.yaml"),
        errors,
    )

    ask_order = qf.get("ask_order", [])
    if isinstance(ask_order, list):
        for k in ask_order:
            if k not in field_keys:
                errors.append(f"{pack_name}/question_flow.yaml: ask_order field '{k}' not found in fields")

    deps = qf.get("field_dependencies", {})
    if isinstance(deps, dict):
        for k, vals in deps.items():
            if k not in field_keys:
                errors.append(f"{pack_name}/question_flow.yaml: dependency key '{k}' not in fields")
            if isinstance(vals, list):
                for v in vals:
                    if v not in field_keys:
                        errors.append(f"{pack_name}/question_flow.yaml: dependency '{k}->{v}' not in fields")


def validate_artifact_mapping(mapping: dict[str, Any], artifact_specs: dict[str, Any], pack_name: str, errors: list[str]) -> None:
    expect_keys(mapping, ["artifacts"], Path(f"{pack_name}/artifact_mapping.yaml"), errors)

    spec_list = artifact_specs.get("artifact_specs", []) if isinstance(artifact_specs, dict) else []
    spec_keys = {str(x.get("key")) for x in spec_list if isinstance(x, dict) and x.get("key")}

    artifacts = mapping.get("artifacts", [])
    if isinstance(artifacts, list):
        for item in artifacts:
            if not isinstance(item, dict):
                continue
            key = item.get("artifact_key")
            if key not in spec_keys:
                errors.append(f"{pack_name}/artifact_mapping.yaml: artifact_key '{key}' not in shared artifact_specs")


def validate_supplier_scorecard(scorecard: dict[str, Any], pack_name: str, errors: list[str]) -> None:
    expect_keys(
        scorecard,
        ["hard_gates", "bonus_items", "score_dimensions", "scoring_algorithm", "veto_items", "recommendation_levels"],
        Path(f"{pack_name}/supplier_scorecard.yaml"),
        errors,
    )

    dims = scorecard.get("score_dimensions", [])
    if not isinstance(dims, list) or not dims:
        errors.append(f"{pack_name}/supplier_scorecard.yaml: score_dimensions must be non-empty list")
        return

    for i, d in enumerate(dims):
        if not isinstance(d, dict):
            errors.append(f"{pack_name}/supplier_scorecard.yaml: score_dimensions[{i}] must be dict")
            continue
        for k in ("key", "label", "weight", "score_range"):
            if k not in d:
                errors.append(f"{pack_name}/supplier_scorecard.yaml: score_dimensions[{i}] missing '{k}'")


def validate_rfx_rules(rfx: dict[str, Any], errors: list[str]) -> None:
    expect_keys(rfx, ["input_signals", "decision_conditions", "thresholds"], Path("shared/rules/rfx_rules.yaml"), errors)
    cond = rfx.get("decision_conditions", [])
    actions = set()
    if isinstance(cond, list):
        for c in cond:
            if isinstance(c, dict) and c.get("recommended_action"):
                actions.add(str(c["recommended_action"]))
    missing = {"RFI", "RFP", "RFQ", "RFB"} - actions
    if missing:
        errors.append(f"shared/rules/rfx_rules.yaml: missing actions {sorted(missing)}")


def validate(root: Path) -> list[str]:
    errors: list[str] = []

    yaml_files = sorted(root.rglob("*.yaml"))
    parsed: dict[Path, Any] = {}
    for f in yaml_files:
        try:
            parsed[f] = load_yaml(f)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{f}: YAML parse error: {e}")

    # stop early if parse failed massively
    if errors:
        return errors

    shared_common = parsed[root / "shared" / "fields" / "common_fields.yaml"]
    shared_artifacts = parsed[root / "shared" / "artifacts" / "artifact_specs.yaml"]
    shared_rfx = parsed[root / "shared" / "rules" / "rfx_rules.yaml"]

    expect_keys(shared_common, ["fields"], root / "shared/fields/common_fields.yaml", errors)
    expect_keys(shared_artifacts, ["artifact_specs"], root / "shared/artifacts/artifact_specs.yaml", errors)

    validate_rfx_rules(shared_rfx, errors)

    # recommendation policy assets (TASK-DP-011)
    rec_rules = parsed.get(root / "shared" / "rules" / "template_recommendation_rules.yaml", {})
    rec_registry = parsed.get(root / "shared" / "rules" / "recommendation_policy_registry.yaml", {})
    rec_audit = parsed.get(root / "shared" / "artifacts" / "recommendation_audit_schema.yaml", {})

    expect_keys(rec_rules, ["rules"], root / "shared/rules/template_recommendation_rules.yaml", errors)
    if isinstance(rec_rules, dict) and isinstance(rec_rules.get("rules", []), list):
        for i, r in enumerate(rec_rules.get("rules", [])):
            if not isinstance(r, dict):
                errors.append(f"shared/rules/template_recommendation_rules.yaml: rules[{i}] must be dict")
                continue
            for k in ("rule_id", "scenario", "stage", "trigger_conditions", "weighted_candidates", "fallback_template"):
                if k not in r:
                    errors.append(f"shared/rules/template_recommendation_rules.yaml: rules[{i}] missing '{k}'")

    expect_keys(
        rec_registry,
        ["policy_id", "version", "status", "effective_at", "owner", "change_reason", "policy_defaults", "explanation_schema"],
        root / "shared/rules/recommendation_policy_registry.yaml",
        errors,
    )
    expect_keys(rec_audit, ["required_fields", "version"], root / "shared/artifacts/recommendation_audit_schema.yaml", errors)

    for pack in ("activity_procurement", "gift_customization"):
        fields_obj = parsed[root / pack / "fields.yaml"]
        qf_obj = parsed[root / pack / "question_flow.yaml"]
        score_obj = parsed[root / pack / "supplier_scorecard.yaml"]
        map_obj = parsed[root / pack / "artifact_mapping.yaml"]

        expect_keys(fields_obj, ["pack_id", "version", "field_groups"], root / f"{pack}/fields.yaml", errors)

        field_keys = build_field_set(shared_common, fields_obj, pack, errors)
        validate_question_flow(qf_obj, field_keys, pack, errors)
        validate_artifact_mapping(map_obj, shared_artifacts, pack, errors)
        validate_supplier_scorecard(score_obj, pack, errors)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate xiaocai domain-packs")
    parser.add_argument(
        "--root",
        default="domain-packs",
        help="domain-packs root path (default: domain-packs)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[FAIL] domain-packs root not found: {root}")
        return 1

    errors = validate(root)
    if errors:
        print("[FAIL] domain-packs validation errors:")
        for e in errors:
            print(f"- {e}")
        return 1

    print(f"[OK] domain-packs validation passed: {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
