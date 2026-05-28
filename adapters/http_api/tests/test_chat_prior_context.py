from unittest.mock import patch
import io

import pytest
from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.settings import get_settings


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    response = client.post(
        "/auth/exchange",
        json={"mock": True, "mock_user_id": "test-user"},
    )
    return response.json()["access_token"]


def test_chat_run_does_not_inject_local_prior_or_questions(client, auth_token):
    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "FLARE 原生回复",
            "cards": [],
            "session_id": "test-no-local-prior-session",
            "metadata": {},
        }

        response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "请帮我做活动需求梳理",
                "session_id": "test-no-local-prior-session",
                "context": {
                    "mode": "requirement_canvas",
                    "采购目的": "支持品牌活动落地",
                    "使用场景": "线下活动执行",
                },
            },
        )

        assert response.status_code == 200
        kernel_context = mock_chat.await_args.kwargs["context"]

        assert kernel_context["mode"] == "requirement_canvas"
        assert kernel_context["采购目的"] == "支持品牌活动落地"
        assert kernel_context["使用场景"] == "线下活动执行"
        for local_key in (
            "analysis_template",
            "rfx_template",
            "domain_prior",
            "clarification_policy",
            "category_prior",
            "confidence_policy",
            "field_definitions",
            "required_fields",
            "required_missing",
            "candidate_fields",
            "field_history",
            "field_semantics",
        ):
            assert local_key not in kernel_context

def test_system_prompt_settings_are_not_projected_by_instance_api(client, auth_token):
    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "FLARE 原生回复。",
            "cards": [],
            "session_id": "test-no-system-prompt-session",
            "metadata": {},
        }

        response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "请基于现有需求生成RFX策略和需求分析报告",
                "session_id": "test-no-system-prompt-session",
                "context": {
                    "mode": "auto",
                    "技术要求": "办公桌符合人体工学",
                    "质量标准": "三年质保",
                    "验收口径": "数量、外观、稳定性验收",
                },
            },
        )

        assert response.status_code == 200
        kernel_context = mock_chat.await_args.kwargs["context"]

        assert kernel_context["技术要求"] == "办公桌符合人体工学"
        assert "domain_prompt_templates" not in kernel_context
        assert "domain_prompt_instructions" not in kernel_context
        assert "domain_system_prompt" not in kernel_context

def test_intake_context_does_not_receive_adapter_field_definitions(client, auth_token):
    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "FLARE 原生需求梳理回复。",
            "cards": [],
            "session_id": "test-no-field-definition-session",
            "metadata": {},
        }

        response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "我要采购一批测试服务器，请先帮我梳理采购需求并列出还缺的关键信息。",
                "session_id": "test-no-field-definition-session",
                "context": {"mode": "requirement_canvas"},
            },
        )

        assert response.status_code == 200
        kernel_context = mock_chat.await_args.kwargs["context"]

        assert kernel_context["mode"] == "requirement_canvas"
        for local_key in (
            "clarification_policy",
            "domain_prior",
            "field_definitions",
            "fields",
            "confirmed_fields",
            "candidate_fields",
            "field_history",
            "field_semantics",
            "required_missing",
            "intake_core_fields",
            "intake_supplementary_fields",
        ):
            assert local_key not in kernel_context

def test_chat_run_does_not_inject_confidence_policy_without_native_pending(client, auth_token):
    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "我先帮你整理一个基础分析框架。",
            "cards": [],
            "session_id": "test-confidence-session",
            "metadata": {},
        }

        response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "先帮我做需求分析",
                "session_id": "test-confidence-session",
                "context": {
                    "mode": "requirement_canvas",
                },
            },
        )

        assert response.status_code == 200
        body = response.json()
        kernel_context = mock_chat.await_args.kwargs["context"]
        assert body["message"] == "我先帮你整理一个基础分析框架。"
        assert "pending_contract" not in body["metadata"]
        assert "confidence_policy" not in kernel_context

def test_chat_run_keeps_selected_upload_source_context(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    local_client = TestClient(create_app())
    token_response = local_client.post(
        "/auth/exchange",
        json={"mock": True, "mock_user_id": "selected-upload-user"},
    )
    assert token_response.status_code == 200
    headers = {"Authorization": f"Bearer {token_response.json()['access_token']}"}
    project_id = "proj-selected-upload"

    bind_response = local_client.post(
        "/projects/bind",
        headers=headers,
        json={"project_id": project_id},
    )
    assert bind_response.status_code == 200

    upload_a = local_client.post(
        "/sources/upload",
        headers=headers,
        data={"project_id": project_id},
        files={"file": ("selected.txt", io.BytesIO(b"selected content"), "text/plain")},
    )
    upload_b = local_client.post(
        "/sources/upload",
        headers=headers,
        data={"project_id": project_id},
        files={"file": ("other.txt", io.BytesIO(b"other content"), "text/plain")},
    )
    assert upload_a.status_code == 200
    assert upload_b.status_code == 200
    selected_source_id = upload_a.json()["source_id"]
    other_source_id = upload_b.json()["source_id"]

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "已根据上传内容整理",
            "cards": [],
            "session_id": "test-selected-upload-session",
            "metadata": {},
        }

        response = local_client.post(
            "/chat/run",
            headers=headers,
            json={
                "message": "结合上传内容总结",
                "session_id": "test-selected-upload-session",
                "context": {
                    "project_id": project_id,
                    "context_refs": [{"source_id": selected_source_id}],
                },
            },
        )

    assert response.status_code == 200
    kernel_context = mock_chat.await_args.kwargs["context"]
    injected_source_ids = [item["source_id"] for item in kernel_context["context_refs"]]
    assert injected_source_ids == [selected_source_id]
    assert other_source_id not in injected_source_ids
