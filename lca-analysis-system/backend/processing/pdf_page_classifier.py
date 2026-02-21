"""Per-page pymupdf classification logic for PDF pages."""
from typing import Dict, List, Any

from backend.utils.logger import get_logger

logger = get_logger("pdf_page_classifier")

# Page type constants
TEXT_HEAVY = "text_heavy"
TABLE_HEAVY = "table_heavy"
IMAGE_HEAVY = "image_heavy"
MIXED = "mixed"


def classify_page(page) -> Dict[str, Any]:
    """
    Classify a single pymupdf page into one of four types.
    
    Args:
        page: A pymupdf (fitz) page object.
    
    Returns:
        Dict with keys: type, text_length, image_count, has_table_heuristic
    """
    text = page.get_text()
    text_length = len(text.strip())

    images = page.get_images(full=True)
    image_count = len(images)

    # Table heuristic: check for grid-like line patterns
    has_table_heuristic = False
    try:
        drawings = page.get_drawings()
        h_lines = 0
        v_lines = 0
        for d in drawings:
            for item in d.get("items", []):
                if len(item) >= 3 and item[0] == "l":
                    p1, p2 = item[1], item[2]
                    if abs(p1.y - p2.y) < 2:
                        h_lines += 1
                    if abs(p1.x - p2.x) < 2:
                        v_lines += 1
        has_table_heuristic = h_lines > 5 and v_lines > 5
    except Exception:
        pass

    # Classification logic
    if has_table_heuristic:
        page_type = TABLE_HEAVY
    elif text_length > 500 and image_count == 0:
        page_type = TEXT_HEAVY
    elif image_count > 0 and text_length < 200:
        page_type = IMAGE_HEAVY
    else:
        page_type = MIXED

    return {
        "type": page_type,
        "text_length": text_length,
        "image_count": image_count,
        "has_table_heuristic": has_table_heuristic,
    }


def classify_all_pages(doc) -> List[Dict[str, Any]]:
    """
    Classify all pages in a pymupdf document.
    
    Args:
        doc: A pymupdf (fitz) Document object.
    
    Returns:
        List of classification dicts, one per page.
    """
    results = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        classification = classify_page(page)
        classification["page_number"] = page_num + 1
        results.append(classification)
    return results
