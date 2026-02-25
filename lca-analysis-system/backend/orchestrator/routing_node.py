"""Routing node — assigns each file to the correct agent."""

from typing import Any

import structlog

from backend.models.enums import AgentType, FileType
from backend.processing.bedrock_client import invoke_claude_sonnet, parse_json_response

logger = structlog.get_logger(__name__)

# ─── Deterministic routing table ───
FILE_TYPE_TO_AGENT: dict[FileType, AgentType] = {
    FileType.EXCEL: AgentType.EXCEL_AGENT,
    FileType.CSV: AgentType.EXCEL_AGENT,
    FileType.IMAGE: AgentType.IMAGE_VLM_AGENT,
    FileType.MINDMAP_XMIND: AgentType.MINDMAP_AGENT,
    FileType.MINDMAP_FREEMIND: AgentType.MINDMAP_AGENT,
    FileType.DOCX: AgentType.GENERIC_AGENT,
    FileType.TEXT: AgentType.GENERIC_AGENT,
    FileType.PPTX: AgentType.GENERIC_AGENT,
}


LLM_ROUTING_PROMPT = """You are an LCA document routing specialist.

Given the following file metadata, determine the best processing agent.

Available agents:
- "excel_agent": For spreadsheets with tabular LCA data
- "pdf_hybrid_agent": For PDFs with mixed content (text, tables, images)
- "pdf_text_agent": For text-only PDFs
- "pdf_scanned_agent": For fully scanned/OCR PDFs
- "image_agent": For standalone images (charts, diagrams, photos)
- "mindmap_agent": For mind map files
- "generic_agent": For DOCX, TXT, PPTX, and other document types

File metadata:
- Filename: {filename}
- Detected type: {file_type}
- PDF structure (if PDF): {pdf_structure}

Return JSON: {{"agent": "<agent_name>", "reason": "<brief explanation>"}}"""


async def route_file(
    file_id: str,
    filename: str,
    file_type: str,
    pdf_structure: dict[str, Any] | None = None,
    excel_structure: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Route a single file to the appropriate agent.

    Uses deterministic rules first, LLM routing as fallback for ambiguous cases.
    """
    ft = FileType(file_type) if file_type in [e.value for e in FileType] else FileType.UNKNOWN

    # ─── Rule-based routing ───

    # PDF routing based on structure
    if ft == FileType.PDF and pdf_structure:
        is_scanned = pdf_structure.get("is_scanned", False)
        has_text = pdf_structure.get("has_text_layer", False)
        has_images = pdf_structure.get("has_embedded_images", False)
        has_tables = pdf_structure.get("has_tables_heuristic", False)

        if is_scanned:
            return {
                "agent": AgentType.PDF_SCANNED_AGENT.value,
                "reason": "Fully scanned PDF detected — using OCR-focused agent",
            }
        elif has_images or has_tables:
            return {
                "agent": AgentType.PDF_HYBRID_AGENT.value,
                "reason": "PDF with mixed content (text + images/tables) — using hybrid agent",
            }
        elif has_text:
            return {
                "agent": AgentType.PDF_TEXT_AGENT.value,
                "reason": "Text-only PDF — using text extraction agent",
            }
        else:
            return {
                "agent": AgentType.PDF_HYBRID_AGENT.value,
                "reason": "PDF structure unclear — defaulting to hybrid agent",
            }

    # Direct type mapping
    if ft in FILE_TYPE_TO_AGENT:
        agent = FILE_TYPE_TO_AGENT[ft]
        return {
            "agent": agent.value,
            "reason": f"Detected as {ft.value} file — routed to {agent.value}",
        }

    # ─── LLM routing for unknown types ───
    if ft == FileType.UNKNOWN:
        try:
            prompt = LLM_ROUTING_PROMPT.format(
                filename=filename,
                file_type=file_type,
                pdf_structure=pdf_structure or "N/A",
            )

            raw = await invoke_claude_sonnet(
                prompt=prompt,
                system="You are a file routing specialist. Return only JSON.",
                max_tokens=256,
            )

            result = parse_json_response(raw)
            if result and "agent" in result:
                logger.info(
                    "llm_routing",
                    file_id=file_id,
                    agent=result["agent"],
                    reason=result.get("reason", "LLM decision"),
                )
                return {
                    "agent": result["agent"],
                    "reason": result.get("reason", "LLM-based routing decision"),
                }
        except Exception as e:
            logger.warning("llm_routing_failed", file_id=file_id, error=str(e))

    # Ultimate fallback
    return {
        "agent": AgentType.GENERIC_AGENT.value,
        "reason": f"Unknown file type '{file_type}' — defaulting to generic agent",
    }


async def route_all_files(
    file_tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Route all files in a job and return updated tasks with agent assignments."""
    routed = []
    for task in file_tasks:
        routing = await route_file(
            file_id=task["file_id"],
            filename=task["filename"],
            file_type=task["file_type"],
            pdf_structure=task.get("pdf_structure"),
            excel_structure=task.get("excel_structure"),
        )
        task["agent"] = routing["agent"]
        task["routing_reason"] = routing["reason"]
        routed.append(task)

        logger.info(
            "file_routed",
            file_id=task["file_id"],
            filename=task["filename"],
            agent=routing["agent"],
            reason=routing["reason"],
        )

    return routed
