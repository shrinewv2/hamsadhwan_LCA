"""LLM text wrapper using AWS Bedrock (supports Claude, Llama, Pixtral, etc.)."""
import json
from typing import Any, Dict, List, Optional

import boto3

from backend.config import get_settings
from backend.utils.logger import get_logger
from backend.utils.retry import retry_with_backoff

logger = get_logger("bedrock_client")


def _get_bedrock_client():
    """Get the Bedrock Runtime client."""
    cfg = get_settings()
    if cfg.MOCK_AWS:
        return None
    return boto3.client(
        "bedrock-runtime",
        region_name=cfg.BEDROCK_REGION,
        aws_access_key_id=cfg.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=cfg.AWS_SECRET_ACCESS_KEY,
    )


@retry_with_backoff(max_retries=3, initial_delay=2.0)
def invoke_claude(
    prompt: str,
    system_prompt: str = "",
    model: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.0,
) -> str:
    """
    Invoke Claude via Bedrock Converse API.
    
    Args:
        prompt: User message text.
        system_prompt: System message text.
        model: Model ID. Defaults to Sonnet.
        max_tokens: Maximum response tokens.
        temperature: Sampling temperature.
    
    Returns:
        The model's text response.
    """
    client = _get_bedrock_client()
    cfg = get_settings()
    if client is None:
        logger.warning("bedrock_mock_mode", detail="Returning mock response")
        return '{"mock": true, "message": "Bedrock is in mock mode"}'

    model_id = model or cfg.BEDROCK_MODEL_SONNET

    messages = [
        {"role": "user", "content": [{"text": prompt}]}
    ]

    kwargs: Dict[str, Any] = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": {
            "maxTokens": max_tokens,
            "temperature": temperature,
        },
    }

    if system_prompt:
        kwargs["system"] = [{"text": system_prompt}]

    response = client.converse(**kwargs)
    output = response.get("output", {})
    message = output.get("message", {})
    content_blocks = message.get("content", [])

    result_text = ""
    for block in content_blocks:
        if "text" in block:
            result_text += block["text"]

    return result_text


async def invoke_claude_sonnet(
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 4096,
    **kwargs: Any,
) -> str:
    """Invoke primary model (Sonnet/Llama) for routing, validation, synthesis tasks.

    Supports both `system_prompt=` and legacy `system=` keyword usage.
    """
    if kwargs.get("system") and not system_prompt:
        system_prompt = kwargs["system"]

    cfg = get_settings()
    model = cfg.BEDROCK_MODEL_SONNET
    return invoke_claude(prompt, system_prompt, model=model, max_tokens=max_tokens)


def invoke_claude_haiku(prompt: str, system_prompt: str = "", max_tokens: int = 4096) -> str:
    """Invoke fast model (Haiku/Scout) for code gen, per-doc summaries."""
    cfg = get_settings()
    model = cfg.BEDROCK_MODEL_HAIKU
    return invoke_claude(prompt, system_prompt, model=model, max_tokens=max_tokens)


def parse_json_response(response: str) -> Dict[str, Any]:
    """Parse a JSON response from Claude, handling markdown code fences."""
    text = response.strip()
    # Remove markdown code fences if present
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return json.loads(text)
