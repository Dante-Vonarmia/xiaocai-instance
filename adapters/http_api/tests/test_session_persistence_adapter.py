from flare_kernel.contracts.context import ContextContract

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.session_persistence_adapter import XiaocaiSessionPersistenceAdapter


def _build_repository() -> XiaocaiSessionPersistenceAdapter:
    settings = get_settings()
    return XiaocaiSessionPersistenceAdapter(
        db_path=settings.storage_db_path,
        db_url=settings.storage_db_url,
    )


def test_create_and_load_session_record_round_trip():
    repository = _build_repository()

    created = repository.create_session_record(
        {
            "session_id": "sess_round_trip",
            "project_id": "proj-round-trip",
            "title": "Round Trip",
            "preview": "session preview",
            "title_source": "manual",
            "status": "active",
            "user_id": "user-round-trip",
            "function_type": "requirement_canvas",
            "context": ContextContract(
                context_revision_id="ctx-rev-1",
                session_summary="summary",
                confirmed_fields={"budget": "1000"},
                missing_fields=["delivery_date"],
                notes=["keep it minimal"],
                updated_at="2026-04-30T00:00:00+00:00",
            ).model_dump(mode="python"),
            "created_at": "2026-04-30T00:00:00+00:00",
            "updated_at": "2026-04-30T00:00:00+00:00",
        }
    )

    loaded = repository.load_session_record("sess_round_trip")

    assert loaded == created
    assert loaded["context"]["context_revision_id"] == "ctx-rev-1"
    assert loaded["context"]["confirmed_fields"] == {"budget": "1000"}


def test_append_and_list_messages_with_flare_fields():
    repository = _build_repository()
    repository.create_session_record(
        {
            "session_id": "sess_messages",
            "project_id": "proj-messages",
            "title": "Messages",
            "preview": "",
            "title_source": "default",
            "status": "active",
            "user_id": "user-messages",
            "function_type": "intelligent_sourcing",
            "context": ContextContract().model_dump(mode="python"),
            "created_at": "2026-04-30T00:00:00+00:00",
            "updated_at": "2026-04-30T00:00:00+00:00",
        }
    )

    repository.append_session_messages(
        "sess_messages",
        [
            {
                "message_id": "msg_user_1",
                "session_id": "sess_messages",
                "role": "user",
                "content": "user content",
                "attachments": [{"name": "spec.pdf"}],
                "context_refs": [{"field": "budget"}],
                "knowledge_refs": [{"knowledge_id": "k-1"}],
                "created_at": "2026-04-30T00:00:01+00:00",
            },
            {
                "message_id": "msg_assistant_1",
                "session_id": "sess_messages",
                "role": "assistant",
                "content": "assistant content",
                "agent_status": {"state": "done"},
                "thinking_trace": "trace",
                "execution_trace": {"steps": ["a"]},
                "knowledge_search": {"queries": ["budget"]},
                "sourcing_candidates": {"items": ["supplier-a"]},
                "knowledge_citation": {"sources": ["doc-1"]},
                "context_usage": {"used_context_revision_id": "ctx-1"},
                "created_at": "2026-04-30T00:00:02+00:00",
            },
        ],
    )

    messages = repository.list_session_messages("sess_messages")

    assert [item["role"] for item in messages] == ["user", "assistant"]
    assert messages[0]["attachments"] == [{"name": "spec.pdf"}]
    assert messages[1]["agent_status"] == {"state": "done"}
    assert messages[1]["knowledge_search"] == {"queries": ["budget"]}


def test_context_round_trip_and_update_remains_consistent():
    repository = _build_repository()
    repository.create_session_record(
        {
            "session_id": "sess_context_update",
            "project_id": "proj-context",
            "title": "Context",
            "preview": "",
            "title_source": "default",
            "status": "active",
            "user_id": "user-context",
            "function_type": "requirement_canvas",
            "context": ContextContract(
                context_revision_id="ctx-initial",
                facts=[{"id": "fact-1", "text": "initial fact"}],
                updated_at="2026-04-30T00:00:00+00:00",
            ).model_dump(mode="python"),
            "created_at": "2026-04-30T00:00:00+00:00",
            "updated_at": "2026-04-30T00:00:00+00:00",
        }
    )

    original = repository.load_session_record("sess_context_update")
    assert original is not None

    updated = repository.save_session_record(
        {
            **original,
            "context": {
                **original["context"],
                "context_revision_id": "ctx-updated",
                "session_summary": "updated summary",
                "user_focus": ["budget", "delivery"],
                "response_priorities": ["precision"],
                "confirmed_fields": {"budget": "2000"},
                "missing_fields": ["spec"],
                "notes": ["note-1"],
                "turns": [
                    {
                        "turn_id": "turn-1",
                        "user_message": "need sourcing",
                        "assistant_message": "working on it",
                        "source_ids": ["src-1"],
                        "created_at": "2026-04-30T00:00:03+00:00",
                    }
                ],
                "evidence": [{"id": "ev-1", "source_id": "src-1", "snippet": "snippet"}],
                "facts": [{"id": "fact-2", "text": "updated fact"}],
                "inferences": [{"id": "inf-1", "text": "inference"}],
                "unknowns": [{"id": "unk-1", "text": "unknown"}],
                "source_attributions": [{"source_id": "src-1"}],
                "artifact_context": [{"artifact_id": "art-1"}],
                "sourcing_results": [{"round": 1, "items": [{"supplier": "A"}], "timestamp": "2026-04-30T00:00:04+00:00"}],
                "analysis_results": [{"version": 1, "payload": {"score": 10}, "timestamp": "2026-04-30T00:00:05+00:00"}],
                "rank_profile": {"weights": {"price": 0.7}},
                "rank_feedback_log": [{"type": "accept"}],
                "updated_at": "2026-04-30T00:00:06+00:00",
            },
            "updated_at": "2026-04-30T00:00:06+00:00",
        }
    )

    reloaded = repository.load_session_record("sess_context_update")

    assert reloaded == updated
    assert reloaded["context"]["context_revision_id"] == "ctx-updated"
    assert reloaded["context"]["rank_profile"] == {"weights": {"price": 0.7}}
    assert reloaded["context"]["sourcing_results"][0]["items"] == [{"supplier": "A"}]
