"""
资料路由 - Project Source 文件管理
"""

from __future__ import annotations

from pathlib import Path
import os
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from xiaocai_instance_api.security.dependencies import get_current_user_id
from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.ownership_store import get_ownership_store
from xiaocai_instance_api.storage.source_store import get_source_store


router = APIRouter(prefix="/sources", tags=["sources"])


async def _ensure_project_access(user_id: str, project_id: str) -> None:
    ownership_store = get_ownership_store()
    has_access = await ownership_store.check_project_access(user_id=user_id, project_id=project_id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Project access denied: {project_id}",
        )


@router.get("")
async def list_project_sources(
    project_id: str,
    q: str | None = None,
    folder_name: str | None = None,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    await _ensure_project_access(user_id=user_id, project_id=project_id)
    settings = get_settings()
    store = get_source_store(upload_root=settings.upload_root)
    sources = await store.list_project_sources(
        user_id=user_id,
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
                "session_id": item.session_id,
                "folder_name": item.folder_name,
                "file_name": item.file_name,
                "file_size": item.file_size,
                "mime_type": item.mime_type,
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in sources
        ],
    }


@router.get("/folders")
async def list_project_source_folders(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    await _ensure_project_access(user_id=user_id, project_id=project_id)
    settings = get_settings()
    store = get_source_store(upload_root=settings.upload_root)
    folders = await store.list_project_folders(user_id=user_id, project_id=project_id)
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
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    await _ensure_project_access(user_id=user_id, project_id=project_id)
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
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            folder_name=folder_name.strip() or "默认文件夹",
            file_name=file.filename,
            file_size=len(content),
            mime_type=file.content_type or "application/octet-stream",
            source_file_path=tmp_path,
        )
    finally:
        if tmp_path.exists():
            os.unlink(tmp_path)

    return {
        "source_id": record.source_id,
        "project_id": record.project_id,
        "user_id": record.user_id,
        "session_id": record.session_id,
        "folder_name": record.folder_name,
        "file_name": record.file_name,
        "file_size": record.file_size,
        "mime_type": record.mime_type,
        "status": record.status,
        "created_at": record.created_at,
    }


@router.delete("/{source_id}")
async def delete_project_source(
    source_id: str,
    project_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    await _ensure_project_access(user_id=user_id, project_id=project_id)
    settings = get_settings()
    store = get_source_store(upload_root=settings.upload_root)
    deleted = await store.delete_project_source(
        user_id=user_id,
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
    user_id: str = Depends(get_current_user_id),
) -> dict:
    await _ensure_project_access(user_id=user_id, project_id=project_id)
    settings = get_settings()
    store = get_source_store(upload_root=settings.upload_root)
    marked = await store.mark_source_referenced(
        user_id=user_id,
        project_id=project_id,
        source_id=source_id,
    )
    if not marked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return {"marked": True, "source_id": source_id, "status": "referenced"}
