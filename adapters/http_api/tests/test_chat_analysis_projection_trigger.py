from unittest.mock import patch

from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.settings import get_settings


def _auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/exchange",
        json={"mock": True, "mock_user_id": "analysis-trigger-user"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_report_projection_triggers_from_assistant_output_even_when_user_asks_to_understand_attachment(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "storage.sqlite3"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    headers = _auth_headers(client)

    bind_response = client.post(
        "/projects/bind",
        headers=headers,
        json={"project_id": "proj-analysis-output-trigger"},
    )
    assert bind_response.status_code == 200

    with patch("xiaocai_instance_api.chat.kernel_client.KernelClient.chat_stream") as mock_stream:
        async def mock_generator():
            yield {
                "type": "text.delta",
                "channel": "assistant",
                "delta": "基于现有资料，为您生成结构化RFX报告草案如下：\n"
                "一、项目概况\n"
                "- 项目名称：2026年新公司办公空间桌椅配置采购项目\n"
                "- RFX类型：RFQ（询价）\n"
                "二、采购范围与技术要求\n"
                "- 采购数量：180套\n"
                "- 核心要求：模块化快速交付方案。",
            }
            yield {"type": "complete", "session_id": "sess-analysis-output-trigger"}

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/chat/stream",
            headers=headers,
            json={
                "message": "理解一下附件内容",
                "session_id": "sess-analysis-output-trigger",
                "context": {
                    "project_id": "proj-analysis-output-trigger",
                    "mode": "requirement_canvas",
                },
            },
        )

    assert response.status_code == 200
    analysis_index = response.text.find("event: analysis_payload")
    complete_index = response.text.find("event: complete")
    assert analysis_index != -1
    assert complete_index != -1
    assert analysis_index < complete_index
    assert "需求分析与 RFX 策略报告" in response.text
    assert "2026年新公司办公空间桌椅配置采购项目" in response.text
    assert "模块化快速交付方案" in response.text
    assert "分析结论" in response.text
    assert "供应商画像" in response.text
    assert "目标优先级建议" in response.text
    assert '"document"' in response.text
    assert '"content"' in response.text
