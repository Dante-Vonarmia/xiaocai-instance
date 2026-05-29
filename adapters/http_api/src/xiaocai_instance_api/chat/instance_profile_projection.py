"""Project xiaocai branding into the FLARE core instance profile shape."""

from __future__ import annotations

from typing import Any


DEFAULT_PRODUCT_NAME = "小采"
DEFAULT_BRAND_TAG = "AI智能采购助手"
DEFAULT_LOGO_URL = "/assets/logo-xiaocai.svg"
DEFAULT_SIDEBAR_LOGO_URL = "/assets/logo-xiaocai-wordmark.svg"
GENERIC_PRODUCT_NAMES = {"flare", "f.l.a.r.e"}
GENERIC_BRAND_TAGS = {"workspace", "项目协同工作台"}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _first_text(*values: Any) -> str:
    for value in values:
        text = _text(value)
        if text:
            return text
    return ""


def _first_non_generic_text(generic_values: set[str], *values: Any) -> str:
    for value in values:
        text = _text(value)
        if text and text.lower() not in generic_values:
            return text
    return ""


def _profile_source(payload: dict[str, Any]) -> dict[str, Any]:
    nested_profile = _as_dict(payload.get("instance_profile"))
    return nested_profile or payload


def normalize_instance_profile(raw_payload: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize app branding into the flat profile consumed by FLARE chat core."""

    payload = _as_dict(raw_payload)
    profile = _profile_source(payload)
    instance = _as_dict(profile.get("instance"))
    branding = _as_dict(profile.get("branding"))
    logo = _as_dict(branding.get("logo"))
    chat = _as_dict(_as_dict(profile.get("ui")).get("chat"))
    source_labels = {
        **_as_dict(chat.get("uiLabels")),
        **_as_dict(profile.get("ui_labels")),
    }

    product_name = _first_non_generic_text(
        GENERIC_PRODUCT_NAMES,
        profile.get("product_name"),
        source_labels.get("product_name"),
        instance.get("displayName"),
        DEFAULT_PRODUCT_NAME,
    )
    brand_tag = _first_non_generic_text(
        GENERIC_BRAND_TAGS,
        profile.get("brand_tag"),
        source_labels.get("brand_tag"),
        instance.get("subtitle"),
        DEFAULT_BRAND_TAG,
    )
    logo_url = _first_text(
        profile.get("logo_url"),
        source_labels.get("logo_url"),
        logo.get("light"),
        DEFAULT_LOGO_URL,
    )
    sidebar_logo_url = _first_text(
        source_labels.get("sidebar_logo_url"),
        logo.get("sidebar"),
        logo.get("wordmark"),
        DEFAULT_SIDEBAR_LOGO_URL,
        logo_url,
    )
    logo_alt = _first_text(
        profile.get("logo_text"),
        source_labels.get("logo_alt"),
        source_labels.get("sidebar_logo_alt"),
        product_name,
    )

    ui_labels = {
        **source_labels,
        "product_name": product_name,
        "brand_tag": brand_tag,
        "logo_url": logo_url,
        "logo_alt": logo_alt,
        "product_logo_url": _first_text(source_labels.get("product_logo_url"), logo_url),
        "product_logo_alt": _first_text(source_labels.get("product_logo_alt"), logo_alt),
        "empty_state_logo_url": _first_text(source_labels.get("empty_state_logo_url"), logo_url),
        "empty_state_logo_alt": _first_text(source_labels.get("empty_state_logo_alt"), logo_alt),
        "sidebar_logo_url": sidebar_logo_url,
        "sidebar_logo_alt": _first_text(source_labels.get("sidebar_logo_alt"), logo_alt),
    }

    return {
        "product_name": product_name,
        "brand_tag": brand_tag,
        "logo_text": logo_alt,
        "logo_url": logo_url,
        "ui_labels": ui_labels,
    }


def project_instance_profile_event(event: dict[str, Any]) -> dict[str, Any]:
    """Keep stream profile events compatible with FLARE core without UI fallback."""

    profile = normalize_instance_profile(event)
    return {
        **event,
        "instance_profile": profile,
        "product_name": profile["product_name"],
        "brand_tag": profile["brand_tag"],
        "logo_text": profile["logo_text"],
        "logo_url": profile["logo_url"],
        "ui_labels": profile["ui_labels"],
    }


__all__ = ["normalize_instance_profile", "project_instance_profile_event"]
