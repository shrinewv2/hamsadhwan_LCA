"""
Configuration module — loads and validates all environment variables.
The application refuses to start if required variables are missing.
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All environment configuration for the LCA Multi-Agent System."""

    # AWS Core
    AWS_REGION: str = Field(default="us-east-1")
    AWS_ACCESS_KEY_ID: str = Field(...)
    AWS_SECRET_ACCESS_KEY: str = Field(...)

    # AWS Bedrock (LLM + Vision)
    BEDROCK_REGION: str = Field(default="us-east-1")
    BEDROCK_MODEL_SONNET: str = Field(default="anthropic.claude-sonnet-4-6")
    BEDROCK_MODEL_HAIKU: str = Field(default="anthropic.claude-haiku-4-5-20251001")
    BEDROCK_MODEL_VISION: str = Field(default="anthropic.claude-sonnet-4-6")

    # AWS Textract
    TEXTRACT_REGION: str = Field(default="us-east-1")

    # E2B (Code Sandbox)
    E2B_API_KEY: str = Field(...)

    # AWS S3 Buckets
    S3_BUCKET_UPLOADS: str = Field(default="lca-uploads")
    S3_BUCKET_PARSED: str = Field(default="lca-parsed")
    S3_BUCKET_REPORTS: str = Field(default="lca-reports")
    S3_BUCKET_AUDIT: str = Field(default="lca-audit-logs")
    S3_BUCKET_TEMP: str = Field(default="lca-temp")

    # AWS DynamoDB Tables
    DYNAMO_TABLE_FILES: str = Field(default="lca-files")
    DYNAMO_TABLE_ANALYSES: str = Field(default="lca-analyses")

    # AWS OpenSearch
    OPENSEARCH_ENDPOINT: str = Field(default="")
    OPENSEARCH_INDEX: str = Field(default="lca-documents")

    # Application
    MAX_FILE_SIZE_MB: int = Field(default=100)
    MAX_FILES_PER_JOB: int = Field(default=20)
    SANDBOX_TIMEOUT_SECONDS: int = Field(default=120)
    VLM_MIN_CONFIDENCE: int = Field(default=3)
    LOG_LEVEL: str = Field(default="INFO")

    # Optional Variables
    VIRUS_SCAN_ENABLED: bool = Field(default=True)
    MOCK_AWS: bool = Field(default=False)
    CORS_ORIGINS: str = Field(default="http://localhost:5173")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def get_settings() -> Settings:
    """Load and validate settings. Raises ValidationError if required vars are missing."""
    return Settings()


# Singleton — imported by other modules
settings: Optional[Settings] = None


def init_settings() -> Settings:
    """Initialize settings singleton. Call once at startup."""
    global settings
    settings = get_settings()
    return settings
