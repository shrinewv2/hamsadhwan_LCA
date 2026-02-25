"""Image VLM Agent — two-pass image analysis using Vision models."""
from backend.agents.base_agent import BaseAgent
from backend.config import get_settings
from backend.models.schemas import FileMetadata, ParsedOutput
from backend.processing.vlm_client import classify_image, extract_from_image
from backend.utils.logger import append_job_log, get_logger

logger = get_logger("image_agent")


class ImageVLMAgent(BaseAgent):
    agent_name = "image_agent"

    def process(self, file_meta: FileMetadata, file_bytes: bytes) -> ParsedOutput:
        warnings = []

        # Pass 1 — Visual Classification
        append_job_log(
            file_meta.job_id, "INFO", self.agent_name, file_meta.file_id,
            "Pass 1: Visual classification"
        )
        classification = classify_image(file_bytes)
        visual_type = classification.get("visual_type", "other")
        confidence_raw = classification.get("confidence", 3)
        brief_desc = classification.get("brief_description", "")

        append_job_log(
            file_meta.job_id, "INFO", self.agent_name, file_meta.file_id,
            f"Classified as '{visual_type}' (confidence={confidence_raw}/5): {brief_desc}"
        )

        # Confidence gate
        cfg = get_settings()
        vlm_min = cfg.VLM_MIN_CONFIDENCE
        low_confidence = confidence_raw < vlm_min
        if low_confidence:
            warnings.append(
                f"Low confidence classification ({confidence_raw}/5). "
                f"Result flagged for human review."
            )
            append_job_log(
                file_meta.job_id, "WARN", self.agent_name, file_meta.file_id,
                f"Low confidence: {confidence_raw}/5 (threshold={vlm_min})"
            )

        # Pass 2 — Type-Specific Extraction
        append_job_log(
            file_meta.job_id, "INFO", self.agent_name, file_meta.file_id,
            f"Pass 2: Extracting content for type '{visual_type}'"
        )
        extraction = extract_from_image(file_bytes, visual_type)

        # Build markdown
        markdown_parts = [
            f"# Image Analysis: {file_meta.original_name}\n",
            f"**Visual Type:** {visual_type}",
            f"**Description:** {brief_desc}",
            f"**Classification Confidence:** {confidence_raw}/5\n",
            "## Extracted Content\n",
            extraction,
        ]

        if low_confidence:
            markdown_parts.append(
                "\n\n> **Warning:** This extraction has low confidence "
                "and should be reviewed by a human analyst."
            )

        full_markdown = "\n".join(markdown_parts)

        return ParsedOutput(
            file_id=file_meta.file_id,
            job_id=file_meta.job_id,
            agent=self.agent_name,
            markdown=full_markdown,
            structured_json={
                "visual_type": visual_type,
                "classification_confidence": confidence_raw,
                "brief_description": brief_desc,
                "extracted_content": extraction,
                "low_confidence": low_confidence,
            },
            lca_relevant=True,  # Let downstream analysis determine relevance
            confidence=confidence_raw / 5.0,
            low_confidence_pages=[1] if low_confidence else [],
            word_count=len(full_markdown.split()),
            warnings=warnings,
        )


class ImageAgent(ImageVLMAgent):
    pass
