"""AWS Textract wrapper for PDF OCR and table extraction."""
import io
from typing import Any, Dict, List, Optional

import boto3

from backend.config import get_settings
from backend.utils.logger import get_logger
from backend.utils.retry import retry_with_backoff

logger = get_logger("textract_client")


def _get_textract_client():
    """Get an AWS Textract client."""
    cfg = get_settings()
    if cfg.MOCK_AWS:
        return None
    return boto3.client(
        "textract",
        region_name=cfg.TEXTRACT_REGION,
        aws_access_key_id=cfg.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=cfg.AWS_SECRET_ACCESS_KEY,
    )


@retry_with_backoff(max_retries=3, initial_delay=2.0)
def detect_document_text(image_bytes: bytes) -> Dict[str, Any]:
    """
    Call Textract DetectDocumentText on an image/page.
    Returns the raw Textract response.
    """
    client = _get_textract_client()
    if client is None:
        return {"Blocks": [], "mock": True}

    response = client.detect_document_text(
        Document={"Bytes": image_bytes}
    )
    return response


@retry_with_backoff(max_retries=3, initial_delay=2.0)
def analyze_document(image_bytes: bytes, features: List[str] = None) -> Dict[str, Any]:
    """
    Call Textract AnalyzeDocument with specified feature types.
    Features: "TABLES", "FORMS"
    """
    client = _get_textract_client()
    if client is None:
        return {"Blocks": [], "mock": True}

    if features is None:
        features = ["TABLES", "FORMS"]

    response = client.analyze_document(
        Document={"Bytes": image_bytes},
        FeatureTypes=features,
    )
    return response


def extract_text_lines(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all LINE blocks from a Textract response with text and bounding box."""
    lines = []
    for block in response.get("Blocks", []):
        if block.get("BlockType") == "LINE":
            bbox = block.get("Geometry", {}).get("BoundingBox", {})
            lines.append({
                "text": block.get("Text", ""),
                "confidence": block.get("Confidence", 0),
                "top": bbox.get("Top", 0),
                "left": bbox.get("Left", 0),
                "width": bbox.get("Width", 0),
                "height": bbox.get("Height", 0),
            })
    # Sort by vertical position (reading order)
    lines.sort(key=lambda x: (x["top"], x["left"]))
    return lines


def extract_tables(response: Dict[str, Any]) -> List[str]:
    """
    Extract TABLE blocks from a Textract response and reconstruct as Markdown tables.
    """
    blocks_by_id = {b["Id"]: b for b in response.get("Blocks", []) if "Id" in b}
    tables_md = []

    for block in response.get("Blocks", []):
        if block.get("BlockType") != "TABLE":
            continue

        # Collect all cells for this table
        cells = []
        for rel in block.get("Relationships", []):
            if rel["Type"] == "CHILD":
                for child_id in rel["Ids"]:
                    child = blocks_by_id.get(child_id, {})
                    if child.get("BlockType") == "CELL":
                        cells.append(child)

        if not cells:
            continue

        # Determine table dimensions
        max_row = max(c.get("RowIndex", 1) for c in cells)
        max_col = max(c.get("ColumnIndex", 1) for c in cells)

        # Build the table grid
        grid = [["" for _ in range(max_col)] for _ in range(max_row)]
        for cell in cells:
            row_idx = cell.get("RowIndex", 1) - 1
            col_idx = cell.get("ColumnIndex", 1) - 1
            # Get cell text from child WORD blocks
            cell_text = _get_cell_text(cell, blocks_by_id)
            if 0 <= row_idx < max_row and 0 <= col_idx < max_col:
                grid[row_idx][col_idx] = cell_text

        # Convert to Markdown
        md_lines = []
        for i, row in enumerate(grid):
            md_lines.append("| " + " | ".join(row) + " |")
            if i == 0:
                md_lines.append("| " + " | ".join(["---"] * len(row)) + " |")

        tables_md.append("\n".join(md_lines))

    return tables_md


def extract_forms(response: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract FORMS (key-value pairs) from a Textract response."""
    blocks_by_id = {b["Id"]: b for b in response.get("Blocks", []) if "Id" in b}
    kv_pairs = []

    for block in response.get("Blocks", []):
        if block.get("BlockType") != "KEY_VALUE_SET":
            continue
        if block.get("EntityTypes", [None])[0] != "KEY":
            continue

        key_text = _get_child_text(block, blocks_by_id)
        value_text = ""

        for rel in block.get("Relationships", []):
            if rel["Type"] == "VALUE":
                for val_id in rel["Ids"]:
                    val_block = blocks_by_id.get(val_id, {})
                    value_text = _get_child_text(val_block, blocks_by_id)

        if key_text:
            kv_pairs.append({"key": key_text.strip(), "value": value_text.strip()})

    return kv_pairs


def _get_cell_text(cell_block: Dict, blocks_by_id: Dict) -> str:
    """Get text content of a cell from its child WORD blocks."""
    words = []
    for rel in cell_block.get("Relationships", []):
        if rel["Type"] == "CHILD":
            for child_id in rel["Ids"]:
                child = blocks_by_id.get(child_id, {})
                if child.get("BlockType") == "WORD":
                    words.append(child.get("Text", ""))
    return " ".join(words)


def _get_child_text(block: Dict, blocks_by_id: Dict) -> str:
    """Get text from child WORD blocks."""
    words = []
    for rel in block.get("Relationships", []):
        if rel["Type"] == "CHILD":
            for child_id in rel["Ids"]:
                child = blocks_by_id.get(child_id, {})
                if child.get("BlockType") == "WORD":
                    words.append(child.get("Text", ""))
    return " ".join(words)


def get_average_confidence(response: Dict[str, Any]) -> float:
    """Compute the average confidence score from all Textract blocks."""
    confidences = [
        b.get("Confidence", 0)
        for b in response.get("Blocks", [])
        if "Confidence" in b
    ]
    if not confidences:
        return 0.0
    return sum(confidences) / len(confidences)
