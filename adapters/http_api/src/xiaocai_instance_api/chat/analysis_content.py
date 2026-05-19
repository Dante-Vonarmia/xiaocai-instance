"""Section-level content composer for procurement analysis reports."""

from __future__ import annotations

import re
from typing import Any

from xiaocai_instance_api.chat.response_text import normalize_assistant_display_text


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _to_text(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return ""


def _value(values: dict[str, str], *keys: str) -> str:
    for key in keys:
        text = _to_text(values.get(key))
        if text:
            return text
    return ""


def _fact_line(label: str, values: dict[str, str]) -> str:
    value = _to_text(values.get(label))
    return f"{label}：{value}" if value else f"{label}：待业务确认"


def _display(value: str, fallback: str = "待确认") -> str:
    text = _to_text(value)
    return text or fallback


def _internal_phrase_tokens() -> tuple[str, ...]:
    return (
        "produce_output",
        "当前步骤",
        "最终目标",
        "任务推进状态",
        "正文/结构",
        "workflow",
        "node_",
    )


def _number_from_text(text: str) -> float | None:
    compact = text.replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)", compact)
    if not match:
        return None
    value = float(match.group(1))
    if "万" in compact:
        value *= 10000
    return value


def _format_amount(value: float | None) -> str:
    if value is None:
        return "待确认"
    if value >= 10000:
        return f"{value / 10000:.1f}万元".replace(".0万", "万")
    return f"{value:.0f}元"


def _unit_budget(values: dict[str, str]) -> str:
    budget = _number_from_text(_value(values, "预算金额"))
    quantity = _number_from_text(_value(values, "数量"))
    unit = _value(values, "单位") or "单位"
    if budget is None or not quantity:
        return "单项预算上限待确认，建议在报价表中拆分产品、安装、服务和质保费用。"
    return f"按当前预算测算，单{unit}预算约 {_format_amount(budget / quantity)}，可作为供应商报价合理性校验线。"


def _contextual_notes(notes: list[str]) -> str:
    if not notes:
        return ""
    filtered: list[str] = []
    seen: set[str] = set()
    for item in notes:
        text = _to_text(item)
        if not text:
            continue
        if any(token in text for token in _internal_phrase_tokens()):
            continue
        # 低置信占位句在正文里已经有最小标注（如“待确认”），不再重复罗列。
        if any(marker in text for marker in ("待业务确认", "待确认", "待补充")):
            continue
        if text in seen:
            continue
        seen.add(text)
        filtered.append(text)
    if not filtered:
        return ""
    return "\n".join(f"- {item}" for item in filtered)


def _clean_table_line(line: str) -> str:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    cells = [cell for cell in cells if cell and set(cell) != {"-"}]
    if len(cells) >= 2:
        return f"{cells[0]}：{cells[1]}"
    return line.strip().strip("|").strip()


def _assistant_notes(assistant_message: str) -> dict[str, list[str]]:
    text = normalize_assistant_display_text(assistant_message).strip()
    if not text:
        return {}
    keyword_map = {
        "project-understanding": ("项目概况", "项目名称", "PR编号", "采购目的", "需求提出人", "使用场景"),
        "market-analysis": ("交付地点", "交付批次", "服务要求", "验收"),
        "cost-analysis": ("预算", "付款", "发票", "响应时效", "成本"),
        "risk-analysis": ("风险", "延误", "验收", "质保", "波动"),
        "strategy-suggestion": ("采购策略", "评估", "决策", "RFX", "RFQ", "RFP", "RFI", "RFB", "权重"),
        "supplier-selection": ("供应商", "画像", "资质", "履约", "候选"),
        "implementation-plan": ("里程碑", "实施", "流程", "交付", "计划", "假设", "待补充"),
    }
    notes: dict[str, list[str]] = {key: [] for key in keyword_map}
    for raw_line in text.splitlines():
        line = _clean_table_line(raw_line).lstrip("-•0123456789.、 ").strip()
        if not line or set(line) <= {"-", "|", " "}:
            continue
        if any(token in line for token in _internal_phrase_tokens()):
            continue
        for section_id, keywords in keyword_map.items():
            if any(keyword in line for keyword in keywords) and line not in notes[section_id]:
                notes[section_id].append(line)
    return {key: value[:6] for key, value in notes.items() if value}


def _section_dispatch_map() -> dict[str, Any]:
    """Schema-like section dispatch contract to avoid hardcoded if/else chains."""
    return {
        "project-understanding": lambda values, notes, rfx_type: _section_project(values, notes),
        "market-analysis": lambda values, notes, rfx_type: _section_market(values, notes),
        "cost-analysis": lambda values, notes, rfx_type: _section_cost(values, notes),
        "risk-analysis": lambda values, notes, rfx_type: _section_risk(values, notes),
        "strategy-suggestion": lambda values, notes, rfx_type: _section_strategy(values, notes, rfx_type),
        "supplier-selection": lambda values, notes, rfx_type: _section_supplier(values, notes),
        "implementation-plan": lambda values, notes, rfx_type: _section_plan(values, notes),
    }


def _section_project(values: dict[str, str], notes: list[str]) -> str:
    lines = [_contextual_notes(notes), "#### 项目概述", "| 维度 | 说明 |", "| --- | --- |"]
    lines.extend(
        [
            f"| RFX类型 | {_display(_value(values, 'RFX类型') or 'RFQ')} |",
            f"| 项目目标 | {_display(_value(values, '采购目的', '项目目标'))} |",
            f"| 项目名称 | {_display(_value(values, '项目名称'))} |",
            f"| 决策人 | {_display(_value(values, '决策人', '需求提出人'))} |",
            f"| 使用场景 | {_display(_value(values, '使用场景'))} |",
            f"| 品类 | {_display(_value(values, '一级品类'))} / {_display(_value(values, '二级品类'))} |",
        ]
    )
    return "\n".join(line for line in lines if line)


def _section_market(values: dict[str, str], notes: list[str]) -> str:
    lines = [_contextual_notes(notes)]
    lines.extend(
        [
            "#### 需求与交付范围",
            f"- **交付地点**：{_display(_value(values, '交付地点'))}",
            f"- **交付批次**：{_display(_value(values, '交付策略', '交付方式'))}",
            f"- **服务要求**：{_display(_value(values, '技术要求', '服务要求'), '供应商需提供现场测量、空间复核、安装与清运服务。')}",
            f"- **验收标准**：{_display(_value(values, '验收口径', '质量标准'), '以平整度、安装稳定性与基础使用功能验收为准。')}",
        ]
    )
    return "\n".join(line for line in lines if line)


def _section_cost(values: dict[str, str], notes: list[str]) -> str:
    budget_amount = _value(values, "预算金额")
    budget_currency = _value(values, "预算币种") or "CNY"
    budget_text = f"{budget_amount} {budget_currency}".strip() if budget_amount else "待确认"
    lines = [_contextual_notes(notes)]
    lines.extend(
        [
            "#### 预算与商务条款",
            "| 条款项 | 要求 |",
            "| --- | --- |",
            f"| 预算金额 | {budget_text} |",
            f"| 付款节点 | {_display(_value(values, '付款条款'))} |",
            f"| 发票类型 | {_display(_value(values, '发票类型'))} |",
            f"| 响应时效 | {_display(_value(values, '响应时效'))} |",
            _unit_budget(values),
        ]
    )
    return "\n".join(line for line in lines if line)


def _section_risk(values: dict[str, str], notes: list[str]) -> str:
    delivery_time = _value(values, "交付时间") or "目标交付时间"
    lines = [_contextual_notes(notes)]
    lines.extend(
        [
            f"核心风险一：交付排期风险。当前交付节点为「{delivery_time}」，若供应商备货、运输或现场安装排期不足，会影响入驻/会议协作等业务使用。",
            "核心风险二：规格与验收风险。若技术参数、材质、尺寸、颜色、承重和人体工学要求未固化，容易出现到货不一致和返工。",
            "核心风险三：报价口径风险。若未要求分项报价，供应商可能将运输、安装、清运、质保等费用混入总价，影响横向比价。",
            "建议控制条款：明确验收口径、免费更换/补齐机制、延期责任、质保响应时限，以及现场复尺/安装完成标准。",
        ]
    )
    return "\n".join(line for line in lines if line)


def _section_strategy(values: dict[str, str], notes: list[str], rfx_type: str) -> str:
    lines = [_contextual_notes(notes)]
    lines.extend(
        [
            "#### 供应商评估与决策机制",
            "| 评估维度 | 权重 | 核心考察点 |",
            "| --- | --- | --- |",
            "| 价格 | 30% | 综合报价竞争力、隐性成本透明度 |",
            "| 质量 | 25% | 材质与工艺、验收标准满足度 |",
            "| 交付 | 20% | 排期可达成性、安装协同能力 |",
            "| 服务 | 15% | 安装与售后响应时效 |",
            "| 风险 | 10% | 合同履约稳定性与风险应对 |",
            f"建议采用 {rfx_type} 作为当前主路径，优先统一分项报价口径后再进行评审定标。",
        ]
    )
    return "\n".join(line for line in lines if line)


def _section_supplier(values: dict[str, str], notes: list[str]) -> str:
    location = _value(values, "交付地点") or "项目交付地"
    lines = [_contextual_notes(notes)]
    lines.extend(
        [
            f"供应商画像：优先选择在「{location}」或周边具备批量交付、现场测量、安装协调和售后响应能力的办公家具/空间配置供应商。",
            "准入门槛：合法经营资质、同类项目案例、基础质量/环保/材质证明、可承诺交付排期、可提供发票与合同履约保障。",
            "优选指标：履约能力、专业人员、项目经验、资质认证、创新能力/知识产权、企业信用正负面记录、售后服务响应能力。",
            "建议候选池：内部合格供应商库优先；不足时补充本地有现货或快速生产能力的区域供应商，并要求提供样品/材质照片或过往项目验收证明。",
        ]
    )
    return "\n".join(line for line in lines if line)


def _section_plan(values: dict[str, str], notes: list[str]) -> str:
    delivery_time = _value(values, "交付时间") or "最终交付节点"
    lines = [_contextual_notes(notes)]
    lines.extend(
        [
            "#### 项目里程碑与排期",
            "| 里程碑节点 | 计划完成时间 | 关键交付物/动作 |",
            "| --- | --- | --- |",
            "| 供应商初筛 | 待确认 | 资质核验、过往案例评估 |",
            "| 报价比选 | 待确认 | 综合评分、商务谈判 |",
            "| 合同签署 | 待确认 | 条款确认、法务审批 |",
            f"| 首批交付安装 | {_display(delivery_time)} | 到货安装、现场初验 |",
            "",
            "#### 当前假设",
            "1. 现场清运仅覆盖本次采购新增家具包装，不包含原有家具拆除。",
            "2. 首批交付完成并验收后再触发安装阶段付款。",
            "3. 供应商可提供结构化配置清单并支持现场复尺。",
            "",
            "#### 待补充信息 / 高价值校准",
            "- 高价值校准项：第二批交付（独立办公区与接待区）的截止日期与验收标准是否与首批一致。",
            "- 建议补充项：详细 BOM 清单（品类、数量、材质/颜色偏好、人体工学等级）。",
        ]
    )
    lines.extend(
        [
            f"计划建议：围绕「{delivery_time}」倒排，先完成供应商初筛与 RFX 发出，再完成报价澄清、评审定标、合同签署、到货安装和整体验收。",
            "流程建议：若供应商范围不清，可先做信息收集；若规格明确，可直接比价；若方案差异大，再做方案型评审。",
        ]
    )
    return "\n".join(line for line in lines if line)


def compose_section_content(
    *,
    section: dict[str, Any],
    values: dict[str, str],
    user_message: str,
    assistant_notes: dict[str, list[str]],
    rfx_type: str,
) -> str:
    _ = user_message
    section_id = _to_text(section.get("id"))
    notes = assistant_notes.get(section_id, [])
    render = _section_dispatch_map().get(section_id)
    if render:
        return render(values, notes, rfx_type)
    title = _to_text(section.get("title")) or "分析章节"
    return f"围绕「{title}」生成结构化分析初稿，并保留缺口字段用于后续补证。"


def compose_document_sections(
    *,
    template_sections: list[dict[str, Any]],
    field_values: dict[str, str],
    user_message: str,
    evidence_refs: list[dict[str, Any]],
    assistant_message: str,
    rfx_type: str,
) -> list[dict[str, Any]]:
    evidence_ids = [_to_text(item.get("id")) for item in evidence_refs if _to_text(item.get("id"))]
    notes = _assistant_notes(assistant_message)
    sections: list[dict[str, Any]] = []
    for section in template_sections:
        required_fields = [_to_text(item) for item in _as_list(section.get("required_fields")) if _to_text(item)]
        missing = [field for field in required_fields if not _to_text(field_values.get(field))]
        sections.append(
            {
                "kind": "narrative",
                "id": _to_text(section.get("id")),
                "title": _to_text(section.get("title")),
                "status": "incomplete" if missing else "complete",
                "info": [f"待确认字段：{field}" for field in missing],
                "content": compose_section_content(
                    section=section,
                    values=field_values,
                    user_message=user_message,
                    assistant_notes=notes,
                    rfx_type=rfx_type,
                ),
                "evidence_ref_ids": evidence_ids,
            }
        )
    return sections
