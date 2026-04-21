from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app


def _auth_token(client: TestClient, user_id: str = "admin") -> str:
    response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": user_id})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_settings_integrations_flow():
    client = TestClient(create_app())
    token = _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    list_response = client.get("/settings/integrations", headers=headers)
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["domain_injection_mode"] == "assist"
    assert isinstance(data["connectors"], list)
    assert any(item["key"] == "xiaocai_db" for item in data["connectors"])

    patch_mode_response = client.patch(
        "/settings/domain-injection-mode",
        headers=headers,
        json={"domain_injection_mode": "enforce"},
    )
    assert patch_mode_response.status_code == 200
    assert patch_mode_response.json()["domain_injection_mode"] == "enforce"

    toggle_response = client.patch(
        "/settings/connectors/mcp_gateway",
        headers=headers,
        json={"enabled": True},
    )
    assert toggle_response.status_code == 200
    assert toggle_response.json()["enabled"] is True

    test_response = client.post("/settings/connectors/xiaocai_db/test", headers=headers)
    assert test_response.status_code == 200
    assert test_response.json()["status"] in {"connected", "error"}


def test_instance_integration_status_summary():
    client = TestClient(create_app())
    response = client.get("/instance/integration-status")
    assert response.status_code == 200
    payload = response.json()
    assert "generated_at" in payload
    assert isinstance(payload.get("connectors"), list)
    assert payload["connectors"]
    assert set(payload["connectors"][0].keys()) == {
        "key",
        "enabled",
        "status",
        "health",
        "latency_ms",
        "updated_at",
    }
