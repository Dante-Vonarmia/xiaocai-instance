from xiaocai_instance_api.chat.orchestration.extractor import extract_slots
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


def test_extract_slots_handles_server_intake_scene_and_week_deadline():
    slots = extract_slots("我要采购一批测试服务器，用于AI模型训练和数据库压测，预算30万，2周内交付")

    assert slots["预算金额"] == "30万"
    assert slots["采购目的"] == "完成本次业务采购交付"
    assert slots["一级品类"] == "服务器"
    assert slots["二级品类"] == "服务器"
    assert slots["交付时间"] == "2周内"
    assert slots["使用场景"] == "AI模型训练和数据库压测"


def test_intake_workbench_projection_outputs_canvas_state():
    projection = build_intake_workbench_projection(
        pending_contract={
            "current_stage": "clarify_requirement",
            "missing_fields": ["采购目的"],
            "current_question": {
                "field_key": "采购目的",
                "question_text": "为先把当前需求分析做准，建议先补充：采购目的",
                "options": [],
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
    assert canvas_state["progress"] > 0
    assert canvas_state["collected"]
    assert all(item["field_key"] != "采购目的" for item in canvas_state["missing"])
