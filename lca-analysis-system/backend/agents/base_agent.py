"""Abstract base class all agents inherit."""
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from backend.models.schemas import FileMetadata, ParsedOutput
from backend.utils.logger import append_job_log, get_logger

logger = get_logger("base_agent")


class BaseAgent(ABC):
    """
    Abstract base class for all LCA document processing agents.
    Every agent must implement the `process` method.
    """

    agent_name: str = "base_agent"

    @abstractmethod
    def process(self, file_meta: FileMetadata, file_bytes: bytes) -> ParsedOutput:
        """
        Process a single file and return a ParsedOutput.
        
        Args:
            file_meta: File metadata record.
            file_bytes: Raw file bytes.
        
        Returns:
            ParsedOutput with extracted content.
        """
        ...

    def safe_process(self, file_meta: FileMetadata, file_bytes: bytes) -> ParsedOutput:
        """
        Wrapper that catches exceptions and returns a partial output on failure.
        """
        start_time = time.time()
        append_job_log(
            file_meta.job_id, "INFO", self.agent_name, file_meta.file_id,
            f"Starting processing: {file_meta.original_name}"
        )
        try:
            result = self.process(file_meta, file_bytes)
            result.processing_time_s = time.time() - start_time
            append_job_log(
                file_meta.job_id, "INFO", self.agent_name, file_meta.file_id,
                f"Completed processing in {result.processing_time_s:.1f}s (confidence={result.confidence})"
            )
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"Agent {self.agent_name} failed: {str(e)}"
            logger.error("agent_failed", agent=self.agent_name, file_id=file_meta.file_id, error=str(e))
            append_job_log(
                file_meta.job_id, "ERROR", self.agent_name, file_meta.file_id, error_msg
            )
            return ParsedOutput(
                file_id=file_meta.file_id,
                job_id=file_meta.job_id,
                agent=self.agent_name,
                markdown=f"# Error Processing {file_meta.original_name}\n\n{error_msg}",
                structured_json={"error": str(e)},
                lca_relevant=False,
                confidence=0.0,
                processing_time_s=elapsed,
                errors=[error_msg],
            )
