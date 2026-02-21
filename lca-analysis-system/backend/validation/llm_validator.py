"""LLM-based validation for LCA data (Phase 5 from spec)."""

import json
from typing import Any

import structlog

from backend.processing.bedrock_client import invoke_claude_sonnet, parse_json_response

logger = structlog.get_logger(__name__)


TAXONOMY_VALIDATION_PROMPT = """You are an expert LCA (Life Cycle Assessment) validator.

Analyse the following extracted LCA content and validate it against standard LCA taxonomies
(EF 3.1, ReCiPe 2016, ISO 14040/14044).

For each issue, provide:
- "category": one of "unit_error", "taxonomy_mismatch", "plausibility", "completeness", "methodology"
- "severity": one of "info", "warning", "error"
- "description": clear description of the issue
- "location": approximate location in the text (quote relevant portion)
- "suggestion": recommended fix or action

Also evaluate overall:
- "methodology_score": 0-100 (how well the methodology follows ISO 14040/44)
- "data_quality_score": 0-100 (quality of reported data)
- "completeness_score": 0-100 (completeness of the LCA study)

Return a JSON object:
{{
    "issues": [...],
    "methodology_score": <int>,
    "data_quality_score": <int>,
    "completeness_score": <int>,
    "summary": "<brief overall assessment>"
}}

Content to validate:
---
{content}
---"""


PLAUSIBILITY_VALIDATION_PROMPT = """You are an expert LCA data analyst.

Review the following LCA data and check each numeric value for plausibility.
Compare values against typical ranges for the materials, processes, and impact categories mentioned.

Flag any values that seem:
1. Unrealistically high or low
2. In the wrong order of magnitude
3. Using incorrect units
4. Inconsistent with other values in the same document

For each flagged value, provide:
- "value": the numeric value
- "context": what the value represents
- "expected_range": typical range for this type of value
- "severity": "warning" or "error"
- "explanation": why this value seems implausible

Return a JSON object:
{{
    "flags": [...],
    "overall_plausibility": "high" | "medium" | "low",
    "confidence": 0.0-1.0
}}

Data to validate:
---
{content}
---"""


class LLMValidator:
    """Uses Claude Sonnet for advanced LCA validation beyond rule-based checks."""

    async def validate_taxonomy(
        self, markdown_content: str, max_content_length: int = 15000
    ) -> dict[str, Any]:
        """Validate content against LCA taxonomies using LLM."""
        # Truncate if needed to stay within context
        content = markdown_content[:max_content_length]

        prompt = TAXONOMY_VALIDATION_PROMPT.format(content=content)

        try:
            raw = await invoke_claude_sonnet(
                prompt=prompt,
                system="You are an LCA validation expert. Respond only with valid JSON.",
                max_tokens=4096,
            )

            result = parse_json_response(raw)

            if result is None:
                logger.warning("llm_taxonomy_validation_parse_failed", raw_length=len(raw))
                return {
                    "issues": [],
                    "methodology_score": 0,
                    "data_quality_score": 0,
                    "completeness_score": 0,
                    "summary": "LLM validation response could not be parsed.",
                    "raw_response": raw[:500],
                }

            logger.info(
                "llm_taxonomy_validation_complete",
                issues_count=len(result.get("issues", [])),
                methodology_score=result.get("methodology_score"),
            )

            return result

        except Exception as e:
            logger.error("llm_taxonomy_validation_error", error=str(e))
            return {
                "issues": [],
                "methodology_score": 0,
                "data_quality_score": 0,
                "completeness_score": 0,
                "summary": f"LLM validation failed: {str(e)}",
            }

    async def validate_plausibility(
        self, markdown_content: str, max_content_length: int = 15000
    ) -> dict[str, Any]:
        """Check numeric plausibility using LLM."""
        content = markdown_content[:max_content_length]

        prompt = PLAUSIBILITY_VALIDATION_PROMPT.format(content=content)

        try:
            raw = await invoke_claude_sonnet(
                prompt=prompt,
                system="You are an LCA data analyst. Respond only with valid JSON.",
                max_tokens=4096,
            )

            result = parse_json_response(raw)

            if result is None:
                logger.warning("llm_plausibility_validation_parse_failed", raw_length=len(raw))
                return {
                    "flags": [],
                    "overall_plausibility": "unknown",
                    "confidence": 0.0,
                    "raw_response": raw[:500],
                }

            logger.info(
                "llm_plausibility_validation_complete",
                flags_count=len(result.get("flags", [])),
                overall_plausibility=result.get("overall_plausibility"),
            )

            return result

        except Exception as e:
            logger.error("llm_plausibility_validation_error", error=str(e))
            return {
                "flags": [],
                "overall_plausibility": "unknown",
                "confidence": 0.0,
                "error": str(e),
            }

    async def validate_all(
        self, markdown_content: str
    ) -> dict[str, Any]:
        """Run all LLM-based validations and combine results."""
        taxonomy_result = await self.validate_taxonomy(markdown_content)
        plausibility_result = await self.validate_plausibility(markdown_content)

        combined = {
            "taxonomy": taxonomy_result,
            "plausibility": plausibility_result,
            "overall_scores": {
                "methodology": taxonomy_result.get("methodology_score", 0),
                "data_quality": taxonomy_result.get("data_quality_score", 0),
                "completeness": taxonomy_result.get("completeness_score", 0),
                "plausibility": plausibility_result.get("overall_plausibility", "unknown"),
            },
            "total_issues": len(taxonomy_result.get("issues", []))
            + len(plausibility_result.get("flags", [])),
        }

        logger.info(
            "llm_validation_all_complete",
            total_issues=combined["total_issues"],
            overall_scores=combined["overall_scores"],
        )

        return combined
