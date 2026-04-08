import pytest
import httpx

from xiaocai_instance_api.chat.kernel_client import KernelClient
from xiaocai_instance_api.settings import Settings
import xiaocai_instance_api.chat.kernel_client as kernel_client_module


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, lines=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self._lines = lines or []
        self.request = httpx.Request("POST", "http://kernel.local")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "HTTP error",
                request=self.request,
                response=self,
            )

    def json(self):
        return self._json_data

    async def aiter_lines(self):
        for line in self._lines:
            yield line


class FakeStreamContext:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeAsyncClient:
    def __init__(self, post_response=None, stream_response=None):
        self.post_response = post_response or FakeResponse()
        self.stream_response = stream_response or FakeResponse()
        self.post_calls = []
        self.stream_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, timeout=None):
        self.post_calls.append({"url": url, "json": json, "timeout": timeout})
        return self.post_response

    def stream(self, method, url, json=None, timeout=None):
        self.stream_calls.append(
            {"method": method, "url": url, "json": json, "timeout": timeout}
        )
        return FakeStreamContext(self.stream_response)


@pytest.mark.asyncio
async def test_kernel_client_run_uses_settings_path_and_reply(monkeypatch):
    settings = Settings(
        instance_jwt_secret="secret",
        kernel_host="kernel.local",
        kernel_port=8080,
        kernel_run_path="/custom/run",
        kernel_stream_path="/custom/stream",
        flare_domain_pack_root=".",
    )
    monkeypatch.setattr(kernel_client_module, "get_settings", lambda: settings)

    fake_client = FakeAsyncClient(
        post_response=FakeResponse(
            json_data={
                "reply": "hello",
                "cards": [{"type": "card"}],
                "session_id": "kernel-session",
            }
        )
    )
    monkeypatch.setattr(kernel_client_module.httpx, "AsyncClient", lambda: fake_client)

    client = KernelClient()
    result = await client.chat_run(
        user_id="user-1",
        message="hello",
        session_id="session-1",
        context={"project_id": "proj-1"},
    )

    assert fake_client.post_calls[0]["url"] == "http://kernel.local:8080/custom/run"
    assert fake_client.post_calls[0]["json"]["user_id"] == "user-1"
    assert fake_client.post_calls[0]["json"]["context"] == {"project_id": "proj-1"}
    assert result["message"] == "hello"
    assert result["cards"] == [{"type": "card"}]
    assert result["session_id"] == "kernel-session"


@pytest.mark.asyncio
async def test_kernel_client_stream_parses_sse_events(monkeypatch):
    settings = Settings(
        instance_jwt_secret="secret",
        kernel_host="kernel.local",
        kernel_port=8080,
        kernel_run_path="/custom/run",
        kernel_stream_path="/custom/stream",
        flare_domain_pack_root=".",
    )
    monkeypatch.setattr(kernel_client_module, "get_settings", lambda: settings)

    fake_client = FakeAsyncClient(
        stream_response=FakeResponse(
            lines=[
                "event: token",
                'data: {"content": "你"}',
                "",
                "event: token",
                'data: {"content": "好"}',
                "",
                'data: {"type": "done"}',
                "",
            ]
        )
    )
    monkeypatch.setattr(kernel_client_module.httpx, "AsyncClient", lambda: fake_client)

    client = KernelClient()
    events = [
        event
        async for event in client.chat_stream(
            user_id="user-1",
            message="你好",
            session_id="session-1",
            context={},
        )
    ]

    assert fake_client.stream_calls[0]["url"] == "http://kernel.local:8080/custom/stream"
    assert events[0]["type"] == "token"
    assert events[0]["content"] == "你"
    assert events[1]["type"] == "token"
    assert events[1]["payload"] == {"content": "好"}
    assert events[2]["type"] == "done"


@pytest.mark.asyncio
async def test_kernel_client_run_http_error(monkeypatch):
    settings = Settings(
        instance_jwt_secret="secret",
        kernel_host="kernel.local",
        kernel_port=8080,
        kernel_run_path="/custom/run",
        kernel_stream_path="/custom/stream",
        flare_domain_pack_root=".",
    )
    monkeypatch.setattr(kernel_client_module, "get_settings", lambda: settings)

    fake_client = FakeAsyncClient(
        post_response=FakeResponse(status_code=500, json_data={"detail": "boom"})
    )
    monkeypatch.setattr(kernel_client_module.httpx, "AsyncClient", lambda: fake_client)

    client = KernelClient()

    with pytest.raises(httpx.HTTPStatusError):
        await client.chat_run(
            user_id="user-1",
            message="hello",
            session_id="session-1",
            context={},
        )
