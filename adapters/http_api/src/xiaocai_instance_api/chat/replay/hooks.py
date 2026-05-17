from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from xiaocai_instance_api.settings import get_settings

from .contracts import ReplayKind
from .store import ReplayStore


@dataclass(frozen=True)
class ReplayHandle:
    capture_id: str
    enabled: bool


def _store() -> ReplayStore:
    settings = get_settings()
    return ReplayStore(settings.chat_replay_dir)


def begin_kernel_capture(
    *,
    kind: ReplayKind,
    user_id: str,
    session_id: str,
    kernel_url: str,
    request_body: dict[str, Any],
) -> ReplayHandle:
    settings = get_settings()
    if not settings.chat_replay_enabled:
        return ReplayHandle(capture_id="", enabled=False)
    try:
        store = _store()
        manifest = store.start_capture(
            kind=kind,
            user_id=user_id,
            session_id=session_id,
            kernel_url=kernel_url,
            request_body=request_body,
        )
        store.append_event(manifest.capture_id, "kernel.request", request_body)
        return ReplayHandle(capture_id=manifest.capture_id, enabled=True)
    except Exception:
        return ReplayHandle(capture_id="", enabled=False)


def append_kernel_capture(handle: ReplayHandle, event_type: str, payload: Any) -> None:
    if not handle.enabled:
        return
    try:
        _store().append_event(handle.capture_id, event_type, payload)
    except Exception:
        return


def finish_kernel_capture(handle: ReplayHandle, *, status: str, error: str | None = None) -> None:
    if not handle.enabled:
        return
    try:
        _store().finish_capture(handle.capture_id, status=status, error=error)
    except Exception:
        return
