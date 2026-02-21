"""File complexity scoring (0–1) for processing time estimation."""
from backend.models.enums import FileType
from backend.utils.logger import get_logger

logger = get_logger("complexity_scorer")


def compute_complexity_score(
    file_type: FileType,
    page_count: int = 0,
    has_embedded_images: bool = False,
    is_scanned: bool = False,
    sheet_count: int = 0,
    estimated_row_count: int = 0,
    size_bytes: int = 0,
) -> float:
    """
    Compute a complexity score between 0.0 and 1.0.
    Higher values indicate more complex files requiring longer processing.
    """
    score = 0.0

    if file_type == FileType.PDF:
        score = min(page_count / 200.0, 0.6)
        if has_embedded_images:
            score += 0.2
        if is_scanned:
            score += 0.2

    elif file_type in (FileType.EXCEL, FileType.CSV):
        score = min(sheet_count / 20.0, 0.5)
        score += min(estimated_row_count / 100000.0, 0.5)

    elif file_type == FileType.IMAGE:
        score = 0.4

    elif file_type in (FileType.MINDMAP_XMIND, FileType.MINDMAP_FREEMIND):
        score = 0.3

    elif file_type in (FileType.DOCX, FileType.TEXT, FileType.PPTX):
        score = 0.2

    elif file_type == FileType.UNKNOWN:
        score = 0.5

    # Clamp to [0.0, 1.0]
    score = max(0.0, min(score, 1.0))
    return round(score, 3)


def estimate_processing_seconds(complexity_score: float) -> int:
    """
    Estimate processing time in seconds based on complexity score.
    """
    # Base time + complexity-scaled time
    base_seconds = 10
    max_additional = 180
    return base_seconds + int(complexity_score * max_additional)
