from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from xiaocai_instance_api.chat.orchestration.contract_loader import load_pack_mount_snapshot
from .constants import CITY_KEYWORDS


def contains_any(text: str, keywords: List[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _normalize(value: str) -> str:
    return value.strip().strip("'").strip('"')


def _resolve_intent_alias_rules_path() -> Path:
    root = Path(load_pack_mount_snapshot().domain_packs_root)
    return root / "shared" / "rules" / "clarification_relevance_rules.yaml"


def _parse_intent_alias_rules(text: str) -> dict:
    data = {
        "direct_plan_keywords": [],
        "product_service_aliases": {},
    }
    section = ""
    current_alias = ""
    alias_indent = 0

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = _line_indent(raw_line)
        if stripped == "direct_plan_keywords:":
            section = "direct_plan_keywords"
            current_alias = ""
            continue
        if stripped == "product_service_aliases:":
            section = "product_service_aliases"
            current_alias = ""
            continue
        if section == "direct_plan_keywords" and indent == 0 and stripped.endswith(":") and stripped != "direct_plan_keywords:":
            section = ""
            current_alias = ""
            continue
        if section == "product_service_aliases" and indent == 0 and stripped.endswith(":") and stripped != "product_service_aliases:":
            section = ""
            current_alias = ""
            continue
        if section == "direct_plan_keywords" and stripped.startswith("- "):
            data["direct_plan_keywords"].append(_normalize(stripped[2:]))
            continue
        if section == "product_service_aliases" and stripped.startswith("- alias:"):
            current_alias = _normalize(stripped.split(":", 1)[1]).lower()
            alias_indent = indent
            continue
        if section == "product_service_aliases" and current_alias and indent > alias_indent and stripped.startswith("canonical:"):
            data["product_service_aliases"][current_alias] = _normalize(stripped.split(":", 1)[1])
            current_alias = ""
    return data


@lru_cache(maxsize=1)
def _load_intent_alias_rules() -> dict:
    path = _resolve_intent_alias_rules_path()
    try:
        return _parse_intent_alias_rules(path.read_text(encoding="utf-8"))
    except Exception:
        return {"direct_plan_keywords": [], "product_service_aliases": {}}


def is_direct_plan_request(message: str) -> bool:
    text = (message or "").strip().lower()
    if not text:
        return False
    rules = _load_intent_alias_rules()
    keywords = [str(item).strip().lower() for item in rules.get("direct_plan_keywords", []) if str(item).strip()]
    return contains_any(text, keywords)


def _alias_product_service(text: str) -> str:
    normalized = text.strip().lower()
    if not normalized:
        return ""
    rules = _load_intent_alias_rules()
    aliases = rules.get("product_service_aliases", {})
    canonical = aliases.get(normalized)
    return str(canonical).strip() if isinstance(canonical, str) else ""


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
    elif not slots.get("产品/服务"):
        aliased = _alias_product_service(text)
        if aliased:
            slots["产品/服务"] = aliased

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
