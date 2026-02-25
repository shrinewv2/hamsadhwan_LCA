"""Local Python sandbox for safe code execution using subprocess."""
import io
import json
import os
import sys
import tempfile
import subprocess
from typing import Any, Dict, Optional, Tuple

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger("local_sandbox")

# Allowed modules for sandbox execution
ALLOWED_MODULES = {
    "pandas", "numpy", "json", "sys", "io", "csv", "re",
    "math", "statistics", "collections", "itertools", "functools",
    "datetime", "decimal", "fractions", "openpyxl", "xlrd",
}


def execute_code_in_sandbox(
    code: str,
    files_to_upload: Optional[Dict[str, bytes]] = None,
    timeout_seconds: Optional[int] = None,
) -> Tuple[int, str, str]:
    """
    Execute Python code in a local subprocess sandbox.

    Args:
        code: Python code string to execute.
        files_to_upload: Dict of {path_in_sandbox: file_bytes} to write before execution.
        timeout_seconds: Override default timeout.

    Returns:
        Tuple of (exit_code, stdout, stderr).
    """
    cfg = get_settings()
    timeout = timeout_seconds or cfg.SANDBOX_TIMEOUT_SECONDS

    # In mock mode, return a mock result
    if cfg.MOCK_AWS:
        logger.info("sandbox_mock_mode", detail="Returning mock sandbox result")
        return 0, json.dumps({"sheets": [], "data_found": False, "errors": []}), ""

    temp_dir = None
    try:
        # Create a temporary directory for sandbox execution
        temp_dir = tempfile.mkdtemp(prefix="sandbox_")

        # Write uploaded files to temp directory
        file_mappings = {}
        if files_to_upload:
            for virtual_path, data in files_to_upload.items():
                # Map virtual paths like /home/user/input_file to temp dir
                filename = os.path.basename(virtual_path)
                real_path = os.path.join(temp_dir, filename)
                with open(real_path, "wb") as f:
                    f.write(data)
                file_mappings[virtual_path] = real_path
                logger.info("sandbox_file_written", path=real_path, size=len(data))

        # Replace virtual paths in code with real paths
        modified_code = code
        for virtual_path, real_path in file_mappings.items():
            # Normalize path separators for the current OS
            real_path_escaped = real_path.replace("\\", "\\\\")
            modified_code = modified_code.replace(virtual_path, real_path_escaped)

        # Write the code to a temp file
        code_path = os.path.join(temp_dir, "sandbox_script.py")
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(modified_code)

        # Execute in subprocess
        result = subprocess.run(
            [sys.executable, code_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=temp_dir,
            env={
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONUNBUFFERED": "1",
            },
        )

        logger.info(
            "sandbox_execution_complete",
            exit_code=result.returncode,
            stdout_len=len(result.stdout),
            stderr_len=len(result.stderr),
        )

        return result.returncode, result.stdout.strip(), result.stderr.strip()

    except subprocess.TimeoutExpired:
        logger.warning("sandbox_timeout", timeout=timeout)
        return 1, "", f"Execution timed out after {timeout} seconds"
    except Exception as e:
        logger.error("sandbox_execution_failed", error=str(e))
        return 1, "", str(e)
    finally:
        # Clean up temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass


def execute_excel_analysis(
    file_bytes: bytes,
    code: str,
    filename: str = "input_file"
) -> Tuple[int, str, str]:
    """
    Execute Excel analysis code in sandbox with the file pre-uploaded.
    """
    return execute_code_in_sandbox(
        code=code,
        files_to_upload={f"/home/user/{filename}": file_bytes},
    )


def execute_dataframe_analysis(
    file_bytes: bytes,
    file_extension: str = "xlsx",
) -> Tuple[int, str, str]:
    """
    Execute a standard dataframe analysis on the given file.
    Returns JSON with sheets data.
    """
    code = f'''
import pandas as pd
import json
import sys

try:
    file_path = "/home/user/input_file.{file_extension}"

    if "{file_extension}" == "csv":
        sheets_data = {{"Sheet1": pd.read_csv(file_path)}}
    else:
        sheets_data = pd.read_excel(file_path, sheet_name=None)

    result = {{"sheets": [], "data_found": False, "errors": []}}

    for name, df in sheets_data.items():
        if df.empty:
            continue

        try:
            md = df.to_markdown(index=False)
        except Exception:
            md = df.to_string()

        result["sheets"].append({{
            "name": str(name),
            "markdown": md,
            "columns": list(df.columns.astype(str)),
            "row_count": len(df),
        }})
        result["data_found"] = True

    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{"sheets": [], "data_found": False, "errors": [str(e)]}}))
'''

    return execute_code_in_sandbox(
        code=code,
        files_to_upload={f"/home/user/input_file.{file_extension}": file_bytes},
    )
