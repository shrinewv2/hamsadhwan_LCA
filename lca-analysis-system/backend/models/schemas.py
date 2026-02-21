"""All Pydantic models (request/response/internal) for the LCA system."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import AgentType, FileStatus, FileType, ValidationStatus


# ──────────────────────────────────────────────────
#  Internal / DynamoDB models
# ──────────────────────────────────────────────────

class FileMetadata(BaseModel):
    file_id: str
    job_id: str
    original_name: str
    s3_key: str
    actual_mime: str
    file_type: FileType
    size_bytes: int
    is_scanned: bool = False
    has_text_layer: bool = False
    has_embedded_images: bool = False
    page_count: Optional[int] = None
    sheet_count: Optional[int] = None
    complexity_score: float = 0.0
    status: FileStatus = FileStatus.PENDING
    upload_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_assigned: Optional[str] = None


class ParsedOutput(BaseModel):
    file_id: str
    job_id: str
    agent: str
    markdown: str
    structured_json: Dict[str, Any] = Field(default_factory=dict)
    lca_relevant: bool = False
    confidence: float = 0.0
    low_confidence_pages: List[int] = Field(default_factory=list)
    word_count: int = 0
    processing_time_s: float = 0.0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ValidationReport(BaseModel):
    file_id: str
    status: ValidationStatus = ValidationStatus.PASSED
    rule_errors: List[str] = Field(default_factory=list)
    rule_warnings: List[str] = Field(default_factory=list)
    taxonomy_issues: List[str] = Field(default_factory=list)
    cross_doc_conflicts: List[str] = Field(default_factory=list)
    plausibility_flags: List[str] = Field(default_factory=list)
    data_quality_rating: str = "Fair"
    llm_confidence_score: float = 0.0


class ErrorRecord(BaseModel):
    file_id: Optional[str] = None
    agent: Optional[str] = None
    stage: str = ""
    message: str = ""
    traceback: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class FinalOutput(BaseModel):
    markdown_report: str = ""
    structured_json: Dict[str, Any] = Field(default_factory=dict)
    viz_data: Dict[str, Any] = Field(default_factory=dict)
    per_doc_summaries: List[Dict[str, Any]] = Field(default_factory=list)
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)


# ──────────────────────────────────────────────────
#  API Request / Response models
# ──────────────────────────────────────────────────

class JobCreateResponse(BaseModel):
    job_id: str
    file_count: int
    estimated_seconds: int
    status: str = "PENDING"


class FileRecord(BaseModel):
    file_id: str
    name: str
    type: str
    agent: Optional[str] = None
    status: str
    confidence: Optional[float] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float = 0.0
    files: List[FileRecord] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class ReportResponse(BaseModel):
    markdown_report: str
    structured_json: Dict[str, Any]
    viz_data: Dict[str, Any]
    validation_summary: Dict[str, Any]
    audit_summary: Dict[str, Any]


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str = "ok"
    bedrock: str = "connected"
    s3: str = "connected"
    dynamo: str = "connected"


class LogEntry(BaseModel):
    timestamp: str
    level: str = "INFO"
    agent: str = ""
    file_id: Optional[str] = None
    message: str = ""


# ──────────────────────────────────────────────────
#  Analysis-level DynamoDB record
# ──────────────────────────────────────────────────

class AnalysisRecord(BaseModel):
    job_id: str
    status: str = "PENDING"
    file_ids: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    report_s3_key: Optional[str] = None
    json_s3_key: Optional[str] = None
    viz_s3_key: Optional[str] = None
    audit_s3_key: Optional[str] = None
    user_context: Dict[str, Any] = Field(default_factory=dict)
    total_processing_time_s: Optional[float] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)
