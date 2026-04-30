from __future__ import annotations

from pathlib import Path

from xiaocai_instance_api.chat.orchestration.contract_loader import load_pack_mount_snapshot


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _normalize_scalar(value: str) -> str:
    return value.strip().strip("'").strip('"')


def _normalize_for_match(value: str) -> str:
    return (
        value.replace(" ", "")
        .replace("　", "")
        .replace("/", "")
        .replace("（", "(")
        .replace("）", ")")
        .strip()
    )


def _resolve_taxonomy_path() -> Path:
    root = Path(load_pack_mount_snapshot().domain_packs_root)
    return root / "category-fields" / "procurement-category-fields.yaml"


def _parse_taxonomy_paths(text: str) -> list[dict]:
    paths: list[dict] = []
    in_owner_section = False
    current_owner = ""
    current_l1 = ""

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "采购负责类:":
            in_owner_section = True
            continue
        if not in_owner_section:
            continue

        indent = _line_indent(raw_line)
        if indent == 2 and stripped.startswith("- 名称:"):
            current_owner = _normalize_scalar(stripped.split(":", 1)[1])
            current_l1 = ""
            continue
        if indent == 6 and stripped.startswith("- 名称:"):
            current_l1 = _normalize_scalar(stripped.split(":", 1)[1])
            continue
        if indent == 10 and stripped.startswith("- 名称:"):
            current_l2 = _normalize_scalar(stripped.split(":", 1)[1])
            paths.append(
                {
                    "owner_category": current_owner,
                    "level1_category": current_l1,
                    "level2_category": current_l2,
                    "path": [current_owner, current_l1, current_l2],
                }
            )

    return paths


def _build_source_text(user_message: str | None, kernel_context: dict) -> str:
    fragments: list[str] = []
    if isinstance(user_message, str) and user_message.strip():
        fragments.append(user_message.strip())
    for key in ("采购目的", "使用场景", "一级品类", "二级品类", "产品/服务"):
        value = kernel_context.get(key)
        if isinstance(value, str) and value.strip():
            fragments.append(value.strip())
    confirmed_fields = kernel_context.get("confirmed_fields")
    if isinstance(confirmed_fields, dict):
        for key in ("采购目的", "使用场景", "一级品类", "二级品类", "产品/服务"):
            value = confirmed_fields.get(key)
            if isinstance(value, str) and value.strip():
                fragments.append(value.strip())
    return _normalize_for_match(" ".join(fragments))


def _round_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def build_taxonomy_prior(
    *,
    user_message: str | None,
    kernel_context: dict,
    limit: int = 5,
) -> dict:
    taxonomy_text = _resolve_taxonomy_path().read_text(encoding="utf-8")
    paths = _parse_taxonomy_paths(taxonomy_text)
    source_text = _build_source_text(user_message, kernel_context)

    explicit_l1 = _normalize_for_match(str(kernel_context.get("一级品类") or ""))
    explicit_l2 = _normalize_for_match(str(kernel_context.get("二级品类") or ""))

    candidate_pool: list[dict] = []
    for item in paths:
        owner = _normalize_for_match(item["owner_category"])
        level1 = _normalize_for_match(item["level1_category"])
        level2 = _normalize_for_match(item["level2_category"])

        owner_hit = 1.0 if owner and owner in source_text else 0.0
        level1_hit = 1.0 if level1 and level1 in source_text else 0.0
        level2_hit = 1.0 if level2 and level2 != "/" and level2 in source_text else 0.0
        explicit_match_bonus = 0.0
        if explicit_l1 and explicit_l1 == level1:
            explicit_match_bonus += 0.2
        if explicit_l2 and explicit_l2 == level2:
            explicit_match_bonus += 0.3

        score = owner_hit * 0.2 + level1_hit * 0.35 + level2_hit * 0.45 + explicit_match_bonus
        if score <= 0:
            continue

        candidate_pool.append(
            {
                "owner_category": item["owner_category"],
                "level1_category": item["level1_category"],
                "level2_category": item["level2_category"],
                "path": item["path"],
                "owner_hit": _round_score(owner_hit),
                "level1_hit": _round_score(level1_hit),
                "level2_hit": _round_score(level2_hit),
                "explicit_match_bonus": _round_score(explicit_match_bonus),
                "score": _round_score(score),
            }
        )

    candidate_pool.sort(
        key=lambda item: (
            item.get("score", 0.0),
            item.get("level2_hit", 0.0),
            item.get("level1_hit", 0.0),
        ),
        reverse=True,
    )
    top_candidate = candidate_pool[0] if candidate_pool else {}
    return {
        "candidate_pool": candidate_pool[: max(1, limit)],
        "resolved_path": top_candidate.get("path", []),
        "resolved_level1_category": top_candidate.get("level1_category", ""),
        "resolved_level2_category": top_candidate.get("level2_category", ""),
        "confidence_score": top_candidate.get("score", 0.0),
    }
