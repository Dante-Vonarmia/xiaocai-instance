from xiaocai_instance_api.chat.orchestration.field_candidates import normalize_candidate_payload
from xiaocai_instance_api.chat.router import _build_pending_contract


def test_candidate_normalizer_accepts_canonical_category_candidate():
    normalized = normalize_candidate_payload({
        "candidate_fields": [{
            "field_key": "一级品类",
            "value": "活动",
            "source": "model_inferred",
            "confidence": 0.74,
            "evidence": "用户提到活动落地",
        }]
    })

    assert normalized["rejected_candidates"] == []
    candidate = normalized["candidate_fields"][0]
    assert candidate["field_key"] == "一级品类"
    assert candidate["value"] == "活动"
    assert candidate["source"] == "model_inferred"
    assert candidate["confidence"] == 0.74
    assert candidate["evidence"] == "用户提到活动落地"
    assert candidate["normalization_status"] == "needs_confirmation"


def test_candidate_normalizer_maps_single_field_alias_to_canonical_field():
    normalized = normalize_candidate_payload({
        "field_candidates": [{
            "field": "影响范围",
            "value": "上海办公室",
            "source": "model_inferred",
        }]
    })

    assert normalized["rejected_candidates"] == []
    candidate = normalized["candidate_fields"][0]
    assert candidate["field_key"] == "影响范围（部门/区域）"
    assert candidate["raw_field_key"] == "影响范围"
    assert candidate["canonicalization"] == "alias"


def test_candidate_normalizer_reads_nested_intake_result_candidates():
    normalized = normalize_candidate_payload({
        "intake_result": {
            "structured_fields": [{
                "key": "交付地点",
                "value": "上海",
                "origin": "model_inferred",
            }]
        }
    })

    assert normalized["rejected_candidates"] == []
    candidate = normalized["candidate_fields"][0]
    assert candidate["field_key"] == "交付地点"
    assert candidate["value"] == "上海"
    assert candidate["source"] == "model_inferred"


def test_candidate_normalizer_rejects_alias_that_requires_split():
    normalized = normalize_candidate_payload({
        "candidate_fields": [{
            "field_key": "数量和单位",
            "value": "120套",
        }]
    })

    assert normalized["candidate_fields"] == []
    rejection = normalized["rejected_candidates"][0]
    assert rejection["field_key"] == "数量和单位"
    assert rejection["rejection_reason"] == "multi_field_alias_requires_split"


def test_candidate_normalizer_does_not_reject_category_value_locally():
    normalized = normalize_candidate_payload({
        "candidate_fields": [{
            "field_key": "一级品类",
            "value": "开放式办公区",
        }]
    })

    assert normalized["rejected_candidates"] == []
    candidate = normalized["candidate_fields"][0]
    assert candidate["field_key"] == "一级品类"
    assert candidate["value"] == "开放式办公区"
    assert candidate["normalization_status"] == "needs_confirmation"


def test_candidate_normalizer_does_not_trust_provider_confirmed_status():
    normalized = normalize_candidate_payload({
        "candidate_fields": [{
            "field_key": "二级品类",
            "value": "服务器",
            "status": "confirmed",
            "source": "model_inferred",
        }]
    })

    assert normalized["rejected_candidates"] == []
    candidate = normalized["candidate_fields"][0]
    assert candidate["normalization_status"] == "needs_confirmation"


def test_pending_contract_preserves_candidates_without_confirming_them():
    pending = _build_pending_contract(
        {
            "missing_fields": ["一级品类"],
            "current_question": {
                "field_key": "一级品类",
                "question_text": "请确认一级品类。",
            },
            "candidate_fields": [{
                "field_key": "一级品类",
                "value": "活动",
                "source": "model_inferred",
            }],
        },
        session_id="candidate-session",
        mode="requirement_intake",
    )

    assert pending is not None
    assert pending["candidate_fields"][0]["field_key"] == "一级品类"
    assert pending["candidate_fields"][0]["value"] == "活动"
    assert pending["candidate_fields"][0]["normalization_status"] == "needs_confirmation"
    assert "confirmed_fields" not in pending
