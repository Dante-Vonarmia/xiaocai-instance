from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app


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
        assert confidence_policy["action"] in {"proceed", "clarify_category_first", "clarify_requirement_first", "defer_to_canvas"}
        assert domain_prior["instruction_hints"]["preferred_category_path"] == category_prior["resolved_path"]
        assert domain_prior["instruction_hints"]["top_missing_field"] == clarification_policy["top_missing_field"]
        assert domain_prior["instruction_hints"]["clarification_action"] == confidence_policy["action"]
        assert domain_prior["instruction_hints"]["prefer_weighted_template_candidates"] is True


def test_chat_run_uses_confidence_policy_to_build_pending_contract(client, auth_token):
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
        pending_contract = response.json()["metadata"]["pending_contract"]
        assert pending_contract["command_type"] == "clarify_category_first"
        assert pending_contract["gate"]["reason"] == "low_category_confidence"
        assert pending_contract["current_question"]["field_key"] == "一级品类"
        assert pending_contract["next_actions"][0]["action_key"] == "clarify_category_first"
