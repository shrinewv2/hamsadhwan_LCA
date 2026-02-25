"""LCA Multi-Agent Analysis System — FastAPI Application.

All routes under /api/v1.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.background import BackgroundTasks

from backend.config import get_settings, settings as app_settings
from backend.ingestion.router import router as ingestion_router
from backend.models.schemas import ErrorResponse, HealthResponse
from backend.orchestrator.graph import run_pipeline
from backend.storage.dynamo_client import (
    get_analysis_record,
    get_file_records_for_job,
    update_analysis_record,
    update_file_record,
)
from backend.storage.s3_client import download_text
from backend.utils.logger import get_job_logs, setup_logging

# ─── Setup ───
setup_logging()
logger = structlog.get_logger(__name__)
settings = get_settings()

app = FastAPI(
    title="LCA Multi-Agent Analysis System",
    description="Automated Life Cycle Assessment document analysis using multi-agent AI",
    version="1.0.0",
)

# ─── CORS ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# ─── Mount Ingestion Router ───
app.include_router(ingestion_router, prefix="/api/v1")


# ─── GET /api/v1/jobs/{job_id} — Job Status ───
@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Return full job status for frontend polling."""
    try:
        analysis = await get_analysis_record(job_id)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        file_records = await get_file_records_for_job(job_id)

        # Calculate progress
        total = len(file_records)
        completed = sum(1 for f in file_records if f.get("status") in ("COMPLETED", "QUARANTINED"))
        failed = sum(1 for f in file_records if f.get("status") == "FAILED")
        processing = sum(1 for f in file_records if f.get("status") == "PROCESSING")

        status = analysis.get("status", "PENDING")
        if status == "COMPLETED":
            progress = 100
        elif status == "FAILED":
            progress = -1
        elif total > 0:
            progress = int((completed / total) * 70)  # 70% for agent processing
        else:
            progress = 0

        files_response = []
        for fr in file_records:
            files_response.append({
                "file_id": fr.get("file_id"),
                "name": fr.get("original_name"),
                "type": fr.get("file_type"),
                "agent": fr.get("agent"),
                "status": fr.get("status"),
                "confidence": float(fr.get("confidence", 0)),
            })

        errors = []
        if analysis.get("error"):
            errors.append(analysis["error"])

        return {
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "files": files_response,
            "errors": errors,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_job_status_error", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /api/v1/jobs/{job_id}/report — Full Analysis Result ───
@app.get("/api/v1/jobs/{job_id}/report")
async def get_job_report(job_id: str):
    """Return the full analysis result."""
    try:
        analysis = await get_analysis_record(job_id)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        status = analysis.get("status", "PENDING")
        if status != "COMPLETED":
            return JSONResponse(
                status_code=202,
                content={"status": status, "message": "Analysis still processing"},
            )

        # Fetch all outputs from S3
        report_key = analysis.get("report_s3_key", f"reports/{job_id}/full_report.md")
        json_key = analysis.get("analysis_json_s3_key", f"reports/{job_id}/analysis.json")
        viz_key = analysis.get("viz_data_s3_key", f"reports/{job_id}/viz_data.json")
        audit_key = analysis.get("audit_s3_key", f"audit/{job_id}/audit.json")

        markdown_report = ""
        structured_json = {}
        viz_data = {}
        audit_summary = {}

        reports_bucket = app_settings.S3_BUCKET_REPORTS if app_settings else "lca-reports"
        audit_bucket = app_settings.S3_BUCKET_AUDIT if app_settings else "lca-audit-logs"

        try:
            markdown_report = download_text(reports_bucket, report_key)
        except Exception:
            logger.warning("report_download_failed", key=report_key)

        try:
            json_text = download_text(reports_bucket, json_key)
            structured_json = json.loads(json_text)
        except Exception:
            logger.warning("analysis_json_download_failed", key=json_key)

        try:
            viz_text = download_text(reports_bucket, viz_key)
            viz_data = json.loads(viz_text)
        except Exception:
            logger.warning("viz_data_download_failed", key=viz_key)

        try:
            audit_text = download_text(audit_bucket, audit_key)
            audit_summary = json.loads(audit_text)
        except Exception:
            logger.warning("audit_download_failed", key=audit_key)

        # Validation summary from analysis record or structured json
        validation_summary = structured_json.get("validation_summary", {})

        return {
            "markdown_report": markdown_report,
            "structured_json": structured_json,
            "viz_data": viz_data,
            "validation_summary": validation_summary,
            "audit_summary": audit_summary,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_report_error", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /api/v1/jobs/{job_id}/download/report — Download Markdown Report ───
@app.get("/api/v1/jobs/{job_id}/download/report")
async def download_report(job_id: str):
    """Stream the Markdown report as a file download."""
    try:
        reports_bucket = app_settings.S3_BUCKET_REPORTS if app_settings else "lca-reports"
        report_key = f"reports/{job_id}/full_report.md"
        content = download_text(reports_bucket, report_key)

        return StreamingResponse(
            iter([content.encode("utf-8")]),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="lca_report_{job_id}.md"'
            },
        )
    except Exception as e:
        logger.error("download_report_error", job_id=job_id, error=str(e))
        raise HTTPException(status_code=404, detail="Report not found")


# ─── GET /api/v1/jobs/{job_id}/download/json — Download Structured JSON ───
@app.get("/api/v1/jobs/{job_id}/download/json")
async def download_json(job_id: str):
    """Stream the structured JSON as a file download."""
    try:
        reports_bucket = app_settings.S3_BUCKET_REPORTS if app_settings else "lca-reports"
        json_key = f"reports/{job_id}/analysis.json"
        content = download_text(reports_bucket, json_key)

        return StreamingResponse(
            iter([content.encode("utf-8")]),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="lca_analysis_{job_id}.json"'
            },
        )
    except Exception as e:
        logger.error("download_json_error", job_id=job_id, error=str(e))
        raise HTTPException(status_code=404, detail="Analysis JSON not found")


# ─── GET /api/v1/jobs/{job_id}/download/audit — Download Audit Trail ───
@app.get("/api/v1/jobs/{job_id}/download/audit")
async def download_audit(job_id: str):
    """Stream the audit trail JSON as a file download."""
    try:
        audit_bucket = app_settings.S3_BUCKET_AUDIT if app_settings else "lca-audit-logs"
        audit_key = f"audit/{job_id}/audit.json"
        content = download_text(audit_bucket, audit_key)

        return StreamingResponse(
            iter([content.encode("utf-8")]),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="lca_audit_{job_id}.json"'
            },
        )
    except Exception as e:
        logger.error("download_audit_error", job_id=job_id, error=str(e))
        raise HTTPException(status_code=404, detail="Audit trail not found")


# ─── GET /api/v1/jobs/{job_id}/logs — SSE Log Stream ───
@app.get("/api/v1/jobs/{job_id}/logs")
async def stream_logs(job_id: str):
    """Server-Sent Events endpoint for live processing logs."""

    async def event_generator():
        last_index = 0
        while True:
            logs = get_job_logs(job_id)
            new_logs = logs[last_index:]
            last_index = len(logs)

            for log_entry in new_logs:
                data = json.dumps(log_entry)
                yield f"data: {data}\n\n"

            # Check if job is complete
            try:
                analysis = await get_analysis_record(job_id)
                if analysis and analysis.get("status") in ("COMPLETED", "FAILED"):
                    # Send final batch
                    final_logs = get_job_logs(job_id)
                    for log_entry in final_logs[last_index:]:
                        data = json.dumps(log_entry)
                        yield f"data: {data}\n\n"
                    # Send close event
                    yield f"data: {json.dumps({'event': 'close', 'status': analysis['status']})}\n\n"
                    break
            except Exception:
                pass

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── POST /api/v1/jobs/{job_id}/force-include-quarantined ───
@app.post("/api/v1/jobs/{job_id}/force-include-quarantined")
async def force_include_quarantined(job_id: str, background_tasks: BackgroundTasks):
    """Re-run synthesis including quarantined files."""
    try:
        analysis = await get_analysis_record(job_id)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        file_records = await get_file_records_for_job(job_id)

        # Build file tasks
        file_tasks = []
        for fr in file_records:
            file_tasks.append({
                "file_id": fr.get("file_id"),
                "job_id": job_id,
                "filename": fr.get("original_name"),
                "file_type": fr.get("file_type"),
                "s3_key": fr.get("s3_key", f"uploads/{job_id}/{fr.get('file_id')}"),
                "agent": fr.get("agent", "generic_agent"),
                "routing_reason": "Re-run with quarantined files",
                "pdf_structure": None,
                "excel_structure": None,
            })

        # Re-run pipeline with force_include
        background_tasks.add_task(
            run_pipeline,
            job_id=job_id,
            file_tasks=file_tasks,
            force_include_quarantined=True,
        )

        return {
            "job_id": job_id,
            "status": "REPROCESSING",
            "message": "Re-running synthesis with quarantined files included",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("force_include_error", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /api/v1/health — Health Check ───
@app.get("/api/v1/health")
async def health_check():
    """Return system health status."""
    health: dict[str, str] = {"status": "ok"}

    # Check Bedrock
    try:
        import boto3
        bedrock = boto3.client(
            "bedrock-runtime",
            region_name=settings.AWS_REGION,
        )
        health["bedrock"] = "connected"
    except Exception:
        health["bedrock"] = "unavailable"

    # Check S3
    try:
        import boto3
        s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        s3.head_bucket(Bucket=settings.S3_BUCKET)
        health["s3"] = "connected"
    except Exception:
        health["s3"] = "unavailable"

    # Check DynamoDB
    try:
        import boto3
        dynamo = boto3.client("dynamodb", region_name=settings.AWS_REGION)
        dynamo.describe_table(TableName=settings.DYNAMO_FILES_TABLE)
        health["dynamo"] = "connected"
    except Exception:
        health["dynamo"] = "unavailable"

    return health


# ─── Error Handlers ───
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "REQUEST_FAILED",
            "message": exc.detail,
            "details": {},
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": {},
        },
    )


# ─── Startup ───
@app.on_event("startup")
async def startup():
    logger.info("application_startup", version="1.0.0")


@app.on_event("shutdown")
async def shutdown():
    logger.info("application_shutdown")
