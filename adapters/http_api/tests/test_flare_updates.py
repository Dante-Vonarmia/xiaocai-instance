from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.flare_updates import service


def test_flare_updates_status_endpoint_reports_runtime_gate(monkeypatch) -> None:
    service._CACHE = None

    def latest_equals_installed(package: str) -> str | None:
        return service.installed_version(package)

    monkeypatch.setattr(service, "latest_pypi_version", latest_equals_installed)
    client = TestClient(create_app())

    response = client.get("/flare-updates/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"aligned", "attention_required"}
    assert payload["update_count"] == 0
    assert payload["packages"]
    assert payload["runtime_gate"]["current_question_projected"] is False
    assert payload["runtime_gate"]["composer_chooser_projected"] is False
