from unittest.mock import patch
import io

import pytest
from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.chat.orchestration.flare_intake_contract import build_flare_intake_contract
from xiaocai_instance_api.chat.orchestration.prior_context import build_procurement_prior_context
from xiaocai_instance_api.chat.pending_policy import apply_confidence_policy_to_pending_contract
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


def test_chat_run_injects_template_recommendation_prior(client, auth_token):
    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "已按模板建议生成",
            "cards": [],
            "session_id": "test-prior-rules-session",
            "metadata": {},
        }

        response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "请帮我做活动需求梳理",
                "session_id": "test-prior-rules-session",
                "context": {
                    "mode": "requirement_canvas",
                    "采购目的": "支持品牌活动落地",
                    "使用场景": "线下活动执行",
                },
            },
        )

        assert response.status_code == 200
        kernel_context = mock_chat.await_args.kwargs["context"]
        domain_prior = kernel_context["domain_prior"]
        template_recommendation = domain_prior["template_recommendation"]
        missing_fields_with_priority = domain_prior["missing_fields_with_priority"]
        missing_fields_with_relevance = domain_prior["missing_fields_with_relevance"]
        clarification_policy = kernel_context["clarification_policy"]
        category_prior = kernel_context["category_prior"]
        confidence_policy = kernel_context["confidence_policy"]
        field_definitions = kernel_context["field_definitions"]
        definitions_by_key = {item["key"]: item for item in field_definitions}

        assert template_recommendation["stage"] == "requirement_collection"
        assert len(template_recommendation["matched_rules"]) >= 1
        assert len(template_recommendation["candidate_pool"]) >= 1
        assert len(missing_fields_with_priority) >= 1
        assert len(missing_fields_with_relevance) >= 1
        assert domain_prior["readiness_score"] > 0
        assert template_recommendation["candidate_pool"][0]["template_key"] == "activity_analysis_standard"
        assert template_recommendation["candidate_pool"][0]["base_weight"] == 0.55
        assert template_recommendation["candidate_pool"][0]["score"] > 0
        assert template_recommendation["candidate_pool"][0]["status"] in {"candidate", "needs_more_context"}
        assert template_recommendation["candidate_pool"][0]["fallback_template"] == "clarification_questions_first"
        assert "field_key" in missing_fields_with_priority[0]
        assert "priority_score" in missing_fields_with_priority[0]
        assert "stage_priority" in missing_fields_with_priority[0]
        assert clarification_policy["ask_missing_fields_one_by_one"] is True
        assert "relevance" in missing_fields_with_relevance[0]
        assert "action" in missing_fields_with_relevance[0]
        assert isinstance(clarification_policy["priority_order"], list)
        assert "technical_requirements" in clarification_policy["defer_to_canvas"]
        assert len(category_prior["candidate_pool"]) >= 1
        assert category_prior["confidence_score"] > 0
        assert category_prior["resolved_level1_category"] == "活动"
        assert "allow_direct_commit" in confidence_policy
        assert "should_clarify_before_commit" in confidence_policy
        assert "action" in confidence_policy
        assert confidence_policy["action"] in {
            "proceed",
            "clarify_category_first",
            "clarify_requirement_first",
            "defer_to_canvas",
        }
        assert domain_prior["instruction_hints"]["preferred_category_path"] == category_prior["resolved_path"]
        assert domain_prior["instruction_hints"]["top_missing_field"] == clarification_policy["top_missing_field"]
        assert domain_prior["instruction_hints"]["clarification_action"] == confidence_policy["action"]
        assert domain_prior["instruction_hints"]["prefer_weighted_template_candidates"] is True
        assert "采购目的" in kernel_context["required_fields"]
        assert definitions_by_key["采购目的"]["priority"] == "required"
        assert definitions_by_key["采购目的"]["blocker"] is False
        assert definitions_by_key["采购目的"]["question"]
        assert definitions_by_key["使用场景"]["question"]
        assert definitions_by_key["一级品类"]["options"]
        assert any(item["value"] == "活动" for item in definitions_by_key["一级品类"]["options"])
        assert definitions_by_key["预算金额"]["question"]
        assert kernel_context["fields"]["采购目的"] == "支持品牌活动落地"
        assert kernel_context["fields"]["使用场景"] == "线下活动执行"
        assert "采购目的" not in kernel_context["required_missing"]


def test_chat_prior_keeps_project_name_out_of_chat_question_priority(client, auth_token):
    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_chat:
        mock_chat.return_value = {
            "message": "已进入需求梳理。",
            "cards": [],
            "session_id": "test-project-name-deferred-session",
            "metadata": {},
        }

        response = client.post(
            "/chat/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "我要采购一批测试服务器，请先帮我梳理采购需求并列出还缺的关键信息。",
                "session_id": "test-project-name-deferred-session",
                "context": {"mode": "requirement_canvas"},
            },
        )

        assert response.status_code == 200
        kernel_context = mock_chat.await_args.kwargs["context"]
        clarification_policy = kernel_context["clarification_policy"]
        domain_prior = kernel_context["domain_prior"]
        relevance_rows = domain_prior["missing_fields_with_relevance"]
        definitions_by_key = {item["key"]: item for item in kernel_context["field_definitions"]}

        assert "项目名称" in clarification_policy["defer_to_canvas"]
        assert clarification_policy["top_missing_field"] != "项目名称"
        assert clarification_policy["priority_order"][0] != "项目名称"
        assert relevance_rows[0]["action"] == "ask_in_chat"
        assert domain_prior["message_extracted_fields"]["数量"] == "1"
        assert domain_prior["message_extracted_fields"]["单位"] == "批"
        assert "一级品类" not in domain_prior["message_extracted_fields"]
        assert domain_prior["readiness_score"] < 0.35
        assert kernel_context["fields"]["数量"] == "1"
        assert kernel_context["fields"]["单位"] == "批"
        assert kernel_context["confirmed_fields"]["数量"] == "1"
        assert any(item["field_key"] == "数量" for item in kernel_context["field_history"])
        assert "一级品类" not in kernel_context["fields"]
        assert "二级品类" not in kernel_context["fields"]
        assert any(item["field_key"] == "一级品类" for item in kernel_context["candidate_fields"])
        assert any(item["field_key"] == "二级品类" for item in kernel_context["candidate_fields"])
        assert kernel_context["field_definitions"][0]["key"] == "项目名称"
        assert definitions_by_key["项目名称"]["priority"] == "optional"
        assert definitions_by_key["项目名称"]["completion_required"] is True
        assert definitions_by_key["预算金额"]["question"]
        assert definitions_by_key["一级品类"]["options"]
        assert kernel_context["field_semantics"]["项目名称"]["criticality"] == "supplementary"
        assert "项目名称" not in kernel_context.get("intake_core_fields", [])
        assert "项目名称" in kernel_context["required_missing"]
        assert kernel_context["confidence_policy"]["should_clarify_before_commit"] is True
        assert clarification_policy["ask_missing_fields_one_by_one"] is True
        assert domain_prior["instruction_hints"]["defer_missing_fields_to_workbench"] is False


def test_office_furniture_terms_become_canonical_category_candidates():
    message = "我要采购一批办公桌椅，用于上海新办公室开放办公区，预算45万元，数量120套，2周内交付。请先帮我梳理需求。"
    prior = build_procurement_prior_context(
        kernel_context={},
        mode="requirement_canvas",
        user_message=message,
    )
    contract = build_flare_intake_contract(
        kernel_context={},
        domain_prior=prior.domain_prior,
        mode="requirement_canvas",
    )

    category_prior = prior.domain_prior["category_prior"]
    candidates_by_key = {item["field_key"]: item for item in contract["candidate_fields"]}

    assert category_prior["resolved_level1_category"] == "空间相关"
    assert category_prior["resolved_level2_category"] == "办公家具、电器"
    assert category_prior["confidence_score"] >= 0.4
    assert "一级品类" not in contract["confirmed_fields"]
    assert "二级品类" not in contract["confirmed_fields"]
    assert candidates_by_key["一级品类"]["normalized_value"] == "空间相关"
    assert candidates_by_key["二级品类"]["normalized_value"] == "办公家具、电器"
    assert candidates_by_key["一级品类"]["normalization_status"] == "needs_confirmation"


def test_sourcing_prior_does_not_hard_block_on_missing_ranking_fields():
    prior = build_procurement_prior_context(
        kernel_context={"产品/服务": "测试服务器"},
        mode="intelligent_sourcing",
        user_message="我要采购一批测试服务器，直接先给供应商。",
    )

    domain_prior = prior.domain_prior
    assert domain_prior["active_stage"] == "sourcing"
    assert domain_prior["missing_fields"] == []
    assert "预算金额" not in domain_prior["missing_fields"]
    assert "交付地点" not in domain_prior["missing_fields"]
    assert domain_prior["instruction_hints"]["ask_for_missing_required_fields_before_finalizing"] is False


def test_chat_run_keeps_confidence_policy_hidden_without_native_pending(client, auth_token):
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
        assert "confidence_policy" in kernel_context


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


def test_confidence_policy_does_not_create_pending_contract_outside_intake():
    pending_contract = apply_confidence_policy_to_pending_contract(
        pending_contract=None,
        confidence_policy={
            "action": "clarify_category_first",
            "rationale": "low_category_confidence",
        },
        clarification_policy={},
        category_prior={},
        session_id="test-analysis-session",
        mode="analysis_mode",
    )

    assert pending_contract is None


def test_confidence_policy_does_not_create_legacy_pending_contract_inside_intake():
    pending_contract = apply_confidence_policy_to_pending_contract(
        pending_contract=None,
        confidence_policy={
            "action": "clarify_category_first",
            "rationale": "low_category_confidence",
        },
        clarification_policy={},
        category_prior={"candidate_pool": [{"level1_category": "工业MRO"}]},
        session_id="test-intake-session",
        mode="requirement_canvas",
    )

    assert pending_contract is None
