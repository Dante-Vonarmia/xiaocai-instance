from unittest.mock import patch

from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.chat.router import EMPTY_ASSISTANT_MESSAGE


def _auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/exchange",
        json={"mock": True, "mock_user_id": "projection-user"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_analysis_request_does_not_synthesize_structured_report(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _auth_headers(client)

    bind_response = client.post(
        "/projects/bind",
        headers=headers,
        json={"project_id": "proj-analysis-report"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {
                "type": "text.delta",
                "channel": "assistant",
                "delta": "我先生成需求分析和RFX策略初稿。",
            }
            yield {"type": "done", "session_id": "sess-analysis-report"}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "帮我生成RFX策略，预算45万，采购120张办公桌，上海交付，6月15日前完成。",
                "session_id": "sess-analysis-report",
                "context": {
                    "project_id": "proj-analysis-report",
                    "mode": "requirement_canvas",
                },
            },
        )

    assert response.status_code == 200
    assert "event: analysis_payload" not in response.text
    assert "需求分析与 RFX 策略报告" not in response.text
    assert "我先生成需求分析和RFX策略初稿。" in response.text
    assert "produce_output" not in response.text
    assert "当前步骤" not in response.text


def test_native_markdown_analysis_payload_passes_through_without_projection(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _auth_headers(client)

    bind_response = client.post(
        "/projects/bind",
        headers=headers,
        json={"project_id": "proj-analysis-native-markdown"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {
                "type": "analysis_payload",
                "markdown": "# 基于证据的回答\n\n## RFX (RFQ) 寻源策略框架",
            }
            yield {
                "type": "text.delta",
                "channel": "assistant",
                "delta": "| 模块 | 核心内容 |\n| --- | --- |\n| 项目概况 | 名称：办公空间桌椅采购<br>目的：支持员工入驻 |\n| 关键里程碑 | 05-25 供应商初筛 → 06-15 首批交付安装 |",
            }
            yield {"type": "done", "session_id": "sess-analysis-native-markdown"}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "检查一下这个需求，分析一下并生成RFX策略。",
                "session_id": "sess-analysis-native-markdown",
                "context": {
                    "project_id": "proj-analysis-native-markdown",
                    "mode": "requirement_canvas",
                },
            },
        )

    assert response.status_code == 200
    assert "基于证据的回答" in response.text
    assert response.text.count("event: analysis_payload") == 1
    assert "需求分析与 RFX 策略报告" not in response.text
    assert "名称：办公空间桌椅采购；目的：支持员工入驻" in response.text
    assert "05-25 供应商初筛 → 06-15 首批交付安装" in response.text


def test_terminal_markdown_analysis_payload_stays_on_complete_event(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _auth_headers(client)

    bind_response = client.post(
        "/projects/bind",
        headers=headers,
        json={"project_id": "proj-analysis-terminal-markdown"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {
                "type": "text.delta",
                "channel": "assistant",
                "delta": "项目概况：名称：办公空间桌椅采购<br>目的：支持员工入驻",
            }
            yield {
                "type": "complete",
                "session_id": "sess-analysis-terminal-markdown",
                "analysis_payload": {
                    "markdown": "# 基于证据的回答\n\n## 项目理解与核心需求\n\n## 市场现状和分析",
                },
            }

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "检查一下这个需求，分析一下并生成RFX策略。",
                "session_id": "sess-analysis-terminal-markdown",
                "context": {
                    "project_id": "proj-analysis-terminal-markdown",
                    "mode": "requirement_canvas",
                },
            },
        )

    assert response.status_code == 200
    complete_index = response.text.find("event: complete")
    assert "event: analysis_payload" not in response.text
    assert complete_index != -1
    assert "需求分析与 RFX 策略报告" not in response.text
    assert "项目概况：名称：办公空间桌椅采购" in response.text
    assert "目的：支持员工入驻" in response.text
    complete_segment = response.text[complete_index:]
    assert '"analysis_payload"' in complete_segment
    assert '"document"' not in complete_segment


def test_native_structured_analysis_payload_is_not_overridden(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _auth_headers(client)

    bind_response = client.post(
        "/projects/bind",
        headers=headers,
        json={"project_id": "proj-analysis-native-structured"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {
                "type": "analysis_payload",
                "document": {
                    "sections": [
                        {
                            "kind": "narrative",
                            "id": "native",
                            "title": "原生报告",
                            "content": "FLARE 已经给出结构化正文。",
                        }
                    ]
                },
            }
            yield {"type": "done", "session_id": "sess-analysis-native-structured"}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "检查一下这个需求，分析一下并生成RFX策略。",
                "session_id": "sess-analysis-native-structured",
                "context": {
                    "project_id": "proj-analysis-native-structured",
                    "mode": "requirement_canvas",
                },
            },
        )

    assert response.status_code == 200
    assert response.text.count("event: analysis_payload") == 1
    assert "FLARE 已经给出结构化正文。" in response.text


def test_stream_response_normalizes_html_break_tags(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _auth_headers(client)

    bind_response = client.post(
        "/projects/bind",
        headers=headers,
        json={"project_id": "proj-stream-break-normalization"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {
                "type": "text.delta",
                "channel": "assistant",
                "delta": "| 模块 | 核心内容 |\n| --- | --- |\n| 项目概况 | 名称：办公桌采购<br>目的：支持入驻 |",
            }
            yield {"type": "done", "session_id": "sess-stream-break-normalization"}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "理解一下附件内容",
                "session_id": "sess-stream-break-normalization",
                "context": {
                    "project_id": "proj-stream-break-normalization",
                    "mode": "requirement_canvas",
                },
            },
        )

    assert response.status_code == 200
    assert "<br>" not in response.text
    assert "名称：办公桌采购；目的：支持入驻" in response.text


def test_sourcing_request_does_not_synthesize_candidate_payload(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _auth_headers(client)

    bind_response = client.post(
        "/projects/bind",
        headers=headers,
        json={"project_id": "proj-sourcing-candidates"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {
                "type": "text.delta",
                "channel": "assistant",
                "delta": "我先按当前条件生成候选供应商初筛。",
            }
            yield {"type": "done", "session_id": "sess-sourcing-candidates"}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "帮我找办公桌供应商，上海交付，预算45万，120张。",
                "session_id": "sess-sourcing-candidates",
                "context": {
                    "project_id": "proj-sourcing-candidates",
                    "mode": "intelligent_sourcing",
                },
            },
        )

    assert response.status_code == 200
    assert "event: sourcing_candidates" not in response.text
    assert "我先按当前条件生成候选供应商初筛。" in response.text
    assert "内部供应商库候选池" not in response.text
    assert '"render_hint": "sourcing_candidates"' not in response.text


def test_chat_run_uses_generic_empty_message_when_kernel_text_is_unusable(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _auth_headers(client)

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_run:
        mock_run.return_value = {"message": "", "cards": [], "session_id": "sess-run-intake-projection"}

        response = client.post(
            "/chat/run",
            headers=headers,
            json={
                "message": "我要采购一批办公桌椅，用于上海新办公室开放办公区，预算45万元，数量120套，2周内交付。请先帮我梳理需求。",
                "session_id": "sess-run-intake-projection",
                "context": {"mode": "requirement_canvas"},
            },
        )

    assert response.status_code == 200
    assert response.json()["message"] == EMPTY_ASSISTANT_MESSAGE


def test_chat_run_uses_generic_empty_message_when_kernel_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _auth_headers(client)

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_run:
        mock_run.side_effect = TimeoutError("kernel timeout")

        response = client.post(
            "/chat/run",
            headers=headers,
            json={
                "message": "我要采购一批办公桌椅，用于上海新办公室开放办公区，预算45万元，数量120套，2周内交付。请先帮我梳理需求。",
                "session_id": "sess-run-intake-raises",
                "context": {"mode": "requirement_canvas"},
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["degraded"] is True
    assert payload["metadata"]["degrade_reason"] == "kernel_exception"
    assert payload["message"] == EMPTY_ASSISTANT_MESSAGE


def test_chat_run_does_not_project_sourcing_when_kernel_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _auth_headers(client)

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run") as mock_run:
        mock_run.side_effect = TimeoutError("kernel timeout")

        response = client.post(
            "/chat/run",
            headers=headers,
            json={
                "message": "基于办公桌椅、上海交付、预算45万、120套，进入智能寻源，输出供应商筛选口径和候选清单结构。",
                "session_id": "sess-run-sourcing-raises",
                "context": {"mode": "requirement_canvas"},
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["degraded"] is True
    assert payload["metadata"]["degrade_reason"] == "kernel_exception"
    assert payload["message"] == EMPTY_ASSISTANT_MESSAGE
    assert "需求分析与 RFX 策略报告" not in payload["message"]
    assert "智能寻源候选初筛" not in payload["message"]


def test_stream_suppresses_unsupported_interaction_fallback(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _auth_headers(client)

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {
                "type": "text.delta",
                "channel": "assistant",
                "delta": "这个交互方式目前还没有开发到，暂时不能直接完成。",
            }
            yield {
                "type": "text.delta",
                "channel": "assistant",
                "delta": "我这边没有拿到完整的可展示结果，先不直接给结论。",
            }
            yield {"type": "done", "session_id": "sess-unsupported-fallback"}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "请基于预算45万、120套办公桌椅、上海交付，生成RFX策略报告。",
                "session_id": "sess-unsupported-fallback",
                "context": {"mode": "requirement_canvas"},
            },
        )

    assert response.status_code == 200
    assert "这个交互方式目前还没有开发到" not in response.text
    assert "暂时不能直接完成" not in response.text
    assert "我这边没有拿到完整的可展示结果" not in response.text
    assert "event: analysis_payload" not in response.text
    assert "需求分析与 RFX 策略报告" not in response.text
    assert EMPTY_ASSISTANT_MESSAGE in response.text
