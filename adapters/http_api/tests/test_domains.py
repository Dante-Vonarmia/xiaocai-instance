from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app


def test_get_procurement_domain_fields():
    client = TestClient(create_app())
    response = client.get("/v1/domains/procurement/fields")
    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "procurement"
    assert "field_groups" in payload
    assert "fields" in payload
    assert isinstance(payload["fields"], list)


def test_get_unknown_domain_fields_returns_404():
    client = TestClient(create_app())
    response = client.get("/v1/domains/unknown/fields")
    assert response.status_code == 404
