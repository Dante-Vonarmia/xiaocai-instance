from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .contracts import ReplayEvent, ReplayExport, ReplayKind, ReplayManifest, ReplaySummary
from .mjs import build_replay_mjs

_SAFE_ID_PATTERN = re.compile(r"[^a-zA-Z0-9_.:-]+")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_part(value: str) -> str:
    normalized = _SAFE_ID_PATTERN.sub("-", value.strip())
    return normalized[:80] or "unknown"


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=False)
        return value
    except TypeError:
        if isinstance(value, dict):
            return {str(key): _json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [_json_safe(item) for item in value]
        return repr(value)


class ReplayStore:
    """File-backed replay persistence; owns only debug artifact storage."""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)

    def start_capture(
        self,
        *,
        kind: ReplayKind,
        user_id: str,
        session_id: str,
        kernel_url: str,
        request_body: dict[str, Any],
    ) -> ReplayManifest:
        capture_id = self._new_capture_id(session_id=session_id)
        manifest = ReplayManifest(
            capture_id=capture_id,
            kind=kind,
            created_at=utc_now_iso(),
            user_id=user_id,
            session_id=session_id,
            kernel_url=kernel_url,
            request_body=_json_safe(request_body),
        )
        directory = self._capture_dir(capture_id)
        directory.mkdir(parents=True, exist_ok=False)
        self._write_manifest(manifest)
        self._write_mjs(manifest)
        return manifest

    def append_event(self, capture_id: str, event_type: str, payload: Any) -> None:
        manifest = self.read_manifest(capture_id)
        event = ReplayEvent(ts=utc_now_iso(), event_type=event_type, payload=_json_safe(payload))
        events_path = self._events_path(capture_id)
        with events_path.open("a", encoding="utf-8") as handle:
            handle.write(event.model_dump_json(exclude_none=True) + "\n")
        manifest.event_count += 1
        self._write_manifest(manifest)

    def finish_capture(self, capture_id: str, *, status: str, error: str | None = None) -> None:
        manifest = self.read_manifest(capture_id)
        manifest.status = "error" if status == "error" else "ok"
        manifest.finished_at = utc_now_iso()
        manifest.error = error
        self._write_manifest(manifest)
        self._write_mjs(manifest)

    def list_summaries(self, *, user_id: str, session_id: str | None = None) -> list[ReplaySummary]:
        summaries: list[ReplaySummary] = []
        if not self.root_dir.exists():
            return summaries
        for manifest_path in self.root_dir.glob("*/manifest.json"):
            try:
                manifest = self._load_manifest_path(manifest_path)
            except (OSError, ValueError):
                continue
            if manifest.user_id != user_id:
                continue
            if session_id and manifest.session_id != session_id:
                continue
            summaries.append(ReplaySummary(**manifest.model_dump(exclude={"request_body", "kernel_url"})))
        return sorted(summaries, key=lambda item: item.created_at, reverse=True)

    def read_export(self, *, capture_id: str, user_id: str) -> ReplayExport:
        manifest = self.read_manifest(capture_id)
        if manifest.user_id != user_id:
            raise PermissionError(f"Replay capture access denied: {capture_id}")
        events_path = self._events_path(capture_id)
        replay_path = self._mjs_path(capture_id)
        events_jsonl = events_path.read_text(encoding="utf-8") if events_path.exists() else ""
        replay_mjs = replay_path.read_text(encoding="utf-8") if replay_path.exists() else build_replay_mjs(manifest)
        return ReplayExport(manifest=manifest, events_jsonl=events_jsonl, replay_mjs=replay_mjs)

    def read_manifest(self, capture_id: str) -> ReplayManifest:
        return self._load_manifest_path(self._manifest_path(capture_id))

    def _new_capture_id(self, *, session_id: str) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        return f"{timestamp}-{_safe_part(session_id)}-{uuid4().hex[:8]}"

    def _capture_dir(self, capture_id: str) -> Path:
        return self.root_dir / _safe_part(capture_id)

    def _manifest_path(self, capture_id: str) -> Path:
        return self._capture_dir(capture_id) / "manifest.json"

    def _events_path(self, capture_id: str) -> Path:
        return self._capture_dir(capture_id) / "events.jsonl"

    def _mjs_path(self, capture_id: str) -> Path:
        return self._capture_dir(capture_id) / "replay.mjs"

    def _write_manifest(self, manifest: ReplayManifest) -> None:
        path = self._manifest_path(manifest.capture_id)
        path.write_text(manifest.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")

    def _write_mjs(self, manifest: ReplayManifest) -> None:
        path = self._mjs_path(manifest.capture_id)
        path.write_text(build_replay_mjs(manifest), encoding="utf-8")

    def _load_manifest_path(self, path: Path) -> ReplayManifest:
        return ReplayManifest.model_validate_json(path.read_text(encoding="utf-8"))
