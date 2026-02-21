"""LangGraph state definition for the multi-agent pipeline."""

from typing import Any, TypedDict


class FileTask(TypedDict):
    """A single file task to be processed by an agent."""
    file_id: str
    job_id: str
    filename: str
    file_type: str
    s3_key: str
    agent: str
    routing_reason: str
    pdf_structure: dict[str, Any] | None
    excel_structure: dict[str, Any] | None


class AgentState(TypedDict, total=False):
    """The global state that flows through the LangGraph pipeline.

    This TypedDict is used as the LangGraph StateGraph state schema.
    """
    # ─── Inputs ───
    job_id: str
    user_context: str
    file_tasks: list[FileTask]
    force_include_quarantined: bool

    # ─── Agent Outputs ───
    parsed_outputs: list[dict[str, Any]]  # Raw agent outputs

    # ─── Normalization ───
    normalized_outputs: list[dict[str, Any]]  # After normalization

    # ─── Validation ───
    validation_reports: list[dict[str, Any]]
    quarantined_file_ids: list[str]

    # ─── Synthesis ───
    synthesis_result: dict[str, Any]

    # ─── Output ───
    markdown_report: str
    analysis_json: dict[str, Any]
    viz_data: dict[str, Any]
    audit_trail: dict[str, Any]

    # ─── Pipeline status ───
    errors: list[dict[str, Any]]
    current_phase: str
    progress: int  # 0-100
