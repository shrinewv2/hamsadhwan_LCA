"""Dispatcher — routes file tasks to the correct agent and executes them."""

import time
from typing import Any

import structlog

from backend.agents.excel_agent import ExcelAgent
from backend.agents.generic_agent import GenericAgent
from backend.agents.image_agent import ImageAgent
from backend.agents.mindmap_agent import MindMapAgent
from backend.agents.pdf_agent import PDFHybridAgent, PDFScannedAgent, PDFTextAgent
from backend.models.enums import AgentType
from backend.storage.dynamo_client import update_file_record
from backend.storage.s3_client import download_bytes
from backend.utils.logger import append_job_log

logger = structlog.get_logger(__name__)

# Agent registry
AGENT_CLASSES = {
    AgentType.EXCEL.value: ExcelAgent,
    AgentType.PDF_HYBRID.value: PDFHybridAgent,
    AgentType.PDF_TEXT.value: PDFTextAgent,
    AgentType.PDF_SCANNED.value: PDFScannedAgent,
    AgentType.IMAGE.value: ImageAgent,
    AgentType.MINDMAP.value: MindMapAgent,
    AgentType.GENERIC.value: GenericAgent,
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
        file_bytes = await download_bytes(s3_key)

        # Instantiate agent
        agent_class = AGENT_CLASSES.get(agent_name)
        if not agent_class:
            raise ValueError(f"Unknown agent: {agent_name}")

        agent = agent_class()

        # Build context for the agent
        context = {
            "file_id": file_id,
            "job_id": job_id,
            "filename": filename,
            "file_type": file_type,
            "s3_key": s3_key,
            "file_bytes": file_bytes,
            "pdf_structure": task.get("pdf_structure"),
            "excel_structure": task.get("excel_structure"),
        }

        # Run agent processing
        result = await agent.safe_process(context)

        processing_time = time.time() - start_time

        # Build parsed output
        parsed_output = {
            "file_id": file_id,
            "job_id": job_id,
            "filename": filename,
            "file_type": file_type,
            "agent": agent_name,
            "markdown": result.get("markdown", ""),
            "structured_json": result.get("structured_json", {}),
            "lca_relevant": result.get("lca_relevant", False),
            "confidence": result.get("confidence", 0.0),
            "low_confidence_pages": result.get("low_confidence_pages", []),
            "word_count": len(result.get("markdown", "").split()),
            "processing_time_s": round(processing_time, 2),
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
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
