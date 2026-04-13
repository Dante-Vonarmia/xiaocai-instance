from __future__ import annotations

import re
from typing import Dict, List

from .constants import CITY_KEYWORDS, L1_L2_KEYWORDS


def contains_any(text: str, keywords: List[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def extract_slots(text: str) -> Dict[str, str]:
    slots: Dict[str, str] = {}

    budget_match = re.search(r"预算[^\d]{0,3}(\d+(?:\.\d+)?)\s*(万|元|k|K|m|M)?", text)
    if budget_match:
        amount = budget_match.group(1)
        unit = budget_match.group(2) or "元"
        slots["预算金额"] = f"{amount}{unit}"

    qty_match = re.search(r"(\d+)\s*(份|个|台|套|人|家|张|件|箱|吨|次)", text)
    if qty_match:
        slots["数量和单位"] = f"{qty_match.group(1)}{qty_match.group(2)}"

    for city in CITY_KEYWORDS:
        if city in text:
            slots["交付地点"] = city
            break

    time_match = re.search(r"(\d{1,2}月\d{1,2}[日号]?[前后]?|[下本]月|月底前|月底|本周|下周|月底之前|[0-9]+天内)", text)
    if time_match:
        slots["交付时间"] = time_match.group(1)

    if contains_any(text, ["采购", "购买", "定制", "招标", "询价"]):
        slots["采购目的"] = "完成本次业务采购交付"

    if contains_any(text, ["周年庆", "发布会", "答谢", "活动"]):
        slots["使用场景"] = "市场活动执行"

    for l1, l2 in L1_L2_KEYWORDS:
        if l1 in text:
            slots["一级品类"] = l1
            slots["二级品类"] = l2
            break

    product_match = re.search(r"(采购|定制|需要|找)([^，。；\n]{2,40})", text)
    if product_match:
        raw = product_match.group(2).strip()
        if raw:
            slots["产品/服务"] = raw

    if "技术要求" in text:
        slots["技术要求"] = "已由用户给出（会话上下文）"
    if "质量标准" in text or "质量" in text:
        slots["质量标准"] = "已由用户给出（会话上下文）"
    if "验收" in text:
        slots["验收口径"] = "已由用户给出（会话上下文）"
    if "发票" in text:
        slots["发票类型"] = "已由用户给出（会话上下文）"
    if "付款" in text:
        slots["付款条款"] = "已由用户给出（会话上下文）"
    if "条款" in text:
        slots["关键条款"] = "已由用户给出（会话上下文）"
    if "分批" in text or "一次性交付" in text or "交付方式" in text:
        slots["交付方式"] = "已由用户给出（会话上下文）"

    return slots


def detect_intent(message: str, mode: str | None) -> str:
    if mode == "intelligent_sourcing":
        return "sourcing"
    if contains_any(message, ["RFX", "RFI", "RFQ", "RFP", "RFB", "询价", "招标", "比价"]):
        return "rfx"
    if contains_any(message, ["需求分析", "分析", "风险分析", "可行性"]):
        return "analysis"
    if contains_any(message, ["寻源", "供应商", "找供应商", "检索"]):
        return "sourcing"
    return "collection"
