import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.sources.ingestion import SourceIngestionOutcome, ingest_source_for_kernel
from xiaocai_instance_api.storage.source_store import SourceRecord
import xiaocai_instance_api.sources.router as source_router_module


@pytest.fixture
def client(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("UPLOAD_MAX_SIZE_BYTES", "16")
    monkeypatch.setattr(
        source_router_module,
        "ingest_source_for_kernel",
        lambda record: SourceIngestionOutcome(source_id=record.source_id, status="stored", chunk_count=1),
    )
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
    assert upload_response.json()["status"] == "ready"
    assert upload_response.json()["folder_name"] == "合同资料"

    list_response = client.get(
        "/sources",
        headers={"Authorization": f"Bearer {token}"},
        params={"project_id": "proj-source-1"},
    )
    assert list_response.status_code == 200
    assert len(list_response.json()["sources"]) == 1
    assert list_response.json()["sources"][0]["status"] == "ready"

    delete_response = client.delete(
        f"/sources/{source_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"project_id": "proj-source-1"},
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


@pytest.mark.parametrize(
    ("filename", "mime_type"),
    [
        ("demo.pdf", "application/pdf"),
        ("demo.doc", "application/msword"),
        ("demo.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("demo.xls", "application/vnd.ms-excel"),
        ("demo.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("demo.csv", "text/csv"),
        ("demo.txt", "text/plain"),
        ("demo.md", "text/markdown"),
        ("demo.png", "image/png"),
        ("demo.jpg", "image/jpeg"),
        ("demo.jpeg", "image/jpeg"),
        ("demo.webp", "image/webp"),
    ],
)
def test_source_upload_accepts_flare_composer_extensions(client, filename, mime_type):
    token = _auth_token(client, user_id=f"source-user-{filename}")
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-source-flare-extensions"},
    )
    assert bind_response.status_code == 200

    upload_response = client.post(
        "/files/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"project_id": "proj-source-flare-extensions"},
        files={"file": (filename, io.BytesIO(b"x"), mime_type)},
    )
    assert upload_response.status_code == 200
    assert upload_response.json()["status"] == "ready"


def test_source_upload_ingests_saved_file_for_kernel(client, monkeypatch):
    token = _auth_token(client, user_id="source-user-ingest")
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": "proj-source-ingest"},
    )
    assert bind_response.status_code == 200

    captured = {}

    def fake_ingest(record):
        captured["source_id"] = record.source_id
        captured["project_id"] = record.project_id
        captured["storage_path_exists"] = Path(record.storage_path).exists()
        return SourceIngestionOutcome(source_id=record.source_id, status="stored", chunk_count=2)

    monkeypatch.setattr(source_router_module, "ingest_source_for_kernel", fake_ingest)

    upload_response = client.post(
        "/files/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"project_id": "proj-source-ingest"},
        files={"file": ("requirement.md", io.BytesIO(b"chair"), "text/markdown")},
    )

    assert upload_response.status_code == 200
    body = upload_response.json()
    assert body["source_id"] == captured["source_id"]
    assert captured["project_id"] == "proj-source-ingest"
    assert captured["storage_path_exists"] is True
    assert body["ingestion_status"] == "stored"
    assert body["ingestion_chunk_count"] == 2


def test_ingest_source_for_kernel_uses_source_id_for_flare_knowledge(tmp_path):
    source_path = tmp_path / "requirement.md"
    source_path.write_text("采购 20 把办公椅，预算 20000 元。", encoding="utf-8")
    record = SourceRecord(
        source_id="src_test_ingest",
        project_id="proj-ingest",
        user_id="source-user-ingest",
        owner_user_id="source-user-ingest",
        visibility="private",
        session_id="sess-ingest",
        folder_name="默认文件夹",
        file_name="requirement.md",
        file_size=source_path.stat().st_size,
        mime_type="text/markdown",
        source_type="upload_attachment",
        date_bucket="today",
        time_bucket="evening",
        context_priority=100,
        storage_path=str(source_path),
        status="available",
        created_at="2026-05-18T00:00:00Z",
    )
    captured = {}

    def fake_extract(path, *, mime_type, filename):
        captured["extract_path"] = path
        captured["mime_type"] = mime_type
        captured["filename"] = filename
        return source_path.read_text(encoding="utf-8")

    def fake_ingest(**kwargs):
        captured.update(kwargs)
        return {"status": "stored", "chunk_count": 1}

    outcome = ingest_source_for_kernel(
        record,
        extract_text_fn=fake_extract,
        ingest_record_fn=fake_ingest,
    )

    assert outcome.status == "stored"
    assert outcome.chunk_count == 1
    assert captured["extract_path"] == source_path
    assert captured["source_id"] == "src_test_ingest"
    assert captured["project_id"] == "proj-ingest"
    assert captured["user_id"] == "source-user-ingest"
    assert captured["content"] == "采购 20 把办公椅，预算 20000 元。"


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
    assert mark_response.json()["status"] == "ready"

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
