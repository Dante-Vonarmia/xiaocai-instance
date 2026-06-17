import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.settings import get_settings


def _headers(client: TestClient, user_id: str = "stream-artifact-user") -> dict[str, str]:
    response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": user_id})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _sse_events(response_text: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for block in response_text.split("\n\n"):
        if not block.strip():
            continue
        event_type = ""
        data_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith("event:"):
                event_type = line.removeprefix("event:").strip()
            if line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").strip())
        if not data_lines:
            continue
        events.append((event_type, json.loads("\n".join(data_lines))))
    return events


def test_structured_reasoning_artifact_projects_to_canvas_state(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _headers(client)
    client.post("/projects/bind", headers=headers, json={"project_id": "proj-artifact-projection"})

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {
                "type": "canvas_state",
                "mode_key": "requirement_intake",
                "canvas_state": {
                    "artifact_document": {"title": "需求文档", "sections": [{"key": "overview", "label": "项目概述"}]},
                    "collected": [],
                    "missing": [{"field_key": "预算金额", "label": "预算金额"}],
                    "progress": 0,
                },
            }
            yield {
                "type": "structured_package",
                "mode_key": "requirement_intake",
                "structured_package": {
                    "field_groups": [{"key": "objective_scope", "label": "采购目标与范围"}],
                    "fields": [
                        {"group_key": "objective_scope", "field_key": "采购目的", "label": "采购目的", "value": "培训室改造"},
                        {"group_key": "objective_scope", "field_key": "预算金额", "label": "预算金额", "value": None},
                    ],
                },
            }
            yield {
                "type": "patch_event",
                "payload": {
                    "structured_reasoning": {
                        "artifact_document": {
                            "artifact_type": "requirements_document",
                            "content": "# 培训室改造采购需求\n\n## 项目概述\n\n用于内部培训。",
                            "content_format": "markdown",
                            "title": "培训室改造采购需求",
                        },
                        "field_extraction": {
                            "confirmed_fields": [
                                {"field_key": "采购目的", "value": "培训室改造", "confidence": 0.95},
                            ],
                            "field_state_patches": [
                                {"field_key": "预算金额", "value": None, "selected_action": "ask"},
                            ],
                        },
                        "question_planner": {
                            "next_question": {
                                "field_key": "预算金额",
                                "question_text": "预算金额是多少？",
                            },
                        },
                        "node_result": {
                            "next_actions": [{"action_key": "continue_collection"}],
                        },
                    },
                },
            }
            yield {"type": "done", "session_id": "sess-artifact-projection"}

        mock_stream.return_value = mock_generator()
        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "帮我梳理培训室改造采购需求",
                "session_id": "sess-artifact-projection",
                "context": {"project_id": "proj-artifact-projection", "mode": "requirement_intake"},
            },
        )

    assert response.status_code == 200
    canvas_events = [payload for event_type, payload in _sse_events(response.text) if event_type == "canvas_state"]
    assert len(canvas_events) == 2
    projected_state = canvas_events[-1]["canvas_state"]
    assert projected_state["artifact_document"]["content"].startswith("# 培训室改造采购需求")
    assert projected_state["artifact_document"]["procurement_packages"][0]["title"] == "采购目标与范围"
    assert projected_state["artifact_document"]["missing_questions"] == ["预算金额是多少？"]
    assert projected_state["collected"][0]["field_key"] == "采购目的"
    assert projected_state["missing"][0]["field_key"] == "预算金额"


def test_stream_without_structured_artifact_does_not_project_canvas(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _headers(client, user_id="stream-no-artifact-user")

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {"type": "text.delta", "channel": "assistant", "delta": "我先梳理需求。"}
            yield {"type": "patch_event", "payload": {"current_question": {"field_key": "预算金额"}}}
            yield {"type": "done", "session_id": "sess-no-artifact-projection"}

        mock_stream.return_value = mock_generator()
        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "帮我梳理采购需求",
                "session_id": "sess-no-artifact-projection",
                "context": {"mode": "requirement_intake"},
            },
        )

    assert response.status_code == 200
    assert [event_type for event_type, _ in _sse_events(response.text)].count("canvas_state") == 0

