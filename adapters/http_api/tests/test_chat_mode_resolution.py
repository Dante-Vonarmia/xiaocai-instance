from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.chat.orchestration.mode_resolution import (
    INTAKE_MODE_ALIAS,
    resolve_effective_mode,
)


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def auth_token(client):
    response = client.post(
        "/auth/exchange",
        json={"mock": True, "mock_user_id": "mode-resolution-user"},
    )
    return response.json()["access_token"]


def test_real_frontend_procurement_intake_message_enters_requirement_canvas():
    mode = resolve_effective_mode(
        request_mode=None,
        session_mode=None,
        message="我要采购一批办公桌椅，用于上海新办公室开放办公区，请先帮我梳理需求。",
    )

    assert mode is None


def test_missing_request_mode_does_not_keep_intake_session_sticky():
    mode = resolve_effective_mode(
        request_mode=None,
        session_mode="requirement_intake",
        message="我要举办一台活动，要做哪些采购准备？",
    )

    assert mode is None


def test_explicit_auto_request_does_not_keep_intake_session_sticky():
    mode = resolve_effective_mode(
        request_mode="auto",
        session_mode="requirement_intake",
        message="继续",
    )

    assert mode == "auto"


def test_explicit_downstream_mode_is_not_overridden_by_intake_terms():
    mode = resolve_effective_mode(
        request_mode="intelligent_sourcing",
        session_mode=None,
        message="我要采购办公椅，请先帮我梳理需求。",
    )

    assert mode == "intelligent_sourcing"


def test_generic_auto_chat_stays_auto():
    mode = resolve_effective_mode(
        request_mode="auto",
        session_mode=None,
        message="今天状态怎么样？",
    )

    assert mode == "auto"


def test_supplier_request_does_not_force_requirement_canvas():
    mode = resolve_effective_mode(
        request_mode=None,
        session_mode=None,
        message="帮我找办公家具供应商。",
    )

    assert mode is None


def test_chat_stream_does_not_infer_mode_from_real_frontend_payload_without_mode(client, auth_token):
    captured = {}
    bind_response = client.post(
        "/projects/bind",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"project_id": "project-real-frontend"},
    )
    assert bind_response.status_code == 200

    async def fake_stream(self, **kwargs):
        _ = self
        captured["context"] = kwargs["context"]
        yield {"type": "done", "message": "普通回答。"}

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream", fake_stream):
        response = client.post(
            "/chat/stream",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "session_id": "sess-real-frontend-no-mode",
                "command": "send_message",
                "project_id": "project-real-frontend",
                "user_id": "mode-resolution-user",
                "payload": {
                    "message": "我要采购一批办公桌椅，用于上海新办公室开放办公区，请先帮我梳理需求。",
                    "project_id": "project-real-frontend",
                    "user_id": "mode-resolution-user",
                },
            },
        )

    assert response.status_code == 200
    assert captured["context"].get("mode") is None
    assert "普通回答。" in response.text
    assert '"mode_key": "requirement_intake"' not in response.text
    assert "event: canvas_state" not in response.text
