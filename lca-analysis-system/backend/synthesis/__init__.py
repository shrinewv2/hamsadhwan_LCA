"""Synthesis layer for LCA multi-document analysis."""

from backend.synthesis.cross_doc_synthesizer import synthesize_across_documents
from backend.synthesis.insight_extractor import (
    extract_insights,
    extract_structured_insights,
)
from backend.synthesis.per_doc_summarizer import (
    summarize_all_documents,
    summarize_document,
)
from backend.synthesis.synthesis_agent import run_synthesis

__all__ = [
    "run_synthesis",
    "summarize_document",
    "summarize_all_documents",
    "synthesize_across_documents",
    "extract_insights",
    "extract_structured_insights",
]
