from xiaocai_instance_api.chat.kernel_request_body import build_kernel_request_body


def test_kernel_request_body_does_not_forward_function_type_as_capability_target():
    for function_type in ("auto", "workflow", "procurement"):
        request_body = build_kernel_request_body(
            user_id=f"user-{function_type}-function-type",
            message="我要举办个招商活动",
            session_id=f"sess-{function_type}-function-type",
            context={
                "project_id": "project-1",
                "function_type": function_type,
                "mode": "auto",
                "enabled_capabilities": [],
            },
        )

        assert "intent" not in request_body
        assert "function_type" not in request_body["context"]
        assert "function_type" not in request_body["payload"]
        assert "enabled_capabilities" not in request_body["context"]
        assert "enabled_capabilities" not in request_body["payload"]
        assert request_body["payload"]["mode"] == "auto"
        assert request_body["payload"]["message"] == "我要举办个招商活动"


def test_kernel_request_body_keeps_explicit_intent_capability_target():
    request_body = build_kernel_request_body(
        user_id="user-explicit-intent",
        message="请生成需求分析",
        session_id="sess-explicit-intent",
        context={
            "intent": "analysis_mode",
        },
    )

    assert request_body["intent"] == "analysis_mode"
    assert request_body["payload"]["intent"] == "analysis_mode"


def test_kernel_request_body_normalizes_legacy_target_mode_alias():
    request_body = build_kernel_request_body(
        user_id="user-legacy-target",
        message="同步到需求梳理",
        session_id="sess-legacy-target",
        context={
            "target_mode": "requirement_canvas",
            "flare_payload_extra": {"mode_key": "requirement_canvas"},
        },
    )

    assert request_body["target_mode"] == "requirement_intake"
    assert request_body["payload"]["target_mode"] == "requirement_intake"
    assert request_body["payload"]["mode_key"] == "requirement_intake"
