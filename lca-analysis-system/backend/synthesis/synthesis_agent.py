"""Synthesis agent — orchestrates all 3 synthesis stages."""

from typing import Any

import structlog

from backend.synthesis.cross_doc_synthesizer import synthesize_across_documents
from backend.synthesis.insight_extractor import (
    extract_insights,
    extract_structured_insights,
)
from backend.synthesis.per_doc_summarizer import summarize_all_documents

logger = structlog.get_logger(__name__)


async def run_synthesis(
    parsed_outputs: list[dict[str, Any]],
    user_context: str = "",
) -> dict[str, Any]:
    """Run the full 3-stage synthesis pipeline.

    Stage 1: Per-Document Summaries
    Stage 2: Cross-Document Synthesis
    Stage 3: LCA-Specific Insight Extraction

    Returns a dict with all synthesis artefacts.
    """
    logger.info("synthesis_pipeline_start", doc_count=len(parsed_outputs))

    # ─── Stage 1: Per-Document Summaries ───
    logger.info("synthesis_stage_1_start")
    doc_summaries = await summarize_all_documents(parsed_outputs)
    logger.info("synthesis_stage_1_complete", summaries=len(doc_summaries))

    # ─── Stage 2: Cross-Document Synthesis ───
    logger.info("synthesis_stage_2_start")
    cross_doc_synthesis = await synthesize_across_documents(
        doc_summaries, user_context=user_context
    )
    logger.info("synthesis_stage_2_complete", length=len(cross_doc_synthesis))

    # ─── Stage 3: Insight Extraction ───
    logger.info("synthesis_stage_3_start")
    insights_markdown = await extract_insights(cross_doc_synthesis)
    structured_insights = await extract_structured_insights(
        cross_doc_synthesis, insights_markdown
    )
    logger.info(
        "synthesis_stage_3_complete",
        insights_length=len(insights_markdown),
        impact_results=len(structured_insights.get("impact_results", [])),
    )

    result = {
        "doc_summaries": doc_summaries,
        "cross_doc_synthesis": cross_doc_synthesis,
        "insights_markdown": insights_markdown,
        "structured_insights": structured_insights,
    }

    logger.info("synthesis_pipeline_complete")
    return result
