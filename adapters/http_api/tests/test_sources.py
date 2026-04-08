import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.settings import get_settings


@pytest.fixture
def client(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("UPLOAD_MAX_SIZE_BYTES", "16")
    get_settings.cache_clear()
    app = create_app()
    return TestClient(app)


def _auth_token(client: TestClient, user_id: str = "source-user") -> str:
    response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": user_id})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_source_upload_list_delete(client):
    token = _auth_token(client)
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-source-1"},
    )
    assert bind_response.status_code == 200

    upload_response = client.post(
        "/sources/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"project_id": "proj-source-1", "session_id": "sess-1", "folder_name": "合同资料"},
        files={"file": ("demo.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert upload_response.status_code == 200
    source_id = upload_response.json()["source_id"]
    assert upload_response.json()["status"] == "available"
    assert upload_response.json()["folder_name"] == "合同资料"

    list_response = client.get(
        "/sources",
        headers={"Authorization": f"Bearer {token}"},
        params={"project_id": "proj-source-1"},
    )
    assert list_response.status_code == 200
    assert len(list_response.json()["sources"]) == 1

    delete_response = client.delete(
        f"/sources/{source_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"project_id": "proj-source-1"},
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


def test_source_search_folder_and_mark_referenced(client):
    token = _auth_token(client, user_id="source-user-3")
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-source-3"},
    )
    assert bind_response.status_code == 200

    upload_a = client.post(
        "/sources/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"project_id": "proj-source-3", "folder_name": "供应商档案"},
        files={"file": ("supplier-a.txt", io.BytesIO(b"a"), "text/plain")},
    )
    assert upload_a.status_code == 200
    source_a = upload_a.json()["source_id"]

    upload_b = client.post(
        "/sources/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"project_id": "proj-source-3", "folder_name": "报价单"},
        files={"file": ("quote-b.txt", io.BytesIO(b"b"), "text/plain")},
    )
    assert upload_b.status_code == 200

    search_response = client.get(
        "/sources",
        headers={"Authorization": f"Bearer {token}"},
        params={"project_id": "proj-source-3", "q": "supplier"},
    )
    assert search_response.status_code == 200
    assert len(search_response.json()["sources"]) == 1
    assert search_response.json()["sources"][0]["file_name"] == "supplier-a.txt"

    folder_filter_response = client.get(
        "/sources",
        headers={"Authorization": f"Bearer {token}"},
        params={"project_id": "proj-source-3", "folder_name": "报价单"},
    )
    assert folder_filter_response.status_code == 200
    assert len(folder_filter_response.json()["sources"]) == 1
    assert folder_filter_response.json()["sources"][0]["folder_name"] == "报价单"

    mark_response = client.post(
        f"/sources/{source_a}/mark-referenced",
        headers={"Authorization": f"Bearer {token}"},
        params={"project_id": "proj-source-3"},
    )
    assert mark_response.status_code == 200
    assert mark_response.json()["status"] == "referenced"

    folder_summary_response = client.get(
        "/sources/folders",
        headers={"Authorization": f"Bearer {token}"},
        params={"project_id": "proj-source-3"},
    )
    assert folder_summary_response.status_code == 200
    folders = {item["folder_name"]: item for item in folder_summary_response.json()["folders"]}
    assert folders["供应商档案"]["file_count"] == 1
    assert folders["供应商档案"]["referenced_count"] == 1
    assert folders["报价单"]["file_count"] == 1
    assert folders["报价单"]["referenced_count"] == 0


def test_source_upload_validation(client):
    token = _auth_token(client, user_id="source-user-2")
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-source-2"},
    )
    assert bind_response.status_code == 200

    bad_ext = client.post(
        "/sources/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"project_id": "proj-source-2"},
        files={"file": ("demo.exe", io.BytesIO(b"bin"), "application/octet-stream")},
    )
    assert bad_ext.status_code == 400
    assert "file extension not allowed" in bad_ext.json()["detail"]

    too_large = client.post(
        "/sources/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"project_id": "proj-source-2"},
        files={"file": ("big.txt", io.BytesIO(b"1234567890-abcdefg"), "text/plain")},
    )
    assert too_large.status_code == 400
    assert "file too large" in too_large.json()["detail"]
