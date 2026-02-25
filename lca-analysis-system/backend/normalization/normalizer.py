"""Normalizer — converts all agent outputs to the unified ParsedOutput schema."""
from typing import List

from backend.config import get_settings
from backend.models.schemas import ParsedOutput
from backend.normalization.markdown_converter import (
    deduplicate_consecutive_lines,
    ensure_table_separator,
)
from backend.storage import s3_client
from backend.storage import dynamo_client
from backend.utils.logger import append_job_log, get_logger

logger = get_logger("normalizer")


def normalize_output(output: ParsedOutput) -> ParsedOutput:
    """
    Apply normalization steps to a ParsedOutput:
    1. Trim markdown whitespace
    2. Ensure table separator rows
    3. Deduplicate consecutive lines
    4. Count words
    5. Cap confidence at 1.0
    6. Store to S3
    7. Update DynamoDB
    """
    # Step 1: Trim whitespace
    output.markdown = output.markdown.strip()

    # Step 2: Ensure table separator rows
    output.markdown = ensure_table_separator(output.markdown)

    # Step 3: Deduplicate consecutive lines
    output.markdown = deduplicate_consecutive_lines(output.markdown)

    # Step 4: Word count
    output.word_count = len(output.markdown.split())

    # Step 5: Cap confidence
    output.confidence = min(output.confidence, 1.0)

    # Step 6: Store to S3
    try:
        cfg = get_settings()
        bucket = cfg.S3_BUCKET_PARSED
        md_key = f"parsed/{output.job_id}/{output.file_id}/content.md"
        s3_client.upload_text(bucket, md_key, output.markdown)

        json_key = f"parsed/{output.job_id}/{output.file_id}/metadata.json"
        s3_client.upload_json(bucket, json_key, output.model_dump())

        append_job_log(
            output.job_id, "INFO", "normalizer", output.file_id,
            f"Stored normalized output to S3 ({output.word_count} words)"
        )
    except Exception as e:
        logger.warning("s3_store_failed", error=str(e))

    # Step 7: Update DynamoDB
    try:
        dynamo_client.update_file_status(
            output.file_id, "COMPLETED",
            extra_attrs={
                "parsed_md_key": f"parsed/{output.job_id}/{output.file_id}/content.md",
                "parsed_json_key": f"parsed/{output.job_id}/{output.file_id}/metadata.json",
                "confidence": output.confidence,
                "word_count": output.word_count,
            }
        )
    except Exception as e:
        logger.warning("dynamo_update_failed", error=str(e))

    return output


def normalize_all(outputs: List[ParsedOutput]) -> List[ParsedOutput]:
    """Normalize a list of ParsedOutputs."""
    normalized = []
    for out in outputs:
        parsed_out = out if isinstance(out, ParsedOutput) else ParsedOutput.model_validate(out)
        try:
            normalized.append(normalize_output(parsed_out))
        except Exception as e:
            logger.error("normalization_failed", file_id=parsed_out.file_id, error=str(e))
            parsed_out.errors.append(f"Normalization error: {str(e)}")
            normalized.append(parsed_out)
    return normalized
