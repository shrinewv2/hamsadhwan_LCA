"""Structured logging setup for the LCA system."""
import logging
import sys
from typing import Optional

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging with structlog."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if sys.stderr.isatty() else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level, logging.INFO)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "lca") -> structlog.BoundLogger:
    """Get a named structured logger."""
    return structlog.get_logger(name)


# In-memory log buffer for SSE streaming
_log_buffers: dict[str, list[dict]] = {}


def init_job_log_buffer(job_id: str) -> None:
    """Initialize a log buffer for a job."""
    _log_buffers[job_id] = []


def append_job_log(
    job_id: str,
    level: str,
    agent: str,
    file_id_or_message: Optional[str],
    message: Optional[str] = None,
    *,
    file_id: Optional[str] = None,
) -> None:
    """Append a log entry to the job's log buffer.

    Supports both:
    - append_job_log(job_id, level, agent, file_id, message)
    - append_job_log(job_id, level, agent, message)
    """
    from datetime import datetime

    if file_id is not None:
        final_file_id = file_id
        final_message = message if message is not None else (file_id_or_message or "")
    elif message is None:
        final_file_id = None
        final_message = file_id_or_message or ""
    else:
        final_file_id = file_id_or_message
        final_message = message

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "agent": agent,
        "file_id": final_file_id,
        "message": final_message,
    }
    if job_id not in _log_buffers:
        _log_buffers[job_id] = []
    _log_buffers[job_id].append(entry)


def get_job_logs(job_id: str, since_index: int = 0) -> list[dict]:
    """Get log entries for a job since a given index."""
    buffer = _log_buffers.get(job_id, [])
    return buffer[since_index:]


def clear_job_log_buffer(job_id: str) -> None:
    """Clear the log buffer for a job."""
    _log_buffers.pop(job_id, None)
