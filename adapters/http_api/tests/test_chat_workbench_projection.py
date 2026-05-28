from xiaocai_instance_api.chat.router import _has_usable_canvas_state_event
from xiaocai_instance_api.chat.workbench_projection import build_intake_workbench_projection


def test_router_recognizes_flare_native_canvas_state_as_usable():
    event = {
        "type": "canvas_state",
        "canvas_state": {
            "progress": 1.0,
            "current_question": {
                "field_key": "use_case",
                "question_text": "主要使用场景是什么？",
                "options": [{"label": "AI 模型训练", "value": "ai_training"}],
            },
        },
    }

    assert _has_usable_canvas_state_event(event) is True


def test_intake_workbench_projection_outputs_canvas_state():
    projection = build_intake_workbench_projection(
        pending_contract={
            "current_stage": "clarify_requirement",
            "missing_fields": ["采购目的"],
            "confirmed_fields": {"预算金额": "30万"},
            "required_coverage": 0.5,
            "current_question": {
                "field_key": "采购目的",
                "question_text": "请说明本次采购的业务目标。",
                "options": ["业务交付", {"label": "内部测试", "value": "内部测试"}],
            },
            "next_actions": [{"action_key": "continue_collection", "label": "继续补充"}],
            "gate": {"status": "blocked"},
        },
        mode="requirement_intake",
        session_id="sess-test",
        user_message="我要采购一批测试服务器，用于AI模型训练和数据库压测，预算30万，2周内交付",
    )

    assert projection is not None
    pending = projection["pending_contract"]
    canvas_payload = projection["canvas_payload"]
    canvas_state = canvas_payload["canvas_state"]

    assert pending["mode_key"] == "requirement_intake"
    assert canvas_payload["type"] == "canvas_state"
    assert canvas_payload["ui_signal"]["active_tab"] == "requirement"
    assert canvas_state["progress"] == 0.5
    assert canvas_state["collected"]
    assert pending["current_question"]["options"][0]["label"] == "业务交付"
    assert canvas_state["current_question"]["options"][1]["value"] == "内部测试"
    assert any(item["field_key"] == "采购目的" for item in canvas_state["missing"])


def test_intake_workbench_projection_does_not_output_display_draft_without_pending_contract():
    projection = build_intake_workbench_projection(
        pending_contract=None,
        mode="requirement_canvas",
        session_id="sess-display-draft",
        user_message="我要采购一批测试服务器，用于AI模型训练和数据库压测，预算30万，2周内交付",
    )

    assert projection is None


def test_intake_workbench_projection_ignores_context_candidates_without_native_pending_contract():
    projection = build_intake_workbench_projection(
        pending_contract=None,
        mode="requirement_canvas",
        session_id="sess-context-candidates",
        user_message="我要采购一批办公桌椅，用于上海新办公室开放办公区，预算45万元",
        candidate_context={
            "candidate_fields": [
                {
                    "field_key": "一级品类",
                    "value": "空间相关",
                    "source": "rule_extracted",
                },
                {
                    "field_key": "二级品类",
                    "value": "办公家具、电器",
                    "source": "rule_extracted",
                },
            ]
        },
    )

    assert projection is None


def test_intake_workbench_projection_does_not_fabricate_missing_field_question():
    projection = build_intake_workbench_projection(
        pending_contract={
            "current_stage": "collecting",
            "missing_fields": ["项目名称"],
            "next_actions": [{"action_key": "continue_collection", "label": "继续补充"}],
        },
        mode="requirement_intake",
        session_id="sess-test",
        user_message="我要采购一批测试服务器",
    )

    assert projection is not None
    pending = projection["pending_contract"]
    canvas_state = projection["canvas_payload"]["canvas_state"]

    assert pending["current_question"] == {}
    assert pending["question"] == {}
    assert pending["has_active_question"] is False
    assert canvas_state["current_question"] == {}


def test_intake_workbench_projection_keeps_model_candidates_separate_from_collected():
    projection = build_intake_workbench_projection(
        pending_contract={
            "current_stage": "collecting",
            "missing_fields": ["一级品类", "二级品类"],
            "candidate_fields": [
                {
                    "field_key": "一级品类",
                    "value": "数据通讯设备",
                    "source": "model_inferred",
                    "confidence": 0.68,
                },
                {
                    "field_key": "二级品类",
                    "value": "服务器",
                    "source": "model_inferred",
                    "confidence": 0.64,
                },
            ],
        },
        mode="requirement_intake",
        session_id="sess-candidates",
        user_message="我要采购一批测试服务器，预算30万，2周内交付",
    )

    assert projection is not None
    pending = projection["pending_contract"]
    canvas_state = projection["canvas_payload"]["canvas_state"]
    collected_keys = {item["field_key"] for item in canvas_state["collected"]}
    candidate_keys = {item["field_key"] for item in canvas_state["candidate_fields"]}
    markdown = canvas_state["versions"][0]["content"]

    assert "一级品类" not in collected_keys
    assert "二级品类" not in collected_keys
    assert candidate_keys == {"一级品类", "二级品类"}
    assert pending["candidate_fields"][0]["normalization_status"] == "needs_confirmation"
    assert canvas_state["readiness"]["ready_for_submit"] is False
    assert "## 候选信息（待确认）" in markdown
    assert "- 一级品类: 数据通讯设备" in markdown


def test_intake_workbench_projection_does_not_reject_category_value_locally():
    projection = build_intake_workbench_projection(
        pending_contract={
            "current_stage": "collecting",
            "missing_fields": ["一级品类"],
            "candidate_fields": [{
                "field_key": "一级品类",
                "value": "开放式办公区",
                "source": "model_inferred",
            }],
        },
        mode="requirement_intake",
        session_id="sess-rejected-candidate",
        user_message="我要采购一批办公桌椅，预算45万元",
    )

    assert projection is not None
    pending = projection["pending_contract"]
    canvas_state = projection["canvas_payload"]["canvas_state"]

    assert pending["candidate_fields"][0]["field_key"] == "一级品类"
    assert canvas_state["candidate_fields"][0]["value"] == "开放式办公区"
    assert pending["rejected_candidates"] == []
    assert canvas_state["rejected_candidates"] == []
