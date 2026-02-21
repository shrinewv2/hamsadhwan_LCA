"""Claude Vision wrapper using AWS Bedrock for image analysis."""
import base64
import json
from typing import Any, Dict, Optional

import boto3

from backend.config import settings
from backend.utils.logger import get_logger
from backend.utils.retry import retry_with_backoff

logger = get_logger("vlm_client")


def _get_bedrock_client():
    """Get Bedrock Runtime client for vision tasks."""
    if settings and settings.MOCK_AWS:
        return None
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.BEDROCK_REGION if settings else "us-east-1",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID if settings else None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY if settings else None,
    )


def _get_media_type(image_bytes: bytes) -> str:
    """Detect image media type from magic bytes."""
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return "image/png"
    if image_bytes[:2] == b'\xff\xd8':
        return "image/jpeg"
    if image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
        return "image/webp"
    if image_bytes[:4] in (b'II*\x00', b'MM\x00*'):
        return "image/tiff"
    # Default to PNG
    return "image/png"


@retry_with_backoff(max_retries=3, initial_delay=2.0)
def invoke_vision(
    image_bytes: bytes,
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 4096,
    temperature: float = 0.0,
) -> str:
    """
    Send an image to Claude Vision via Bedrock and get a text response.
    
    Args:
        image_bytes: Raw image bytes (PNG, JPEG, WebP, TIFF).
        prompt: User message text to accompany the image.
        system_prompt: Optional system message.
        max_tokens: Maximum response tokens.
        temperature: Sampling temperature.
    
    Returns:
        The model's text response.
    """
    client = _get_bedrock_client()
    if client is None:
        logger.warning("vlm_mock_mode")
        return json.dumps({
            "visual_type": "other",
            "confidence": 3,
            "brief_description": "Mock VLM response",
            "extracted_content": "Mock content from image analysis"
        })

    model_id = settings.BEDROCK_MODEL_VISION if settings else "anthropic.claude-sonnet-4-6"
    media_type = _get_media_type(image_bytes)
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "image": {
                        "format": media_type.split("/")[1],
                        "source": {"bytes": image_bytes},
                    }
                },
                {"text": prompt},
            ],
        }
    ]

    kwargs: Dict[str, Any] = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
    }
    if system_prompt:
        kwargs["system"] = [{"text": system_prompt}]

    response = client.converse(**kwargs)
    output = response.get("output", {})
    message = output.get("message", {})
    content_blocks = message.get("content", [])

    result = ""
    for block in content_blocks:
        if "text" in block:
            result += block["text"]

    return result


def classify_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Pass 1 — Visual classification of an image.
    Returns: {"visual_type": str, "confidence": int (1-5), "brief_description": str}
    """
    system_prompt = (
        "You are an LCA (Life Cycle Assessment) document analyst specialising in visual content extraction. "
        "Classify the type of visual content in this image."
    )
    user_prompt = (
        "Identify which of these types best describes the image:\n"
        "- bar_chart — bar, column, or stacked chart\n"
        "- pie_chart — pie or donut chart\n"
        "- line_chart — line or area chart\n"
        "- table_screenshot — a photograph or screenshot of a table\n"
        "- system_boundary_diagram — boxes and arrows showing a product system\n"
        "- process_flowchart — flowchart with decision nodes\n"
        "- mind_map — radial or hierarchical mind map\n"
        "- equation — mathematical formula or calculation\n"
        "- photograph — real-world photograph of a product, facility, or material\n"
        "- mixed — combination of the above\n"
        "- other — none of the above\n\n"
        "Return your answer as a JSON object with keys: visual_type, confidence (1-5), brief_description.\n"
        "Return ONLY the JSON object, no explanation."
    )

    response = invoke_vision(image_bytes, user_prompt, system_prompt)
    try:
        from backend.processing.bedrock_client import parse_json_response
        return parse_json_response(response)
    except (json.JSONDecodeError, Exception):
        return {"visual_type": "other", "confidence": 1, "brief_description": response[:200]}


def extract_from_image(image_bytes: bytes, visual_type: str) -> str:
    """
    Pass 2 — Type-specific extraction from an image.
    Returns Markdown-formatted extracted content.
    """
    system_prompt = (
        "You are an LCA (Life Cycle Assessment) document analyst. "
        "Extract all relevant data from this image in Markdown format."
    )

    type_prompts = {
        "bar_chart": (
            "Extract every visible data label, axis label, legend entry, title, unit, and numeric value from this chart. "
            "Present the data as a Markdown table where rows are categories and columns are series."
        ),
        "pie_chart": (
            "Extract every visible data label, legend entry, title, unit, percentage, and numeric value from this pie/donut chart. "
            "Present the data as a Markdown table where rows are categories with their values and percentages."
        ),
        "line_chart": (
            "Extract every visible data label, axis label, legend entry, title, unit, and numeric value from this line/area chart. "
            "Present the data as a Markdown table where rows are data points and columns are series."
        ),
        "table_screenshot": (
            "Reconstruct this table exactly as a Markdown table, preserving all column headers, row labels, and cell values. "
            "Preserve units in the header row."
        ),
        "system_boundary_diagram": (
            "List every box/node, every arrow and its direction, every label on arrows, and every boundary line. "
            "Format as a structured description with sub-sections for Inputs, Processes, Outputs, and System Boundary."
        ),
        "process_flowchart": (
            "List every box/node, every arrow and its direction, every label on arrows, and every boundary line. "
            "Format as a structured description with sub-sections for Inputs, Processes, Outputs, and System Boundary."
        ),
        "mind_map": (
            "Reconstruct the mind map as a nested Markdown list, preserving the hierarchy from the central node outward."
        ),
        "equation": (
            "Transcribe the equation in both LaTeX syntax and plain English prose."
        ),
        "photograph": (
            "Describe what is shown and identify any LCA-relevant context (materials, processes, transportation, "
            "energy sources visible)."
        ),
    }

    prompt = type_prompts.get(visual_type, (
        "Describe all visible content section by section, presenting any data as Markdown tables "
        "and any hierarchies as nested lists."
    ))

    return invoke_vision(image_bytes, prompt, system_prompt)
