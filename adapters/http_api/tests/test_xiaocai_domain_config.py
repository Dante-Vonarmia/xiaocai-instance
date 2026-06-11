import json
from pathlib import Path


DOMAIN_ROOT = Path(__file__).resolve().parents[3] / "domain-packs" / "xiaocai"


def _read_json(name: str) -> dict:
    data = json.loads((DOMAIN_ROOT / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _as_list(value):
    return value if isinstance(value, list) else []


def _field_names(fields: dict) -> set[str]:
    names = set(fields.get("required_fields", []))
    names.update(fields.get("recommended_fields", []))
    names.update(fields.get("optional_fields", []))
    names.update(
        item["key"]
        for item in fields.get("field_definitions", [])
        if isinstance(item, dict) and item.get("key")
    )
    semantics = fields.get("field_semantics")
    if isinstance(semantics, dict):
        names.update(semantics.keys())
    return names


def _collect_workflow_field_refs(workflow: dict) -> dict[str, list[str]]:
    refs: dict[str, list[str]] = {}
    blocker_policies = workflow.get("blocker_policies") or {}
    for key in ("required_fields", "confirmation_fields", "candidate_only_fields"):
        refs[f"blocker_policies.{key}"] = _as_list(blocker_policies.get(key))

    intake_strategy = workflow.get("intake_strategy") or {}
    for key in ("framework_fields", "candidate_fields", "pre_workspace_required_fields"):
        refs[f"intake_strategy.{key}"] = _as_list(intake_strategy.get(key))

    field_value_policy = workflow.get("field_value_policy") or {}
    question_policy = field_value_policy.get("question_policy") or {}
    refs["field_value_policy.question_policy.suppressed_question_fields"] = _as_list(
        question_policy.get("suppressed_question_fields")
    )
    for key in ("candidate_before_question_fields", "high_value_confirmation_fields"):
        refs[f"field_value_policy.{key}"] = _as_list(field_value_policy.get(key))

    for key, values in (field_value_policy.get("field_value_roles") or {}).items():
        if key == "adapter_authoritative_when_available":
            continue
        refs[f"field_value_policy.field_value_roles.{key}"] = _as_list(values)

    for key, values in (workflow.get("analysis_slot_field_mapping") or {}).items():
        refs[f"analysis_slot_field_mapping.{key}"] = _as_list(values)
    return refs


def test_xiaocai_workflow_references_defined_fields_only():
    fields = _read_json("fields.yaml")
    workflow = _read_json("workflow.yaml")
    defined = _field_names(fields)

    missing = {
        path: [field for field in values if field not in defined]
        for path, values in _collect_workflow_field_refs(workflow).items()
    }
    missing = {path: values for path, values in missing.items() if values}

    assert missing == {}


def test_xiaocai_artifact_templates_reference_existing_files_and_fields():
    fields = _read_json("fields.yaml")
    workflow = _read_json("workflow.yaml")
    defined = _field_names(fields)
    problems: list[str] = []

    for key, template in (workflow.get("artifact_templates") or {}).items():
        if not isinstance(template, dict):
            continue
        template_file = template.get("template")
        if template_file and not (DOMAIN_ROOT / "templates" / template_file).exists():
            problems.append(f"{key}: missing template {template_file}")
        for section in template.get("sections") or []:
            if not isinstance(section, dict):
                continue
            for field in section.get("fields") or []:
                if field not in defined:
                    problems.append(f"{key}.{section.get('key')}: undefined field {field}")

    assert problems == []


def test_xiaocai_taxonomy_matches_category_field_options():
    fields = _read_json("fields.yaml")
    taxonomy = _read_json("taxonomy.yaml")
    categories = taxonomy.get("procurement_categories")
    assert isinstance(categories, dict) and categories

    options_by_field = {}
    for item in fields.get("field_definitions") or []:
        if isinstance(item, dict) and item.get("key") in {"一级品类", "二级品类"}:
            options_by_field[item["key"]] = {
                option.get("value")
                for option in item.get("options", [])
                if isinstance(option, dict) and option.get("value")
            }

    assert set(categories.keys()) <= options_by_field["一级品类"]
    level2 = set()
    for children in categories.values():
        if isinstance(children, dict):
            level2.update(children.keys())
    assert level2 <= options_by_field["二级品类"]


def test_xiaocai_domain_pack_keeps_flare_pack_contract_markers():
    app_profile = _read_json("app-profile.json")
    fields = _read_json("fields.yaml")
    workflow = _read_json("workflow.yaml")
    taxonomy = _read_json("taxonomy.yaml")
    template = (DOMAIN_ROOT / "templates" / "requirements-document.md").read_text(
        encoding="utf-8"
    )
    registry = {
        item["module_key"]: item
        for item in workflow.get("module_prompt_registry", [])
        if isinstance(item, dict) and item.get("module_key")
    }

    assert len(fields["field_definitions"]) == 81
    assert "寻源" not in taxonomy["intent_aliases"]
    assert "供应商" not in taxonomy["intent_aliases"]
    assert app_profile["displayPolicy"]["showUserFooter"] is True
    assert app_profile["displayPolicy"]["showStarterScenarios"] is True
    assert app_profile["branding"]["themeTokens"]["appBg"] == "#ffffff"
    assert app_profile["branding"]["themeTokens"]["sidebarBg"] == "#faf5ff"
    assert app_profile["instanceProfile"]["ui_labels"]["empty_state_title"] == "欢迎来到小采"
    assert app_profile["instanceProfile"]["ui_labels"]["empty_state_description"] == "小采在手，采购不愁。"
    assert set(registry) == {"requirement_intake", "analysis_mode"}
    assert registry["analysis_mode"]["action_commands"] == [
        "generate_analysis",
        "confirm_plan",
    ]
    assert "需求梳理输出架构" in template
    assert "不要输出旧的状态进度块" in template


def test_requirement_intake_stage_actions_match_flare_pack_shape():
    workflow = _read_json("workflow.yaml")
    actions = {
        item["action_key"]: item
        for item in workflow["stages"]["requirement_intake"]["next_actions"]
        if isinstance(item, dict) and item.get("action_key")
    }

    assert set(actions) == {
        "continue_collection",
        "generate_analysis",
        "handoff_to_sourcing",
    }
    assert actions["continue_collection"] == {
        "action_key": "continue_collection",
        "label": "继续补充",
        "priority": 1,
    }
    assert actions["generate_analysis"] == {
        "action_key": "generate_analysis",
        "label": "生成需求分析",
        "priority": 2,
    }
    assert actions["handoff_to_sourcing"] == {
        "action_key": "handoff_to_sourcing",
        "label": "进入智能寻源",
        "target_mode": "intelligent_sourcing",
        "priority": 3,
        "status": "available",
        "reason": "可基于当前需求进入智能寻源，并显式保留待补充项。",
        "reason_ready": "当前需求清晰度已可支持智能寻源。",
        "reason_with_gaps": "可进入智能寻源，但会携带待补充字段与假设。",
        "description": "切换到候选匹配与风险摘要，缺口会作为假设或待确认项保留。",
    }
