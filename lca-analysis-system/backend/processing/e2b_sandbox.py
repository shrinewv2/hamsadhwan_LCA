"""E2B Code Interpreter sandbox wrapper for safe code execution."""
import json
from typing import Any, Dict, Optional, Tuple

from backend.config import settings
from backend.utils.logger import get_logger
from backend.utils.retry import retry_with_backoff

logger = get_logger("e2b_sandbox")


@retry_with_backoff(max_retries=2, initial_delay=2.0)
def execute_code_in_sandbox(
    code: str,
    files_to_upload: Optional[Dict[str, bytes]] = None,
    timeout_seconds: Optional[int] = None,
) -> Tuple[int, str, str]:
    """
    Execute Python code in an E2B sandbox.
    
    Args:
        code: Python code string to execute.
        files_to_upload: Dict of {path_in_sandbox: file_bytes} to upload before execution.
        timeout_seconds: Override default timeout.
    
    Returns:
        Tuple of (exit_code, stdout, stderr).
    """
    timeout = timeout_seconds or (settings.SANDBOX_TIMEOUT_SECONDS if settings else 120)

    try:
        from e2b_code_interpreter import Sandbox

        api_key = settings.E2B_API_KEY if settings else ""
        if not api_key:
            logger.warning("e2b_no_api_key", detail="E2B API key not configured")
            return -1, "", "E2B API key not configured"

        sbx = Sandbox(api_key=api_key, timeout=timeout)

        try:
            # Upload files if provided
            if files_to_upload:
                for path, data in files_to_upload.items():
                    sbx.files.write(path, data)
                    logger.info("e2b_file_uploaded", path=path, size=len(data))

            # Execute code
            execution = sbx.run_code(code)

            # Collect output
            stdout = ""
            stderr = ""

            for log in execution.logs.stdout:
                stdout += log + "\n"
            for log in execution.logs.stderr:
                stderr += log + "\n"

            if execution.error:
                return 1, stdout.strip(), f"{execution.error.name}: {execution.error.value}\n{execution.error.traceback}"

            return 0, stdout.strip(), stderr.strip()

        finally:
            sbx.kill()

    except ImportError:
        logger.warning("e2b_not_installed", detail="e2b-code-interpreter not installed")
        return -1, "", "e2b-code-interpreter not installed"
    except Exception as e:
        logger.error("e2b_execution_failed", error=str(e))
        raise


def execute_excel_analysis(file_bytes: bytes, code: str, filename: str = "input_file") -> Tuple[int, str, str]:
    """
    Execute Excel analysis code in sandbox with the file pre-uploaded.
    """
    return execute_code_in_sandbox(
        code=code,
        files_to_upload={f"/home/user/{filename}": file_bytes},
    )
