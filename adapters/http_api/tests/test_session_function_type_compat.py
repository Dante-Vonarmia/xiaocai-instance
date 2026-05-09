from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app


def _auth_token(client: TestClient, user_id: str) -> str:
    response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": user_id})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_auto_session_list_includes_legacy_function_type():
    client = TestClient(create_app())
    token = _auth_token(client, user_id="function-type-compat-user")
    headers = {"Authorization": f"Bearer {token}"}

    bind_response = client.post(
        "/projects/bind",
        headers=headers,
        json={"project_id": "proj-function-type-compat"},
    )
    assert bind_response.status_code == 200

    legacy_response = client.post(
        "/sessions",
        headers=headers,
        json={
            "project_id": "proj-function-type-compat",
            "title": "旧会话",
            "function_type": "chat_component_debug",
        },
    )
    assert legacy_response.status_code == 200

    auto_response = client.post(
        "/sessions",
        headers=headers,
        json={
            "project_id": "proj-function-type-compat",
            "title": "新会话",
            "function_type": "auto",
        },
    )
    assert auto_response.status_code == 200

    list_response = client.get(
        "/sessions",
        headers=headers,
        params={"project_id": "proj-function-type-compat", "function_type": "auto"},
    )
    assert list_response.status_code == 200
    session_ids = {item["sessionId"] for item in list_response.json()["sessions"]}
    assert legacy_response.json()["sessionId"] in session_ids
    assert auto_response.json()["sessionId"] in session_ids
