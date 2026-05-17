import pytest
from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.chat.kernel_client import KernelClient, get_kernel_client
from xiaocai_instance_api.chat.replay.store import ReplayStore
from xiaocai_instance_api.settings import get_settings


class _FakeRunResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"message": "replay ok", "cards": [], "session_id": "sess-replay"}


class _FakeAsyncClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url, *, json, timeout):
        self.url = url
        self.body = json
        self.timeout = timeout
        return _FakeRunResponse()


class _FakeStreamResponse:
    def raise_for_status(self):
        return None

    async def aiter_lines(self):
        yield "event: content"
        yield 'data: {"type":"content","content":"stream ok"}'
        yield ""
        yield "event: done"
        yield 'data: {"type":"done","message":"stream ok"}'
        yield ""


class _FakeStreamContext:
    async def __aenter__(self):
        return _FakeStreamResponse()

    async def __aexit__(self, exc_type, exc, tb):
        return None


class _FakeStreamAsyncClient(_FakeAsyncClient):
    def stream(self, method, url, *, json, timeout):
        self.method = method
        self.url = url
        self.body = json
        self.timeout = timeout
        return _FakeStreamContext()


@pytest.mark.asyncio
async def test_kernel_run_writes_replay_capture(monkeypatch, tmp_path):
    monkeypatch.setenv("CHAT_REPLAY_ENABLED", "true")
    monkeypatch.setenv("CHAT_REPLAY_DIR", str(tmp_path / "replays"))
    get_settings.cache_clear()
    get_kernel_client.cache_clear()
    monkeypatch.setattr("xiaocai_instance_api.chat.kernel_client.httpx.AsyncClient", _FakeAsyncClient)

    result = await KernelClient().chat_run(
        user_id="user-replay",
        message="我要找衍射仪",
        session_id="sess-replay",
        context={"mode": "requirement_canvas"},
    )

    assert result["message"] == "replay ok"
    summaries = ReplayStore(str(tmp_path / "replays")).list_summaries(user_id="user-replay")
    assert len(summaries) == 1
    export = ReplayStore(str(tmp_path / "replays")).read_export(
        capture_id=summaries[0].capture_id,
        user_id="user-replay",
    )
    assert export.manifest.request_body["message"] == "我要找衍射仪"
    assert "kernel.request" in export.events_jsonl
    assert "kernel.response.raw" in export.events_jsonl
    assert "node replay.mjs" in export.replay_mjs
    assert "我要找衍射仪" in export.replay_mjs


@pytest.mark.asyncio
async def test_kernel_run_ignores_replay_store_failure(monkeypatch):
    class BrokenReplayStore:
        def __init__(self, root_dir):
            self.root_dir = root_dir

        def start_capture(self, **kwargs):
            raise OSError("debug disk unavailable")

    monkeypatch.setenv("CHAT_REPLAY_ENABLED", "true")
    get_settings.cache_clear()
    get_kernel_client.cache_clear()
    monkeypatch.setattr("xiaocai_instance_api.chat.kernel_client.httpx.AsyncClient", _FakeAsyncClient)
    monkeypatch.setattr("xiaocai_instance_api.chat.replay.hooks.ReplayStore", BrokenReplayStore)

    result = await KernelClient().chat_run(
        user_id="user-replay-failure",
        message="主链路不能受 replay 影响",
        session_id="sess-replay-failure",
        context={"mode": "requirement_canvas"},
    )

    assert result["message"] == "replay ok"


@pytest.mark.asyncio
async def test_kernel_stream_writes_replay_events(monkeypatch, tmp_path):
    monkeypatch.setenv("CHAT_REPLAY_ENABLED", "true")
    monkeypatch.setenv("CHAT_REPLAY_DIR", str(tmp_path / "replays"))
    get_settings.cache_clear()
    get_kernel_client.cache_clear()
    monkeypatch.setattr("xiaocai_instance_api.chat.kernel_client.httpx.AsyncClient", _FakeStreamAsyncClient)

    events = []
    async for event in KernelClient().chat_stream(
        user_id="user-stream-replay",
        message="stream replay",
        session_id="sess-stream-replay",
        context={"mode": "requirement_canvas"},
    ):
        events.append(event)

    assert [event["type"] for event in events] == ["content", "done"]
    summaries = ReplayStore(str(tmp_path / "replays")).list_summaries(user_id="user-stream-replay")
    export = ReplayStore(str(tmp_path / "replays")).read_export(
        capture_id=summaries[0].capture_id,
        user_id="user-stream-replay",
    )
    assert export.manifest.kind == "stream"
    assert "kernel.stream.event" in export.events_jsonl
    assert "stream replay" in export.replay_mjs


def test_replay_router_exports_latest_for_current_user(monkeypatch, tmp_path):
    replay_dir = tmp_path / "replays"
    monkeypatch.setenv("CHAT_REPLAY_ENABLED", "true")
    monkeypatch.setenv("CHAT_REPLAY_DIR", str(replay_dir))
    get_settings.cache_clear()

    store = ReplayStore(str(replay_dir))
    manifest = store.start_capture(
        kind="run",
        user_id="router-user",
        session_id="sess-router",
        kernel_url="http://kernel.local/kernel/run",
        request_body={"message": "复现", "session_id": "sess-router"},
    )
    store.append_event(manifest.capture_id, "kernel.response.raw", {"message": "ok"})
    store.finish_capture(manifest.capture_id, status="ok")

    client = TestClient(create_app())
    token_response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": "router-user"})
    token = token_response.json()["access_token"]

    response = client.get(
        "/debug/replay/latest?session_id=sess-router",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["manifest"]["capture_id"] == manifest.capture_id
    assert "kernel.response.raw" in data["events_jsonl"]
    assert "http://kernel.local/kernel/run" in data["replay_mjs"]

    mjs_response = client.get(
        f"/debug/replay/{manifest.capture_id}/mjs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert mjs_response.status_code == 200
    assert "node replay.mjs" in mjs_response.text


def test_replay_router_is_not_registered_by_default(monkeypatch):
    monkeypatch.delenv("CHAT_REPLAY_ENABLED", raising=False)
    get_settings.cache_clear()
    client = TestClient(create_app())
    token_response = client.post("/auth/exchange", json={"mock": True, "mock_user_id": "router-user"})
    token = token_response.json()["access_token"]

    response = client.get(
        "/debug/replay/list",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_replay_export_denies_other_users(tmp_path):
    store = ReplayStore(str(tmp_path / "replays"))
    manifest = store.start_capture(
        kind="run",
        user_id="owner-user",
        session_id="sess-private",
        kernel_url="http://kernel.local/kernel/run",
        request_body={"message": "private"},
    )

    with pytest.raises(PermissionError):
        store.read_export(capture_id=manifest.capture_id, user_id="other-user")
