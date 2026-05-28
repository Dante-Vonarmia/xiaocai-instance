from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.domains.router import _load_procurement_fields_payload


def test_get_procurement_domain_fields():
    _load_procurement_fields_payload.cache_clear()
    client = TestClient(create_app())
    response = client.get("/v1/domains/procurement/fields")
    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "procurement"
    assert payload["pack_id"] == "xiaocai"
    assert "field_groups" in payload
    assert "fields" in payload
    assert isinstance(payload["fields"], list)
    assert len(payload["fields"]) == 81
    assert payload["field_groups"]["required"][0]["key"] == "项目名称"


def test_get_unknown_domain_fields_returns_404():
    client = TestClient(create_app())
    response = client.get("/v1/domains/unknown/fields")
    assert response.status_code == 404
