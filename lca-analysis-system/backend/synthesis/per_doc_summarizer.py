"""Stage 1 — Per-Document Summaries for LCA synthesis."""

from typing import Any

import structlog

from backend.processing.bedrock_client import invoke_claude_sonnet

logger = structlog.get_logger(__name__)


PER_DOC_SUMMARY_PROMPT = """You are an expert LCA (Life Cycle Assessment) analyst.

Produce a structured 300-500 word summary of the following extracted LCA document content.

Cover:
- What document this is (type, apparent purpose)
- What LCA data it contains (which impact categories, functional unit if identified, system boundary if stated)
- Data quality assessment based on the validation report provided
- Any red flags or missing information
- Key numeric findings (up to 5 most significant values)

Format the summary as Markdown with these EXACT sub-headings:
### Document Overview
### LCA Content
### Data Quality
### Key Findings
### Flags

Document filename: {filename}
Document type: {file_type}
Agent used: {agent}
Confidence: {confidence}

Validation summary:
{validation_summary}

Extracted content:
---
{content}
---"""


async def summarize_document(
    file_id: str,
    filename: str,
    file_type: str,
    agent: str,
    confidence: float,
    markdown_content: str,
    validation_summary: str = "No validation data available.",
    max_content_length: int = 20000,
) -> dict[str, Any]:
    """Generate a per-document summary using Claude Sonnet."""
    content = markdown_content[:max_content_length]

    prompt = PER_DOC_SUMMARY_PROMPT.format(
        filename=filename,
        file_type=file_type,
        agent=agent,
        confidence=confidence,
        validation_summary=validation_summary,
        content=content,
    )

    try:
        summary = await invoke_claude_sonnet(
            prompt=prompt,
            system="You are an LCA document analyst. Return only Markdown formatted text.",
            max_tokens=2048,
        )

        logger.info(
            "per_doc_summary_complete",
            file_id=file_id,
            summary_length=len(summary),
        )

        return {
            "file_id": file_id,
            "filename": filename,
            "file_type": file_type,
            "agent": agent,
            "confidence": confidence,
            "summary": summary.strip(),
        }

    except Exception as e:
        logger.error("per_doc_summary_error", file_id=file_id, error=str(e))
        return {
            "file_id": file_id,
            "filename": filename,
            "file_type": file_type,
            "agent": agent,
            "confidence": confidence,
            "summary": f"*Summary generation failed: {str(e)}*",
            "error": str(e),
        }


async def summarize_all_documents(
    parsed_outputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate summaries for all non-quarantined documents."""
    summaries = []

    for doc in parsed_outputs:
        file_id = doc.get("file_id", "unknown")
        if doc.get("status") == "QUARANTINED":
            logger.info("skipping_quarantined_doc", file_id=file_id)
            continue

        validation_summary = "No validation data available."
        if doc.get("validation"):
            vr = doc["validation"]
            parts = []
            if vr.get("rule_errors"):
                parts.append(f"Rule errors: {', '.join(vr['rule_errors'])}")
            if vr.get("rule_warnings"):
                parts.append(f"Rule warnings: {', '.join(vr['rule_warnings'])}")
            if vr.get("data_quality_rating"):
                parts.append(f"Data quality: {vr['data_quality_rating']}")
            validation_summary = "\n".join(parts) if parts else validation_summary

        summary = await summarize_document(
            file_id=file_id,
            filename=doc.get("filename", "unknown"),
            file_type=doc.get("file_type", "unknown"),
            agent=doc.get("agent", "unknown"),
            confidence=doc.get("confidence", 0.0),
            markdown_content=doc.get("markdown", ""),
            validation_summary=validation_summary,
        )
        summaries.append(summary)

    logger.info("all_doc_summaries_complete", count=len(summaries))
    return summaries
