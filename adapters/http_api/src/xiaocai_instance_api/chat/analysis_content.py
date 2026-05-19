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
        "market-analysis": ("市场", "供应链", "供应", "品质", "资料", "证据限制"),
        "cost-analysis": ("成本", "预算", "付款", "价格", "发票", "降本"),
        "risk-analysis": ("风险", "证据限制", "波动", "延误", "验收", "质保", "校准"),
        "strategy-suggestion": ("采购策略", "评估", "决策", "RFX", "RFQ", "RFP", "RFI", "RFB", "权重"),
        "supplier-selection": ("供应商", "画像", "资质", "履约", "服务要求", "候选"),
        "implementation-plan": ("里程碑", "实施", "流程", "交付", "计划", "05-", "06-", "合同"),
    }
    notes: dict[str, list[str]] = {key: [] for key in keyword_map}
    for raw_line in text.splitlines():
        line = _clean_table_line(raw_line).lstrip("-•0123456789.、 ").strip()
        if not line or set(line) <= {"-", "|", " "}:
            continue
        for section_id, keywords in keyword_map.items():
            if any(keyword in line for keyword in keywords) and line not in notes[section_id]:
                notes[section_id].append(line)
    return {key: value[:5] for key, value in notes.items() if value}


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
    facts = ["项目名称", "PR编号", "采购目的", "使用场景", "需求提出人", "一级品类", "二级品类"]
    lines = [_contextual_notes(notes), "本节用于确认项目目标、采购边界和业务影响范围："]
    lines.extend(f"- {_fact_line(item, values)}" for item in facts)
    lines.append("分析结论：若以上字段无异议，可将本项目定位为标准化办公空间配置采购，后续重点放在交期、规格一致性和履约服务约束。")
    return "\n".join(line for line in lines if line)


def _section_market(values: dict[str, str], notes: list[str]) -> str:
    product = _value(values, "产品/服务", "采购目的") or "本次采购对象"
    location = _value(values, "交付地点") or "目标交付地"
    lines = [_contextual_notes(notes)]
    lines.extend(
        [
            f"围绕「{product}」和「{location}」交付，应优先判断区域供应可得性、现货/定制周期、安装服务覆盖和售后响应半径。",
            "若属于办公家具等标准化程度较高的品类，市场供给通常可通过多家供应商比价获得，但交付周期、安装排期和批量一致性会直接影响最终可用性。",
            "建议补充外部市场价格区间、同城履约案例和主要品牌/材质档位，用于校准报价是否偏离市场合理区间。",
        ]
    )
    return "\n".join(line for line in lines if line)


def _section_cost(values: dict[str, str], notes: list[str]) -> str:
    lines = [_contextual_notes(notes)]
    lines.extend(
        [
            _unit_budget(values),
            "成本结构建议拆为：产品/主材成本、定制或模块化配置成本、运输搬运成本、现场测量与安装成本、售后质保成本、项目管理与风险缓冲。",
            f"- {_fact_line('预算金额', values)}",
            f"- {_fact_line('数量', values)}",
            f"- {_fact_line('单位', values)}",
            f"- {_fact_line('付款条款', values)}",
            "降本方向：优先统一规格与材质档位、压缩非必要定制项、分项报价比价、将安装/清运/质保服务单列以避免总价不透明。",
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
            f"建议采用 {rfx_type} 作为当前主路径：在需求规格较明确、供应商可比价的前提下，优先形成统一报价口径并快速完成供应商横向评估。",
            "目标优先级建议：价格30%、产品质量25%、交付周期20%、安装服务15%、售后质保10%。若业务更重视快速入驻，可将交付周期权重上调。",
            "执行策略：先发出标准化 RFQ/RFX 包，要求供应商提交分项报价、材料/资质证明、交付排期、安装方案和质保承诺；报价后组织一次澄清，统一缺口后再定标。",
            "输出物：配置清单、分项报价表、评分表、澄清问题清单、合同关键条款草案。",
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
            "优先解决的问题：冻结规格与数量、确认交付楼层/区域、明确安装窗口、统一付款和验收条款。",
            f"计划建议：围绕「{delivery_time}」倒排，先完成供应商初筛与 RFQ/RFX 发出，再完成报价澄清、评审定标、合同签署、到货安装和整体验收。",
            "流程建议：若供应商范围不清，可先 RFI 收集候选；若已有供应商池且规格明确，可直接 RFQ；若方案差异较大，再追加 RFP 澄清方案能力。",
            "资源保障：采购负责人、需求部门验收人、行政/空间负责人、财务付款确认人需提前明确，避免合同与现场验收脱节。",
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
