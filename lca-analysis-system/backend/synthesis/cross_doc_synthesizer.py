"""Stage 2 — Cross-Document Synthesis for LCA analysis."""

from typing import Any

import structlog

from backend.processing.bedrock_client import invoke_claude_sonnet

logger = structlog.get_logger(__name__)


CROSS_DOC_SYNTHESIS_PROMPT = """You are an expert LCA (Life Cycle Assessment) analyst performing a cross-document synthesis.

You are given per-document summaries from {doc_count} LCA-related documents that have been individually analysed. Your task is to synthesise a unified analysis.

Identify:
1. Which documents cover which life cycle stages (A1-A3 manufacturing, A4-A5 construction, B1-B7 use, C1-C4 end-of-life, D benefits)
2. Any conflicts (different functional units, conflicting impact values for the same process)
3. Complementary data (documents that together cover a complete cradle-to-grave scope)
4. Overall methodological consistency (is the same impact assessment method used throughout?)
5. Write a unified narrative describing the complete LCA study covered by all documents

Return your analysis as a Markdown document with these EXACT sections:
## Study Overview
## Functional Unit
## System Boundary
## Coverage by Life Cycle Stage
## Methodological Consistency
## Conflicts and Discrepancies
## Cross-Document Synthesis

{user_context}

Per-document summaries:
---
{summaries}
---"""


async def synthesize_across_documents(
    doc_summaries: list[dict[str, Any]],
    user_context: str = "",
) -> str:
    """Perform cross-document synthesis using Claude Sonnet."""
    # Build the combined summaries text
    summary_parts = []
    for i, doc in enumerate(doc_summaries, 1):
        summary_parts.append(
            f"### Document {i}: {doc.get('filename', 'Unknown')}\n"
            f"**Type:** {doc.get('file_type', 'unknown')} | "
            f"**Agent:** {doc.get('agent', 'unknown')} | "
            f"**Confidence:** {doc.get('confidence', 0.0):.2f}\n\n"
            f"{doc.get('summary', 'No summary available.')}\n"
        )

    summaries_text = "\n---\n".join(summary_parts)

    context_clause = ""
    if user_context:
        context_clause = f"\nUser-provided context: {user_context}\n"

    prompt = CROSS_DOC_SYNTHESIS_PROMPT.format(
        doc_count=len(doc_summaries),
        summaries=summaries_text,
        user_context=context_clause,
    )

    try:
        synthesis = await invoke_claude_sonnet(
            prompt=prompt,
            system=(
                "You are an LCA synthesis expert. Produce a thorough cross-document "
                "analysis in Markdown format. Be specific about data, not generic."
            ),
            max_tokens=4096,
        )

        logger.info(
            "cross_doc_synthesis_complete",
            doc_count=len(doc_summaries),
            synthesis_length=len(synthesis),
        )

        return synthesis.strip()

    except Exception as e:
        logger.error("cross_doc_synthesis_error", error=str(e))
        return (
            "## Cross-Document Synthesis\n\n"
            f"*Synthesis generation failed: {str(e)}*\n\n"
            "Individual document summaries are available in the appendix."
        )
