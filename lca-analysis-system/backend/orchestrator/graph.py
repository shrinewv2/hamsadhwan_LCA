"""LangGraph StateGraph — the main orchestration pipeline.

Nodes:
  routing_node → agent dispatch → normalization → validation → synthesis → output

Uses LangGraph Send API for parallel agent dispatch.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

import structlog
from langgraph.graph import END, StateGraph

from backend.models.enums import FileStatus
from backend.normalization.normalizer import normalize_all
from backend.orchestrator.dispatcher import dispatch_file
from backend.orchestrator.routing_node import route_all_files
from backend.orchestrator.state import AgentState
from backend.output.audit_logger import build_audit_trail
from backend.output.json_exporter import export_analysis_json
from backend.output.report_generator import generate_report
from backend.output.viz_data_builder import build_viz_data
from backend.storage.dynamo_client import get_file_records_for_job, update_analysis_record
from backend.synthesis.synthesis_agent import run_synthesis
from backend.utils.logger import append_job_log
from backend.validation.llm_validator import LLMValidator
from backend.validation.rule_validator import RuleValidator

logger = structlog.get_logger(__name__)


# ─────────────────────────── Node Functions ───────────────────────────


async def routing_node(state: AgentState) -> dict[str, Any]:
    """Route all files to the correct agents."""
    job_id = state["job_id"]
    append_job_log(job_id, "INFO", "orchestrator", "Starting file routing")

    file_tasks = state.get("file_tasks", [])
    routed_tasks = await route_all_files(file_tasks)

    append_job_log(
        job_id, "INFO", "orchestrator",
        f"Routing complete — {len(routed_tasks)} files assigned to agents"
    )

    return {
        "file_tasks": routed_tasks,
        "current_phase": "routing",
        "progress": 10,
    }


async def agent_processing_node(state: AgentState) -> dict[str, Any]:
    """Dispatch all files to their assigned agents and collect outputs."""
    job_id = state["job_id"]
    file_tasks = state.get("file_tasks", [])
    append_job_log(
        job_id, "INFO", "orchestrator",
        f"Starting agent processing for {len(file_tasks)} files"
    )

    # Process files — could be parallelized with Send API
    # For now, use asyncio.gather for concurrent processing
    tasks = [dispatch_file(task) for task in file_tasks]
    parsed_outputs = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle exceptions
    results = []
    errors = state.get("errors", [])
    for i, output in enumerate(parsed_outputs):
        if isinstance(output, Exception):
            error_entry = {
                "file_id": file_tasks[i].get("file_id", "unknown"),
                "phase": "agent_processing",
                "error": str(output),
            }
            errors.append(error_entry)
            logger.error("agent_processing_exception", **error_entry)
        else:
            results.append(output)

    append_job_log(
        job_id, "INFO", "orchestrator",
        f"Agent processing complete — {len(results)} files processed, {len(errors)} errors"
    )

    return {
        "parsed_outputs": results,
        "errors": errors,
        "current_phase": "agent_processing",
        "progress": 40,
    }


async def normalization_node(state: AgentState) -> dict[str, Any]:
    """Normalize all agent outputs to the unified ParsedOutput schema."""
    job_id = state["job_id"]
    parsed_outputs = state.get("parsed_outputs", [])
    append_job_log(job_id, "INFO", "normalizer", "Starting normalization")

    normalized_models = normalize_all(parsed_outputs)
    normalized = [
        item.model_dump() if hasattr(item, "model_dump") else item
        for item in normalized_models
    ]

    append_job_log(
        job_id, "INFO", "normalizer",
        f"Normalization complete — {len(normalized)} outputs normalized"
    )

    return {
        "normalized_outputs": normalized,
        "current_phase": "normalization",
        "progress": 55,
    }


async def validation_node(state: AgentState) -> dict[str, Any]:
    """Run rule-based and LLM-based validation on all normalized outputs."""
    job_id = state["job_id"]
    normalized_outputs = state.get("normalized_outputs", [])
    force_include = state.get("force_include_quarantined", False)

    append_job_log(job_id, "INFO", "validator", "Starting validation")

    rule_validator = RuleValidator()
    llm_validator = LLMValidator()
    validation_reports = []
    quarantined_ids = []

    for output in normalized_outputs:
        file_id = output.get("file_id", "unknown")
        markdown = output.get("markdown", "")

        append_job_log(
            job_id, "INFO", "validator",
            f"Validating {output.get('filename', 'unknown')}",
            file_id=file_id,
        )

        # Track A — Rule-based
        rule_results = rule_validator.validate(markdown)
        rule_errors = [r["message"] for r in rule_results if not r["passed"] and r["severity"] == "error"]
        rule_warnings = [r["message"] for r in rule_results if not r["passed"] and r["severity"] == "warning"]

        # Track B — LLM-based
        llm_result = await llm_validator.validate_all(markdown)
        taxonomy_issues = [
            issue.get("description", "")
            for issue in llm_result.get("taxonomy", {}).get("issues", [])
        ]
        plausibility_flags = [
            flag.get("explanation", "")
            for flag in llm_result.get("plausibility", {}).get("flags", [])
        ]

        # Determine status
        data_quality = llm_result.get("taxonomy", {}).get("data_quality_score", 50)
        if data_quality >= 75:
            dq_rating = "Good"
        elif data_quality >= 50:
            dq_rating = "Fair"
        elif data_quality >= 25:
            dq_rating = "Poor"
        else:
            dq_rating = "Poor"

        if rule_errors:
            status = "failed"
        elif rule_warnings or taxonomy_issues:
            status = "passed_with_warnings"
        else:
            status = "passed"

        # Quarantine logic
        if status == "failed" and not force_include:
            quarantined_ids.append(file_id)
            status = "quarantined"

        report = {
            "file_id": file_id,
            "filename": output.get("filename", "unknown"),
            "status": status,
            "rule_errors": rule_errors,
            "rule_warnings": rule_warnings,
            "taxonomy_issues": taxonomy_issues,
            "cross_doc_conflicts": [],  # Will be filled in synthesis
            "plausibility_flags": plausibility_flags,
            "data_quality_rating": dq_rating,
            "llm_confidence_score": (llm_result.get("taxonomy", {}).get("completeness_score") or 0) / 100.0,
        }
        validation_reports.append(report)

        append_job_log(
            job_id, "INFO", "validator",
            f"Validation for {output.get('filename', 'unknown')}: {status}",
            file_id=file_id,
        )

    append_job_log(
        job_id, "INFO", "validator",
        f"Validation complete — {len(quarantined_ids)} quarantined"
    )

    return {
        "validation_reports": validation_reports,
        "quarantined_file_ids": quarantined_ids,
        "current_phase": "validation",
        "progress": 65,
    }


async def synthesis_node(state: AgentState) -> dict[str, Any]:
    """Run 3-stage synthesis on validated outputs."""
    job_id = state["job_id"]
    normalized_outputs = state.get("normalized_outputs", [])
    quarantined_ids = state.get("quarantined_file_ids", [])
    validation_reports = state.get("validation_reports", [])
    user_context = state.get("user_context", "")

    append_job_log(job_id, "INFO", "synthesis", "Starting synthesis pipeline")

    # Prepare outputs for synthesis (excluding quarantined)
    synthesis_inputs = []
    for output in normalized_outputs:
        fid = output.get("file_id", "")
        if fid in quarantined_ids:
            continue

        # Attach validation info
        val_report = next(
            (v for v in validation_reports if v.get("file_id") == fid), {}
        )
        output["validation"] = val_report
        synthesis_inputs.append(output)

    if not synthesis_inputs:
        append_job_log(job_id, "WARNING", "synthesis", "No non-quarantined files to synthesize")
        return {
            "synthesis_result": {
                "doc_summaries": [],
                "cross_doc_synthesis": "No files available for synthesis.",
                "insights_markdown": "",
                "structured_insights": {},
            },
            "current_phase": "synthesis",
            "progress": 80,
        }

    result = await run_synthesis(synthesis_inputs, user_context=user_context)

    append_job_log(job_id, "INFO", "synthesis", "Synthesis complete")

    return {
        "synthesis_result": result,
        "current_phase": "synthesis",
        "progress": 80,
    }


async def output_node(state: AgentState) -> dict[str, Any]:
    """Generate all 4 output deliverables."""
    job_id = state["job_id"]
    synthesis_result = state.get("synthesis_result", {})
    validation_reports = state.get("validation_reports", [])
    normalized_outputs = state.get("normalized_outputs", [])

    append_job_log(job_id, "INFO", "output", "Generating outputs")

    # Build file records for output generation
    file_records = []
    for output in normalized_outputs:
        val_report = next(
            (v for v in validation_reports if v.get("file_id") == output.get("file_id")),
            {},
        )
        file_records.append({
            "file_id": output.get("file_id"),
            "original_name": output.get("filename"),
            "file_type": output.get("file_type"),
            "agent": output.get("agent"),
            "confidence": output.get("confidence", 0.0),
            "status": val_report.get("status", "unknown"),
            "validation_status": val_report.get("status", "unknown"),
            "processing_time_s": output.get("processing_time_s", 0),
            "routing_reason": output.get("routing_reason", ""),
            "errors": output.get("errors", []),
        })

    # Output 1 — Markdown Report
    markdown_report = await generate_report(
        job_id, synthesis_result, validation_reports, file_records
    )

    # Output 2 — Structured JSON
    analysis_json = await export_analysis_json(
        job_id, synthesis_result, validation_reports, file_records
    )

    # Output 3 — Visualization Data
    viz_data = await build_viz_data(
        job_id, synthesis_result, validation_reports, file_records
    )

    # Output 4 — Audit Trail
    # Use a reasonable start time estimation
    start_time_str = state.get("start_time")
    if start_time_str:
        start_time = datetime.fromisoformat(start_time_str)
    else:
        start_time = datetime.now(timezone.utc)

    audit_trail = await build_audit_trail(
        job_id, start_time, file_records, validation_reports, state.get("errors", [])
    )

    # Update DynamoDB analysis record
    try:
        await update_analysis_record(job_id, {
            "status": "COMPLETED",
            "report_s3_key": f"reports/{job_id}/full_report.md",
            "analysis_json_s3_key": f"reports/{job_id}/analysis.json",
            "viz_data_s3_key": f"reports/{job_id}/viz_data.json",
            "audit_s3_key": f"audit/{job_id}/audit.json",
        })
    except Exception as e:
        logger.error("dynamo_update_failed", job_id=job_id, error=str(e))

    append_job_log(job_id, "INFO", "output", "All outputs generated successfully")

    return {
        "markdown_report": markdown_report,
        "analysis_json": analysis_json,
        "viz_data": viz_data,
        "audit_trail": audit_trail,
        "current_phase": "output",
        "progress": 100,
    }


# ─────────────────────────── Build the Graph ───────────────────────────


def build_pipeline_graph() -> StateGraph:
    """Build and compile the LangGraph StateGraph for the LCA pipeline."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("routing", routing_node)
    graph.add_node("agent_processing", agent_processing_node)
    graph.add_node("normalization", normalization_node)
    graph.add_node("validation", validation_node)
    graph.add_node("synthesis", synthesis_node)
    graph.add_node("output", output_node)

    # Define edges — linear pipeline
    graph.set_entry_point("routing")
    graph.add_edge("routing", "agent_processing")
    graph.add_edge("agent_processing", "normalization")
    graph.add_edge("normalization", "validation")
    graph.add_edge("validation", "synthesis")
    graph.add_edge("synthesis", "output")
    graph.add_edge("output", END)

    return graph


def get_compiled_pipeline():
    """Get a compiled, ready-to-invoke pipeline."""
    graph = build_pipeline_graph()
    return graph.compile()


# ─────────────────────────── Pipeline Runner ───────────────────────────


async def run_pipeline(
    job_id: str,
    file_tasks: list[dict[str, Any]],
    user_context: str = "",
    force_include_quarantined: bool = False,
) -> dict[str, Any]:
    """Run the full LCA analysis pipeline for a job.

    This is the main entry point called by the API route's BackgroundTasks.
    """
    logger.info("pipeline_start", job_id=job_id, file_count=len(file_tasks))
    append_job_log(job_id, "INFO", "orchestrator", f"Pipeline started for {len(file_tasks)} files")

    start_time = datetime.now(timezone.utc)

    # Update analysis record to PROCESSING
    try:
        await update_analysis_record(job_id, {"status": "PROCESSING"})
    except Exception as e:
        logger.warning("dynamo_status_update_failed", error=str(e))

    initial_state: AgentState = {
        "job_id": job_id,
        "user_context": user_context,
        "file_tasks": file_tasks,
        "force_include_quarantined": force_include_quarantined,
        "parsed_outputs": [],
        "normalized_outputs": [],
        "validation_reports": [],
        "quarantined_file_ids": [],
        "synthesis_result": {},
        "markdown_report": "",
        "analysis_json": {},
        "viz_data": {},
        "audit_trail": {},
        "errors": [],
        "current_phase": "starting",
        "progress": 0,
    }

    try:
        pipeline = get_compiled_pipeline()
        final_state = await pipeline.ainvoke(initial_state)

        logger.info("pipeline_complete", job_id=job_id, progress=final_state.get("progress"))
        append_job_log(job_id, "INFO", "orchestrator", "Pipeline completed successfully")

        return final_state

    except Exception as e:
        logger.error("pipeline_failed", job_id=job_id, error=str(e))
        append_job_log(job_id, "ERROR", "orchestrator", f"Pipeline failed: {str(e)}")

        # Mark as FAILED
        try:
            await update_analysis_record(job_id, {
                "status": "FAILED",
                "error": str(e)[:500],
            })
        except Exception:
            pass

        raise
