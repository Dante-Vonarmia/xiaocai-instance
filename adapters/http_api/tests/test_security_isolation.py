import io

import pytest
from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def _token(client: TestClient, user_id: str) -> str:
    response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": user_id})
    assert response.status_code == 200
    return response.json()["access_token"]


def _bind_project(client: TestClient, token: str, project_id: str) -> None:
    response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": project_id},
    )
    assert response.status_code == 200


def test_conversation_private_isolation_same_project(client):
    project_id = "proj-iso-conv"
    token_a = _token(client, "iso-user-a")
    token_b = _token(client, "iso-user-b")
    _bind_project(client, token_a, project_id)
    _bind_project(client, token_b, project_id)

    create_response = client.post(
        f"/projects/{project_id}/conversations",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"title": "A 的会话", "function_type": "requirement_canvas"},
    )
    assert create_response.status_code == 200
    conversation_id = create_response.json()["id"]
    assert create_response.json()["visibility"] == "private"

    list_b = client.get(
        f"/projects/{project_id}/conversations",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert list_b.status_code == 200
    assert all(item["id"] != conversation_id for item in list_b.json()["conversations"])

    detail_b = client.get(
        f"/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert detail_b.status_code == 404

    write_b = client.post(
        f"/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"content": "越权写入", "role": "user"},
    )
    assert write_b.status_code == 403


def test_source_list_download_and_delete_isolation(client):
    project_id = "proj-iso-source"
    token_a = _token(client, "iso-src-a")
    token_b = _token(client, "iso-src-b")
    _bind_project(client, token_a, project_id)
    _bind_project(client, token_b, project_id)

    upload_response = client.post(
        "/sources/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        data={"project_id": project_id, "folder_name": "隔离资料"},
        files={"file": ("owner-secret.txt", io.BytesIO(b"secret"), "text/plain")},
    )
    assert upload_response.status_code == 200
    source_id = upload_response.json()["source_id"]
    assert upload_response.json()["visibility"] == "private"

    list_b = client.get(
        "/sources",
        headers={"Authorization": f"Bearer {token_b}"},
        params={"project_id": project_id},
    )
    assert list_b.status_code == 200
    assert all(item["source_id"] != source_id for item in list_b.json()["sources"])

    download_b = client.get(
        f"/sources/{source_id}/download",
        headers={"Authorization": f"Bearer {token_b}"},
        params={"project_id": project_id},
    )
    assert download_b.status_code == 404

    delete_b = client.delete(
        f"/sources/{source_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        params={"project_id": project_id},
    )
    assert delete_b.status_code == 403


def test_retrieval_search_isolation(client):
    project_id = "proj-iso-retrieval"
    token_a = _token(client, "iso-ret-a")
    token_b = _token(client, "iso-ret-b")
    _bind_project(client, token_a, project_id)
    _bind_project(client, token_b, project_id)

    upload_response = client.post(
        "/sources/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        data={"project_id": project_id, "folder_name": "检索"},
        files={"file": ("secret-a-hit.txt", io.BytesIO(b"a"), "text/plain")},
    )
    assert upload_response.status_code == 200

    search_b = client.post(
        "/retrieval/search",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"project_id": project_id, "query": "secret-a-hit", "limit": 10},
    )
    assert search_b.status_code == 200
    assert search_b.json()["scope"]["user_id"] == "iso-ret-b"
    assert len(search_b.json()["hits"]) == 0

    search_a = client.post(
        "/retrieval/search",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"project_id": project_id, "query": "secret-a-hit", "limit": 10},
    )
    assert search_a.status_code == 200
    assert len(search_a.json()["hits"]) == 1


def test_artifact_isolation_same_project(client):
    project_id = "proj-iso-artifact"
    token_a = _token(client, "iso-art-a")
    token_b = _token(client, "iso-art-b")
    _bind_project(client, token_a, project_id)
    _bind_project(client, token_b, project_id)

    create_conversation = client.post(
        f"/projects/{project_id}/conversations",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"title": "artifact 会话"},
    )
    assert create_conversation.status_code == 200
    conversation_id = create_conversation.json()["id"]

    create_artifact = client.post(
        f"/artifacts/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"artifact_type": "analysis", "content": {"summary": "A only"}},
    )
    assert create_artifact.status_code == 200
    artifact_id = create_artifact.json()["id"]

    get_b = client.get(
        f"/artifacts/{artifact_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_b.status_code == 404

    export_b = client.get(
        f"/artifacts/{artifact_id}/export",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert export_b.status_code == 404

    list_b = client.get(
        "/artifacts",
        headers={"Authorization": f"Bearer {token_b}"},
        params={"project_id": project_id},
    )
    assert list_b.status_code == 200
    assert all(item["id"] != artifact_id for item in list_b.json()["artifacts"])
