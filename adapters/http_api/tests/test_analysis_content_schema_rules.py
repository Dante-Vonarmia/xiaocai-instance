from xiaocai_instance_api.chat.analysis_content import compose_section_content


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
