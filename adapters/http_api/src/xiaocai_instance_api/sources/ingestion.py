"""Bridge uploaded xiaocai sources into FLARE knowledge ingestion.

This adapter keeps source upload owned by xiaocai while using FLARE's
ingestion boundary for searchable knowledge records.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from xiaocai_instance_api.storage.source_store import SourceRecord


ExtractTextFn = Callable[..., str]
IngestRecordFn = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class SourceIngestionOutcome:
    source_id: str
    status: str
    chunk_count: int = 0
    error_code: str = ""
    error_message: str = ""


def _load_flare_extract_text() -> ExtractTextFn:
    from flare_kernel.runtime.infrastructure.source.text_extractor import extract_source_text

    return extract_source_text


def _load_flare_ingest_record() -> IngestRecordFn:
    from flare_kernel.runtime.infrastructure.knowledge_ingest import ingest_knowledge_record

    return ingest_knowledge_record


def ingest_source_for_kernel(
    record: SourceRecord,
    *,
    extract_text_fn: ExtractTextFn | None = None,
    ingest_record_fn: IngestRecordFn | None = None,
) -> SourceIngestionOutcome:
    """Ingest one saved xiaocai source into FLARE searchable knowledge."""
    try:
        extract_text = extract_text_fn or _load_flare_extract_text()
        ingest_record = ingest_record_fn or _load_flare_ingest_record()
        content = extract_text(
            Path(record.storage_path),
            mime_type=record.mime_type,
            filename=record.file_name,
        )
        result = ingest_record(
            trace_id=f"xiaocai-source-upload-{record.source_id}",
            project_id=record.project_id,
            user_id=record.user_id,
            session_id=record.session_id or "",
            content=content,
            source_id=record.source_id,
            title=record.file_name,
            metadata={
                "source_type": record.source_type,
                "folder_name": record.folder_name,
                "context_priority": record.context_priority,
            },
        )
    except Exception as exc:
        return SourceIngestionOutcome(
            source_id=record.source_id,
            status="failed",
            error_code=exc.__class__.__name__,
            error_message=str(exc),
        )

    return SourceIngestionOutcome(
        source_id=record.source_id,
        status=str(result.get("status") or "failed"),
        chunk_count=int(result.get("chunk_count") or 0),
        error_code=str(result.get("error_code") or ""),
        error_message=str(result.get("error_message") or ""),
    )
