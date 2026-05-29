from xiaocai_instance_api.chat.instance_profile_projection import (
    normalize_instance_profile,
    project_instance_profile_event,
)


def test_normalize_instance_profile_projects_nested_branding_payload():
    profile = normalize_instance_profile(
        {
            "instance_profile": {
                "instance": {
                    "displayName": "小采",
                    "subtitle": "AI智能采购助手",
                },
                "branding": {
                    "logo": {
                        "light": "/assets/logo-xiaocai.svg",
                        "sidebar": "/assets/logo-xiaocai-wordmark.svg",
                    },
                },
                "ui": {
                    "chat": {
                        "uiLabels": {
                            "product_name": "小采",
                            "brand_tag": "AI智能采购助手",
                        },
                    },
                },
            },
        }
    )

    assert profile["product_name"] == "小采"
    assert profile["brand_tag"] == "AI智能采购助手"
    assert profile["logo_url"] == "/assets/logo-xiaocai.svg"
    assert profile["ui_labels"]["sidebar_logo_url"] == "/assets/logo-xiaocai-wordmark.svg"


def test_project_instance_profile_event_keeps_core_flat_profile_shape():
    event = project_instance_profile_event({"type": "instance_profile", "trace_id": "trace-1"})

    assert event["instance_profile"]["product_name"] == "小采"
    assert event["instance_profile"]["ui_labels"]["sidebar_logo_url"] == "/assets/logo-xiaocai-wordmark.svg"
    assert event["product_name"] == "小采"
    assert event["trace_id"] == "trace-1"


def test_normalize_instance_profile_replaces_generic_flare_fallback():
    profile = normalize_instance_profile(
        {
            "product_name": "F.L.A.R.E",
            "brand_tag": "项目协同工作台",
        }
    )

    assert profile["product_name"] == "小采"
    assert profile["brand_tag"] == "AI智能采购助手"
    assert profile["ui_labels"]["sidebar_logo_url"] == "/assets/logo-xiaocai-wordmark.svg"
