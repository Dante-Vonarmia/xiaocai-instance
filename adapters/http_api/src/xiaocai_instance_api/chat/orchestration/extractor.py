from __future__ import annotations

import re
from typing import Dict, List

from .constants import CITY_KEYWORDS


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
        slots["数量"] = qty_match.group(1)
        slots["单位"] = qty_match.group(2)
        slots["数量和单位"] = f"{qty_match.group(1)}{qty_match.group(2)}"
    elif re.search(r"一\s*批", text):
        slots["数量"] = "1"
        slots["单位"] = "批"
        slots["数量和单位"] = "1批"

    for city in CITY_KEYWORDS:
        if city in text:
            slots["交付地点"] = city
            break

    time_match = re.search(r"(\d{1,2}月\d{1,2}[日号]?[前后]?|[下本]月|月底前|月底|本周|下周|月底之前|[0-9]+[天周月]内)", text)
    if time_match:
        slots["交付时间"] = time_match.group(1)

    scene_match = re.search(r"(?:用于|用来|使用于)([^，。；\n]{2,40})", text)
    if scene_match:
        slots["使用场景"] = scene_match.group(1).strip()

    product_match = re.search(r"(采购|定制|需要|找)([^，。；\n]{2,40})", text)
    if product_match:
        raw = product_match.group(2).strip()
        if raw:
            slots["产品/服务"] = raw

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
