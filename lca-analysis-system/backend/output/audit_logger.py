"""Output 4 — Audit Trail Logger."""

import json
from datetime import datetime, timezone
from typing import Any

import structlog

from backend.storage.s3_client import upload_json

logger = structlog.get_logger(__name__)


async def build_audit_trail(
    job_id: str,
    start_time: datetime,
    file_records: list[dict[str, Any]],
    validation_summaries: list[dict[str, Any]] | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build and store the full audit trail JSON.

    Format per spec:
    {
      "job_id": "...",
      "start_time": "ISO8601",
      "end_time": "ISO8601",
      "total_duration_seconds": 142,
      "files": [...],
      "models_used": [...],
      "total_tokens": 0,
      "validation_summary": {...},
      "errors": [...]
    }
    """
    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()
    validation_summaries = validation_summaries or []
    errors = errors or []

    # Build file audit entries
    file_audits = []
    for fr in file_records:
        file_audits.append({
            "file_id": fr.get("file_id", "unknown"),
            "original_name": fr.get("original_name", "unknown"),
            "agent_assigned": fr.get("agent", "unknown"),
            "routing_reason": fr.get("routing_reason", "Detected file type routing"),
            "processing_time_s": fr.get("processing_time_s", 0),
            "confidence": fr.get("confidence", 0.0),
            "validation_status": fr.get("validation_status", "unknown"),
            "errors": fr.get("errors", []),
        })

    # Validation summary counts
    passed = sum(1 for v in validation_summaries if v.get("status") == "passed")
    warnings = sum(1 for v in validation_summaries if v.get("status") == "passed_with_warnings")
    failed = sum(1 for v in validation_summaries if v.get("status") == "failed")
    quarantined = sum(1 for v in validation_summaries if v.get("status") == "quarantined")

    audit = {
        "job_id": job_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "total_duration_seconds": round(duration, 2),
        "files": file_audits,
        "models_used": ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
        "total_tokens": 0,  # Could be tracked per-call if needed
        "validation_summary": {
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "quarantined": quarantined,
        },
        "errors": errors,
    }

    # Store to S3
    s3_key = f"audit/{job_id}/audit.json"
    try:
        await upload_json(s3_key, audit)
        logger.info("audit_trail_uploaded", job_id=job_id, s3_key=s3_key)
    except Exception as e:
        logger.error("audit_trail_upload_failed", job_id=job_id, error=str(e))

    return audit
