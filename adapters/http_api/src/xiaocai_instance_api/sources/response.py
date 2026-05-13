"""资料响应投影 - Source client contract."""

from __future__ import annotations

from xiaocai_instance_api.storage.source_store import SourceRecord


_READY_STORAGE_STATUSES = {"available", "referenced", "ready"}


def source_status_for_client(status: str | None) -> str:
    """Keep storage status internal while matching the FLARE upload contract."""
    normalized = str(status or "").strip().lower()
    if normalized in _READY_STORAGE_STATUSES:
        return "ready"
    return normalized or "ready"


def serialize_source_record(record: SourceRecord) -> dict[str, object]:
    """Project a stored source record into the API shape expected by clients."""
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
        "status": source_status_for_client(record.status),
        "created_at": record.created_at,
    }
