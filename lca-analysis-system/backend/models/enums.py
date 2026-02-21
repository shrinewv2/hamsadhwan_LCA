"""Enums used across the LCA Multi-Agent system."""
from enum import Enum


class FileType(str, Enum):
    EXCEL = "EXCEL"
    CSV = "CSV"
    PDF = "PDF"
    IMAGE = "IMAGE"
    MINDMAP_XMIND = "MINDMAP_XMIND"
    MINDMAP_FREEMIND = "MINDMAP_FREEMIND"
    DOCX = "DOCX"
    TEXT = "TEXT"
    PPTX = "PPTX"
    UNKNOWN = "UNKNOWN"


class FileStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"


class ValidationStatus(str, Enum):
    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"


class AgentType(str, Enum):
    EXCEL_AGENT = "excel_agent"
    PDF_TEXT_AGENT = "pdf_text_agent"
    PDF_HYBRID_AGENT = "pdf_hybrid_agent"
    PDF_SCANNED_AGENT = "pdf_scanned_agent"
    IMAGE_VLM_AGENT = "image_vlm_agent"
    MINDMAP_AGENT = "mindmap_agent"
    GENERIC_AGENT = "generic_agent"
