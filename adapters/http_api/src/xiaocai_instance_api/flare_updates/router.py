from __future__ import annotations

from fastapi import APIRouter

from xiaocai_instance_api.flare_updates.contracts import FlareUpdateStatusResponse
from xiaocai_instance_api.flare_updates.service import get_flare_update_status


router = APIRouter(prefix="/flare-updates", tags=["flare-updates"])


@router.get("/status", response_model=FlareUpdateStatusResponse)
async def read_flare_update_status() -> FlareUpdateStatusResponse:
    return get_flare_update_status()
