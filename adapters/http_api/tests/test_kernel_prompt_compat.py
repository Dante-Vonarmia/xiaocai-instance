from xiaocai_instance_api.chat.kernel_client import KernelClient


DETAILED_RFX_PROMPT = (
    "系统设置提示词：必须按需求分析模板输出完整报告。\n"
    "五、采购策略分析：包含目标优先级权重、其他约束。"
)


def _domain_prompt_context() -> dict:
    return {
        "mode": "requirement_canvas",
        "domain_system_prompt": DETAILED_RFX_PROMPT,
        "domain_prompt_instructions": {
            "source": "system_settings_and_domain_pack",
            "active_stage": "requirement-analysis",
            "active_template": {"key": "requirement_analysis"},
            "prompt_text": DETAILED_RFX_PROMPT,
        },
    }


def test_domain_prompt_context_is_not_projected_into_flare_prompt_contracts():
    body = KernelClient._build_request_body(
        user_id="user-1",
        message="生成RFX策略",
        session_id="session-1",
        context=_domain_prompt_context(),
    )

    payload = body["payload"]

    assert payload["domain_system_prompt"] == DETAILED_RFX_PROMPT
    assert payload["domain_prompt_instructions"]["active_template"]["key"] == "requirement_analysis"
    assert "artifact_template_result" not in payload
    assert "response_strategy_result" not in payload
    assert "user_template" not in payload
    assert "module_prompt_registry" not in payload
