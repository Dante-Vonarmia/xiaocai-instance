"""
Project 归属路由

提供的接口:
- POST /projects/bind - 绑定当前用户与 project 的归属
- GET /projects/mine - 查询当前用户可访问的 project 列表
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.security.dependencies import get_current_user_id
from xiaocai_instance_api.storage.conversation_store import get_conversation_store
from xiaocai_instance_api.storage.ownership_store import get_ownership_store


router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectBindRequest(BaseModel):
    project_id: str = Field(..., description="Project ID")


class ProjectBindResponse(BaseModel):
    success: bool = Field(default=True)
    user_id: str
    project_id: str


class ProjectListResponse(BaseModel):
    project_ids: list[str] = Field(default_factory=list)


class UsageSummaryResponse(BaseModel):
    user_id: str
    project_id: str | None = None
    day_start_utc: str
    daily_message_limit: int
    daily_message_used: int
    daily_message_remaining: int | None = None
    daily_project_message_limit: int
    daily_project_message_used: int | None = None
    daily_project_message_remaining: int | None = None


@router.post("/bind", response_model=ProjectBindResponse)
async def bind_project(
    request: ProjectBindRequest,
    user_id: str = Depends(get_current_user_id),
) -> ProjectBindResponse:
    store = get_ownership_store()
    await store.add_project_ownership(user_id=user_id, project_id=request.project_id)
    return ProjectBindResponse(user_id=user_id, project_id=request.project_id)


@router.get("/mine", response_model=ProjectListResponse)
async def list_my_projects(
    user_id: str = Depends(get_current_user_id),
) -> ProjectListResponse:
    store = get_ownership_store()
    project_ids = await store.list_user_projects(user_id=user_id)
    return ProjectListResponse(project_ids=project_ids)


@router.get("/usage", response_model=UsageSummaryResponse)
async def get_usage_summary(
    project_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
) -> UsageSummaryResponse:
    settings = get_settings()
    store = get_conversation_store()
    day_start_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    daily_message_used = await store.count_user_messages_since(user_id=user_id, since_iso=day_start_utc)
    daily_message_limit = settings.daily_message_limit
    daily_message_remaining: int | None = None
    if daily_message_limit > 0:
        daily_message_remaining = max(daily_message_limit - daily_message_used, 0)

    daily_project_message_limit = settings.daily_project_message_limit
    daily_project_message_used: int | None = None
    daily_project_message_remaining: int | None = None
    if project_id and daily_project_message_limit > 0:
        daily_project_message_used = await store.count_user_project_messages_since(
            user_id=user_id,
            project_id=project_id,
            since_iso=day_start_utc,
        )
        daily_project_message_remaining = max(daily_project_message_limit - daily_project_message_used, 0)

    return UsageSummaryResponse(
        user_id=user_id,
        project_id=project_id,
        day_start_utc=day_start_utc,
        daily_message_limit=daily_message_limit,
        daily_message_used=daily_message_used,
        daily_message_remaining=daily_message_remaining,
        daily_project_message_limit=daily_project_message_limit,
        daily_project_message_used=daily_project_message_used,
        daily_project_message_remaining=daily_project_message_remaining,
    )
