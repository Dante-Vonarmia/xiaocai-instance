from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.dependencies import get_current_auth_claims
from xiaocai_instance_api.settings import get_settings

from .contracts import ReplayExport, ReplaySummary
from .store import ReplayStore


router = APIRouter(prefix="/debug/replay", tags=["debug-replay"])


def _store() -> ReplayStore:
    return ReplayStore(get_settings().chat_replay_dir)


def _read_export_or_raise(capture_id: str, user_id: str) -> ReplayExport:
    try:
        return _store().read_export(capture_id=capture_id, user_id=user_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Replay capture not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/list", response_model=list[ReplaySummary])
async def list_replays(
    session_id: str | None = Query(default=None),
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> list[ReplaySummary]:
    return _store().list_summaries(user_id=claims.user_id, session_id=session_id)


@router.get("/latest", response_model=ReplayExport)
async def latest_replay(
    session_id: str | None = Query(default=None),
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> ReplayExport:
    summaries = _store().list_summaries(user_id=claims.user_id, session_id=session_id)
    if not summaries:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No replay capture found")
    return _store().read_export(capture_id=summaries[0].capture_id, user_id=claims.user_id)


@router.get("/{capture_id}", response_model=ReplayExport)
async def get_replay(
    capture_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> ReplayExport:
    return _read_export_or_raise(capture_id=capture_id, user_id=claims.user_id)


@router.get("/{capture_id}/events", response_class=PlainTextResponse)
async def get_replay_events(
    capture_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> PlainTextResponse:
    export = _read_export_or_raise(capture_id=capture_id, user_id=claims.user_id)
    return PlainTextResponse(export.events_jsonl, media_type="application/x-ndjson")


@router.get("/{capture_id}/mjs", response_class=PlainTextResponse)
async def get_replay_mjs(
    capture_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> PlainTextResponse:
    export = _read_export_or_raise(capture_id=capture_id, user_id=claims.user_id)
    return PlainTextResponse(export.replay_mjs, media_type="text/javascript")
