"""
FLARE chat-core session list event compatibility route.

The current xiaocai API does not yet publish live list invalidation events.
Return a valid short SSE stream so the core can fall back to polling cleanly.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.dependencies import get_current_auth_claims


router = APIRouter(prefix="/chat", tags=["chat-compat"])


@router.get("/list-events")
async def subscribe_chat_list_events(
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> StreamingResponse:
    _ = claims

    async def event_generator():
        yield ": list-events unavailable; polling fallback is expected\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
