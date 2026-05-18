from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app


def _auth_token(client: TestClient, user_id: str = "admin") -> str:
    response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": user_id})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_config_draft_read_write_flow():
    client = TestClient(create_app())
    token = _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    missing_response = client.get(
        "/settings/config-drafts/procurement_domain_assets",
        params={"scope": "procurement"},
        headers=headers,
    )
    assert missing_response.status_code == 200
    assert missing_response.json()["draft"] is None

    save_response = client.put(
        "/settings/config-drafts/procurement_domain_assets",
        headers=headers,
        json={
            "scope": "procurement",
            "base_version": "v1",
            "payload": {
                "fields": {"required": [{"key": "product_name", "label": "产品名称"}]},
                "category": {"ownerNames": ["办公行政"]},
                "prompts": {"askOrder": ["product_name"]},
            },
        },
    )
    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["config_key"] == "procurement_domain_assets"
    assert saved["scope"] == "procurement"
    assert saved["status"] == "draft"
    assert saved["updated_by"] == "admin"

    lookup_response = client.get(
        "/settings/config-drafts/procurement_domain_assets",
        params={"scope": "procurement"},
        headers=headers,
    )
    assert lookup_response.status_code == 200
    draft = lookup_response.json()["draft"]
    assert draft["payload"]["category"]["ownerNames"] == ["办公行政"]

    delete_response = client.delete(
        "/settings/config-drafts/procurement_domain_assets",
        params={"scope": "procurement"},
        headers=headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    reset_lookup_response = client.get(
        "/settings/config-drafts/procurement_domain_assets",
        params={"scope": "procurement"},
        headers=headers,
    )
    assert reset_lookup_response.status_code == 200
    assert reset_lookup_response.json()["draft"] is None


def test_config_draft_rejects_invalid_key():
    client = TestClient(create_app())
    token = _auth_token(client)
    response = client.get(
        "/settings/config-drafts/Invalid Key",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
