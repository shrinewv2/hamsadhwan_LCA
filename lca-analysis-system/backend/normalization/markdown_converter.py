"""Table/chart/list to Markdown conversion helpers."""
import re
from typing import List


def ensure_table_separator(markdown: str) -> str:
    """
    Ensure every Markdown table has a proper separator row.
    If a table starts with a header row (| ... |) but the next line
    isn't a separator (| --- | --- |), insert one.
    """
    lines = markdown.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        result.append(line)

        # Check if this looks like a table row
        if re.match(r"^\|.*\|$", line.strip()):
            # Check next line
            next_i = i + 1
            if next_i < len(lines):
                next_line = lines[next_i].strip()
                # If next line is also a table row but not a separator
                if re.match(r"^\|.*\|$", next_line) and not re.match(r"^\|[\s\-:|]+\|$", next_line):
                    # Count columns
                    cols = line.count("|") - 1
                    if cols > 0:
                        sep = "| " + " | ".join(["---"] * cols) + " |"
                        # Only insert separator if we're at the first row of the table
                        # (check that the previous line wasn't also a table row)
                        if i == 0 or not re.match(r"^\|.*\|$", lines[i - 1].strip()):
                            result.append(sep)
        i += 1
    return "\n".join(result)


def deduplicate_consecutive_lines(text: str) -> str:
    """Remove identical consecutive lines (artifact from some Textract responses)."""
    lines = text.split("\n")
    result = []
    prev = None
    for line in lines:
        if line != prev:
            result.append(line)
        prev = line
    return "\n".join(result)


def list_to_markdown(items: list, indent: int = 0) -> str:
    """Convert a list of items to a Markdown list."""
    prefix = "  " * indent
    return "\n".join(f"{prefix}- {item}" for item in items)


def dict_to_markdown_table(data: dict) -> str:
    """Convert a dict to a Markdown two-column table."""
    lines = ["| Key | Value |", "| --- | --- |"]
    for k, v in data.items():
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines)


def rows_to_markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    """Convert headers + rows to a Markdown table."""
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        padded = row + [""] * (len(headers) - len(row))
        lines.append("| " + " | ".join(padded[:len(headers)]) + " |")
    return "\n".join(lines)
