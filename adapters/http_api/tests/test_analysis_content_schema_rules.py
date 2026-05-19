from xiaocai_instance_api.chat.analysis_content import compose_document_sections, compose_section_content
from xiaocai_instance_api.chat.analysis_visibility import sanitize_analysis_payload, sanitize_visible_text


def test_compose_section_content_uses_schema_dispatch_for_strategy() -> None:
    content = compose_section_content(
        section={"id": "strategy-suggestion", "title": "采购策略分析"},
        values={},
        user_message="",
        assistant_notes={"strategy-suggestion": ["建议统一报价口径"]},
        rfx_type="RFP",
    )

    assert "建议采用 RFP 作为当前主路径" in content
    assert "建议统一报价口径" in content


def test_compose_section_content_drops_low_confidence_note_listing() -> None:
    content = compose_section_content(
        section={"id": "project-understanding", "title": "项目理解与核心需求"},
        values={"项目名称": "办公空间桌椅采购"},
        user_message="",
        assistant_notes={
            "project-understanding": [
                "项目名称：办公空间桌椅采购",
                "项目编号：待业务确认",
                "采购目的：待确认",
            ]
        },
        rfx_type="RFQ",
    )

    assert "- 项目名称：办公空间桌椅采购" in content
    assert "项目编号：待业务确认" not in content
    assert "采购目的：待确认" not in content
    assert "已识别信息：" not in content


def test_compose_document_sections_reuses_assistant_template_facts() -> None:
    sections = compose_document_sections(
        template_sections=[{"id": "project-understanding", "title": "项目理解与核心需求", "required_fields": []}],
        field_values={"采购目的": "完成办公区桌椅采购"},
        user_message="请输出 RFQ 报告",
        evidence_refs=[],
        assistant_message="| 当前步骤 | produce_output |\n| 项目目标 | 完成办公区桌椅采购 |",
        rfx_type="RFQ",
    )

    content = sections[0]["content"]
    assert "| 维度 | 说明 |" in content
    assert "| 项目目标 | 完成办公区桌椅采购 |" in content
    assert "produce_output" not in content


def test_sanitize_visible_text_rewrites_internal_terms() -> None:
    text = sanitize_visible_text("当前步骤：produce_output，最终目标：交付")
    assert "当前建议" in text
    assert "生成分析报告" in text
    assert "交付目标" in text


def test_sanitize_visible_text_drops_internal_debug_lines() -> None:
    text = sanitize_visible_text("执行摘要\ndebug: node_strategy\n建议：先复核关键字段")
    assert "执行摘要" in text
    assert "建议：先复核关键字段" in text
    assert "node_strategy" not in text
    assert "debug" not in text


def test_sanitize_analysis_payload_cleans_nested_fields() -> None:
    payload = {
        "markdown": "当前步骤：produce_output\nnode_plan: draft",
        "document": {
            "summary": {"judgement": "workflow: done", "recommendation": "最终目标：提交报告"},
            "sections": [{"title": "项目理解", "content": "response_strategy_result=1"}],
            "next_steps": [{"label": "next_actions: run"}],
        },
    }
    sanitized = sanitize_analysis_payload(payload)
    assert "produce_output" not in sanitized["markdown"]
    assert "node_plan" not in sanitized["markdown"]
    assert "workflow" not in sanitized["document"]["summary"]["judgement"]
    assert "交付目标" in sanitized["document"]["summary"]["recommendation"]
    assert "response_strategy_result" not in sanitized["document"]["sections"][0]["content"]
    assert "next_actions" not in sanitized["document"]["next_steps"][0]["label"]
