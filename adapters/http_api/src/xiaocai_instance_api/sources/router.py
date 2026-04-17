"""
资料路由 - Project Source 文件管理
"""

from __future__ import annotations

from pathlib import Path
import os
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from xiaocai_instance_api.security.auth_claims import AuthClaims
from xiaocai_instance_api.security.dependencies import get_current_auth_claims
from xiaocai_instance_api.security.authorization import get_authorization_service
from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.source_store import get_source_store


router = APIRouter(prefix="/sources", tags=["sources"])


class SourcePriorityUpdateRequest(BaseModel):
    project_id: str = Field(...)
    context_priority: int = Field(..., ge=0)


@router.get("")
async def list_project_sources(
    project_id: str,
    q: str | None = None,
    folder_name: str | None = None,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_project_access(claims=claims, project_id=project_id)
    settings = get_settings()
    store = get_source_store(upload_root=settings.upload_root)
    sources = await store.list_project_sources(
        user_id=claims.user_id,
        project_id=project_id,
        query=q,
        folder_name=folder_name,
    )
    return {
        "project_id": project_id,
        "query": q or "",
        "folder_name": folder_name or "",
        "sources": [
            {
                "source_id": item.source_id,
                "project_id": item.project_id,
                "user_id": item.user_id,
                "owner_user_id": item.owner_user_id,
                "visibility": item.visibility,
                "session_id": item.session_id,
                "folder_name": item.folder_name,
                "file_name": item.file_name,
                "file_size": item.file_size,
                "mime_type": item.mime_type,
                "source_type": item.source_type,
                "date_bucket": item.date_bucket,
                "time_bucket": item.time_bucket,
                "context_priority": item.context_priority,
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in sources
        ],
    }


@router.get("/folders")
async def list_project_source_folders(
    project_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_project_access(claims=claims, project_id=project_id)
    settings = get_settings()
    store = get_source_store(upload_root=settings.upload_root)
    folders = await store.list_project_folders(user_id=claims.user_id, project_id=project_id)
    return {
        "project_id": project_id,
        "folders": [
            {
                "folder_name": item.folder_name,
                "file_count": item.file_count,
                "referenced_count": item.referenced_count,
            }
            for item in folders
        ],
    }


@router.post("/upload")
async def upload_source_file(
    project_id: str = Form(...),
    session_id: str | None = Form(default=None),
    folder_name: str = Form(default="默认文件夹"),
    source_type: str = Form(default="upload_attachment"),
    context_priority: int = Form(default=100),
    file: UploadFile = File(...),
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_project_access(claims=claims, project_id=project_id)
    settings = get_settings()
    store = get_source_store(upload_root=settings.upload_root)

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file name is required")
    suffix = Path(file.filename).suffix.lower().lstrip(".")
    allowed = {ext.lower().lstrip(".") for ext in settings.upload_allowed_extensions}
    if suffix not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"file extension not allowed: {suffix}",
        )
    if context_priority < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="context_priority must be >= 0",
        )

    original_suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=original_suffix) as tmp:
        tmp_path = Path(tmp.name)
        content = await file.read()
        if len(content) > settings.upload_max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"file too large: {len(content)} bytes",
            )
        tmp.write(content)

    try:
        record = await store.save_source_file(
            user_id=claims.user_id,
            project_id=project_id,
            session_id=session_id,
            folder_name=folder_name.strip() or "默认文件夹",
            file_name=file.filename,
            file_size=len(content),
            mime_type=file.content_type or "application/octet-stream",
            source_file_path=tmp_path,
            source_type=source_type.strip() or "upload_attachment",
            context_priority=context_priority,
        )
    finally:
        if tmp_path.exists():
            os.unlink(tmp_path)

    return {
        "source_id": record.source_id,
        "project_id": record.project_id,
        "user_id": record.user_id,
        "owner_user_id": record.owner_user_id,
        "visibility": record.visibility,
        "session_id": record.session_id,
        "folder_name": record.folder_name,
        "file_name": record.file_name,
        "file_size": record.file_size,
        "mime_type": record.mime_type,
        "source_type": record.source_type,
        "date_bucket": record.date_bucket,
        "time_bucket": record.time_bucket,
        "context_priority": record.context_priority,
        "status": record.status,
        "created_at": record.created_at,
    }


@router.delete("/{source_id}")
async def delete_project_source(
    source_id: str,
    project_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_project_access(claims=claims, project_id=project_id)
    await authz.require_file_write(claims=claims, source_id=source_id)
    settings = get_settings()
    store = get_source_store(upload_root=settings.upload_root)
    record = await store.get_source_for_user(user_id=claims.user_id, source_id=source_id)
    if record is None or record.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    deleted = await store.delete_project_source(
        user_id=claims.user_id,
        project_id=project_id,
        source_id=source_id,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return {"deleted": True}


@router.post("/{source_id}/mark-referenced")
async def mark_project_source_referenced(
    source_id: str,
    project_id: str,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_project_access(claims=claims, project_id=project_id)
    await authz.require_file_write(claims=claims, source_id=source_id)
    settings = get_settings()
    store = get_source_store(upload_root=settings.upload_root)
    record = await store.get_source_for_user(user_id=claims.user_id, source_id=source_id)
    if record is None or record.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    marked = await store.mark_source_referenced(
        user_id=claims.user_id,
        project_id=project_id,
        source_id=source_id,
    )
    if not marked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return {"marked": True, "source_id": source_id, "status": "referenced"}


@router.post("/{source_id}/priority")
async def update_project_source_priority(
    source_id: str,
    request: SourcePriorityUpdateRequest,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> dict:
    authz = get_authorization_service()
    await authz.require_project_access(claims=claims, project_id=request.project_id)
    await authz.require_file_write(claims=claims, source_id=source_id)
    settings = get_settings()
    store = get_source_store(upload_root=settings.upload_root)
    record = await store.get_source_for_user(user_id=claims.user_id, source_id=source_id)
    if record is None or record.project_id != request.project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    updated = await store.update_source_priority(
        user_id=claims.user_id,
        project_id=request.project_id,
        source_id=source_id,
        context_priority=request.context_priority,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    refreshed = await store.get_source_for_user(user_id=claims.user_id, source_id=source_id)
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return {
        "updated": True,
        "source_id": refreshed.source_id,
        "project_id": refreshed.project_id,
        "context_priority": refreshed.context_priority,
    }


@router.get("/{source_id}/download")
async def download_project_source(
    source_id: str,
    project_id: str | None = None,
    claims: AuthClaims = Depends(get_current_auth_claims),
) -> FileResponse:
    authz = get_authorization_service()
    await authz.require_file_access(claims=claims, source_id=source_id)
    settings = get_settings()
    store = get_source_store(upload_root=settings.upload_root)
    record = await store.get_source_for_user(user_id=claims.user_id, source_id=source_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    if project_id and record.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return FileResponse(
        path=record.storage_path,
        filename=record.file_name,
        media_type=record.mime_type,
    )
