from xiaocai_instance_api.chat.kernel_client import KernelClient


DETAILED_RFX_PROMPT = (
    "系统设置提示词：必须按需求分析模板输出完整报告。\n"
    "五、采购策略分析：包含目标优先级权重、其他约束。\n"
    "六、供应商选择建议：包含供应商画像、准入门槛和优选指标。\n"
    "七、项目实施计划与执行建议：包含采购流程规划、文件与工具准备。"
)


def _domain_prompt_context() -> dict:
    return {
        "mode": "requirement_canvas",
        "domain_system_prompt": DETAILED_RFX_PROMPT,
        "domain_prompt_instructions": {
            "source": "system_settings_and_domain_pack",
            "active_stage": "requirement-analysis",
            "active_template": {
                "key": "requirement_analysis",
                "title": "需求分析与 RFX 策略研判",
                "stage": "需求分析",
            },
            "input_fields": [
                {"field": "技术要求", "value": "办公桌符合人体工学", "status": "filled"},
                {"field": "质量标准", "value": "三年质保", "status": "filled"},
            ],
            "output_sections": [
                "项目理解与核心需求",
                "市场现状和分析",
                "成本结构分析",
                "项目风险分析",
                "采购策略分析",
                "供应商选择建议",
                "项目实施计划与执行建议",
            ],
            "template_weights": [
                {
                    "template_key": "office_furniture_analysis",
                    "score": 0.82,
                    "base_weight": 0.7,
                    "status": "candidate",
                }
            ],
            "prompt_text": DETAILED_RFX_PROMPT,
        },
    }


def test_domain_prompt_maps_to_flare_supported_prompt_contracts():
    body = KernelClient._build_request_body(
        user_id="user-1",
        message="生成RFX策略",
        session_id="session-1",
        context=_domain_prompt_context(),
    )

    payload = body["payload"]
    template = payload["artifact_template_result"]["template"]
    strategy = payload["response_strategy_result"]
    user_template = payload["user_template"]["template"]
    module_prompt = payload["module_prompt_registry"][0]

    assert body["context"]["domain_system_prompt"] == DETAILED_RFX_PROMPT
    assert payload["domain_prompt_instructions"]["active_template"]["key"] == "requirement_analysis"
    assert payload["mode"] == "requirement_intake"
    assert payload["artifact_template_result"]["status"] == "matched"
    assert template["template_sections"][0] == "项目理解与核心需求"
    assert template["required_output_fields"] == ["技术要求", "质量标准"]
    assert "目标优先级权重" in template["instruction"]
    assert strategy["response_plan"]["sections"][-1]["label"] == "项目实施计划与执行建议"
    assert "采购流程规划" in strategy["response_plan"]["guidance"]
    assert user_template["template_sections"] == template["template_sections"]
    assert "供应商画像" in user_template["instruction"]
    assert module_prompt["module_key"] == "requirement_analysis"
    assert "准入门槛" in module_prompt["prompt_instruction"]


def test_domain_prompt_mapping_preserves_existing_flare_prompt_contracts():
    context = {
        **_domain_prompt_context(),
        "response_strategy_result": {"strategy_key": "custom_strategy"},
        "artifact_template_result": {"status": "matched", "template_key": "custom_template"},
        "user_template": {"title": "custom user template"},
        "module_prompt_registry": [{"module_key": "existing", "priority": 1}],
    }

    body = KernelClient._build_request_body(
        user_id="user-1",
        message="生成RFX策略",
        session_id="session-1",
        context=context,
    )

    payload = body["payload"]

    assert payload["response_strategy_result"] == {"strategy_key": "custom_strategy"}
    assert payload["artifact_template_result"] == {"status": "matched", "template_key": "custom_template"}
    assert payload["user_template"] == {"title": "custom user template"}
    assert payload["module_prompt_registry"][0]["module_key"] == "requirement_analysis"
    assert payload["module_prompt_registry"][1]["module_key"] == "existing"
