"""Dispatcher — routes file tasks to the correct agent and executes them."""

import time
from typing import Any

import structlog

from backend.agents.excel_agent import ExcelAgent
from backend.agents.generic_agent import GenericAgent
from backend.agents.image_agent import ImageAgent
from backend.agents.mindmap_agent import MindMapAgent
from backend.agents.pdf_agent import PDFHybridAgent, PDFScannedAgent, PDFTextAgent
from backend.config import settings
from backend.models.enums import AgentType, FileStatus, FileType
from backend.models.schemas import FileMetadata
from backend.storage.dynamo_client import update_file_record
from backend.storage.s3_client import download_bytes
from backend.utils.logger import append_job_log

logger = structlog.get_logger(__name__)

# Agent registry
AGENT_CLASSES = {
    AgentType.EXCEL_AGENT.value: ExcelAgent,
    AgentType.PDF_HYBRID_AGENT.value: PDFHybridAgent,
    AgentType.PDF_TEXT_AGENT.value: PDFTextAgent,
    AgentType.PDF_SCANNED_AGENT.value: PDFScannedAgent,
    AgentType.IMAGE_VLM_AGENT.value: ImageAgent,
    AgentType.MINDMAP_AGENT.value: MindMapAgent,
    AgentType.GENERIC_AGENT.value: GenericAgent,
    "image_agent": ImageAgent,
}


async def dispatch_file(task: dict[str, Any]) -> dict[str, Any]:
    """Process a single file task using the assigned agent.

    Downloads the file from S3, instantiates the correct agent, and runs processing.
    Returns the parsed output dict.
    """
    file_id = task["file_id"]
    job_id = task["job_id"]
    agent_name = task["agent"]
    filename = task["filename"]
    s3_key = task["s3_key"]
    file_type = task["file_type"]

    logger.info(
        "dispatch_file_start",
        file_id=file_id,
        agent=agent_name,
        filename=filename,
    )

    append_job_log(
        job_id,
        "INFO",
        agent_name,
        f"Starting processing of {filename}",
        file_id=file_id,
    )

    start_time = time.time()

    try:
        # Update status to PROCESSING
        await update_file_record(file_id, {"status": "PROCESSING", "agent": agent_name})

        # Download file bytes from S3
        file_bytes = download_bytes(
            settings.S3_BUCKET_UPLOADS if settings else "lca-uploads",
            s3_key,
        )

        # Instantiate agent
        agent_class = AGENT_CLASSES.get(agent_name)
        if not agent_class:
            raise ValueError(f"Unknown agent: {agent_name}")

        agent = agent_class()

        # Build file metadata for the agent
        try:
            resolved_file_type = FileType(file_type)
        except Exception:
            resolved_file_type = FileType.UNKNOWN

        file_meta = FileMetadata(
            file_id=file_id,
            job_id=job_id,
            original_name=filename,
            s3_key=s3_key,
            actual_mime="application/octet-stream",
            file_type=resolved_file_type,
            size_bytes=len(file_bytes),
            is_scanned=bool((task.get("pdf_structure") or {}).get("is_scanned", False)),
            has_text_layer=bool((task.get("pdf_structure") or {}).get("has_text_layer", False)),
            has_embedded_images=bool((task.get("pdf_structure") or {}).get("has_embedded_images", False)),
            page_count=(task.get("pdf_structure") or {}).get("page_count"),
            sheet_count=(task.get("excel_structure") or {}).get("sheet_count"),
            complexity_score=0.0,
            status=FileStatus.PROCESSING,
            agent_assigned=agent_name,
        )

        # Run agent processing
        result = agent.safe_process(file_meta, file_bytes)

        processing_time = time.time() - start_time

        # Build parsed output
        parsed_output = {
            "file_id": file_id,
            "job_id": job_id,
            "filename": filename,
            "file_type": file_type,
            "agent": agent_name,
            "markdown": result.markdown,
            "structured_json": result.structured_json,
            "lca_relevant": result.lca_relevant,
            "confidence": result.confidence,
            "low_confidence_pages": result.low_confidence_pages,
            "word_count": len(result.markdown.split()),
            "processing_time_s": round(processing_time, 2),
            "errors": result.errors,
            "warnings": result.warnings,
            "status": "COMPLETED",
        }

        # Update DynamoDB
        await update_file_record(file_id, {
            "status": "COMPLETED",
            "confidence": str(parsed_output["confidence"]),
            "processing_time_s": str(parsed_output["processing_time_s"]),
            "word_count": parsed_output["word_count"],
        })

        append_job_log(
            job_id,
            "INFO",
            agent_name,
            f"Completed {filename} in {processing_time:.1f}s (confidence: {parsed_output['confidence']:.2f})",
            file_id=file_id,
        )

        logger.info(
            "dispatch_file_complete",
            file_id=file_id,
            agent=agent_name,
            confidence=parsed_output["confidence"],
            time_s=processing_time,
        )

        return parsed_output

    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)

        logger.error(
            "dispatch_file_error",
            file_id=file_id,
            agent=agent_name,
            error=error_msg,
        )

        append_job_log(
            job_id,
            "ERROR",
            agent_name,
            f"Failed to process {filename}: {error_msg}",
            file_id=file_id,
        )

        # Update DynamoDB with failure
        await update_file_record(file_id, {
            "status": "FAILED",
            "error": error_msg[:500],
        })

        return {
            "file_id": file_id,
            "job_id": job_id,
            "filename": filename,
            "file_type": file_type,
            "agent": agent_name,
            "markdown": "",
            "structured_json": {},
            "lca_relevant": False,
            "confidence": 0.0,
            "low_confidence_pages": [],
            "word_count": 0,
            "processing_time_s": round(processing_time, 2),
            "errors": [error_msg],
            "warnings": [],
            "status": "FAILED",
        }


async def dispatch_all_files(
    file_tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Dispatch all file tasks to their assigned agents.

    For simplicity, processes sequentially. LangGraph Send API handles
    parallel dispatch at the graph level.
    """
    results = []
    for task in file_tasks:
        result = await dispatch_file(task)
        results.append(result)
    return results
