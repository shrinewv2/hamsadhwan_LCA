"""Stage 3 — LCA-Specific Insight Extraction."""

from typing import Any

import structlog

from backend.processing.bedrock_client import invoke_claude_sonnet, parse_json_response

logger = structlog.get_logger(__name__)


INSIGHT_EXTRACTION_PROMPT = """You are an expert LCA (Life Cycle Assessment) analyst.

Given the following cross-document synthesis of an LCA study, extract specific insights.

**Hotspot Analysis:** Which processes, materials, or life cycle stages contribute most to environmental impact? List the top 5 hotspots with estimated percentage contribution if data allows.

**Uncertainty Assessment:** Where is data quality weakest? Which results are most uncertain and why?

**Completeness Assessment:** What percentage of the product system is covered? What is missing?

**Impact Results Table:** Extract ALL impact category results into a single consolidated table:
| Impact Category | Value | Unit | Life Cycle Stage | Source Document |

**Recommendations:** 3-5 specific, actionable recommendations for reducing the identified environmental hotspots.

Format the output as Markdown with these EXACT sections:
## Environmental Hotspots
## Consolidated Impact Results
## Uncertainty Assessment
## Completeness
## Recommendations

Cross-document synthesis:
---
{synthesis}
---"""


STRUCTURED_INSIGHTS_PROMPT = """You are an LCA data extraction specialist.

From the following LCA analysis text, extract structured data as JSON:

{{
    "functional_unit": "<string or null>",
    "system_boundary": "<string or null>",
    "impact_method": "<string or null>",
    "impact_results": [
        {{"category": "<name>", "value": <number>, "unit": "<unit>", "stage": "<stage or null>", "source": "<filename or null>"}}
    ],
    "hotspots": [
        {{"process": "<name>", "contribution_pct": <number or null>, "impact_category": "<category>"}}
    ],
    "data_quality": "<Excellent|Good|Fair|Poor>",
    "completeness": <0.0-1.0>,
    "recommendations": ["<string>", ...]
}}

Be precise with numeric values. If data is not available, use null.
Extract as many impact results and hotspots as possible from the text.

Analysis text:
---
{content}
---"""


async def extract_insights(synthesis_text: str) -> str:
    """Extract LCA-specific insights from the cross-document synthesis (Markdown output)."""
    prompt = INSIGHT_EXTRACTION_PROMPT.format(synthesis=synthesis_text)

    try:
        insights = await invoke_claude_sonnet(
            prompt=prompt,
            system=(
                "You are an LCA insight extraction expert. "
                "Produce detailed, specific insights in Markdown format. "
                "Include actual numbers and data wherever possible."
            ),
            max_tokens=4096,
        )

        logger.info("insight_extraction_complete", insights_length=len(insights))
        return insights.strip()

    except Exception as e:
        logger.error("insight_extraction_error", error=str(e))
        return (
            "## LCA Insights\n\n"
            f"*Insight extraction failed: {str(e)}*"
        )


async def extract_structured_insights(
    synthesis_text: str, insights_text: str
) -> dict[str, Any]:
    """Extract structured JSON data from the synthesis and insights."""
    combined = f"{synthesis_text}\n\n---\n\n{insights_text}"
    prompt = STRUCTURED_INSIGHTS_PROMPT.format(content=combined[:25000])

    try:
        raw = await invoke_claude_sonnet(
            prompt=prompt,
            system="You are an LCA data extractor. Respond only with valid JSON.",
            max_tokens=4096,
        )

        result = parse_json_response(raw)

        if result is None:
            logger.warning("structured_insights_parse_failed", raw_length=len(raw))
            return _default_structured_insights()

        # Ensure required keys
        result.setdefault("functional_unit", None)
        result.setdefault("system_boundary", None)
        result.setdefault("impact_method", None)
        result.setdefault("impact_results", [])
        result.setdefault("hotspots", [])
        result.setdefault("data_quality", "Fair")
        result.setdefault("completeness", 0.5)
        result.setdefault("recommendations", [])

        logger.info(
            "structured_insights_complete",
            impact_results_count=len(result["impact_results"]),
            hotspots_count=len(result["hotspots"]),
        )

        return result

    except Exception as e:
        logger.error("structured_insights_error", error=str(e))
        return _default_structured_insights()


def _default_structured_insights() -> dict[str, Any]:
    """Return default structured insights when extraction fails."""
    return {
        "functional_unit": None,
        "system_boundary": None,
        "impact_method": None,
        "impact_results": [],
        "hotspots": [],
        "data_quality": "Unknown",
        "completeness": 0.0,
        "recommendations": [],
    }
