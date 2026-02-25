"""Output 2 — Structured JSON Exporter."""

import json
from datetime import datetime, timezone
from typing import Any

import structlog

from backend.config import settings
from backend.storage.s3_client import upload_json

logger = structlog.get_logger(__name__)


async def export_analysis_json(
    job_id: str,
    synthesis_result: dict[str, Any],
    validation_summaries: list[dict[str, Any]] | None = None,
    file_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build and store the structured analysis JSON.

    Format per spec:
    {
      "job_id": "...",
      "analysis_date": "ISO8601",
      "functional_unit": "...",
      "system_boundary": "...",
      "impact_method": "...",
      "impact_results": [...],
      "hotspots": [...],
      "data_quality": "...",
      "completeness": 0.82,
      "files_processed": 5,
      "validation_summary": {...}
    }
    """
    file_records = file_records or []
    validation_summaries = validation_summaries or []
    structured = synthesis_result.get("structured_insights", {})

    # Build validation summary counts
    passed = sum(1 for v in validation_summaries if v.get("status") == "passed")
    warnings = sum(1 for v in validation_summaries if v.get("status") == "passed_with_warnings")
    failed = sum(1 for v in validation_summaries if v.get("status") == "failed")
    quarantined = sum(1 for v in validation_summaries if v.get("status") == "quarantined")

    analysis_json = {
        "job_id": job_id,
        "analysis_date": datetime.now(timezone.utc).isoformat(),
        "functional_unit": structured.get("functional_unit"),
        "system_boundary": structured.get("system_boundary"),
        "impact_method": structured.get("impact_method"),
        "impact_results": structured.get("impact_results", []),
        "hotspots": structured.get("hotspots", []),
        "data_quality": structured.get("data_quality", "Unknown"),
        "completeness": structured.get("completeness", 0.0),
        "files_processed": len(file_records),
        "validation_summary": {
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "quarantined": quarantined,
        },
        "recommendations": structured.get("recommendations", []),
    }

    # Store to S3
    s3_key = f"reports/{job_id}/analysis.json"
    try:
        upload_json(settings.S3_BUCKET_REPORTS if settings else "lca-reports", s3_key, analysis_json)
        logger.info("analysis_json_uploaded", job_id=job_id, s3_key=s3_key)
    except Exception as e:
        logger.error("analysis_json_upload_failed", job_id=job_id, error=str(e))

    return analysis_json
