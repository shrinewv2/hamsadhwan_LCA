"""Large-text chunking utilities for LLM context limits."""
from typing import List


def chunk_text(text: str, max_chunk_size: int = 12000, overlap: int = 500) -> List[str]:
    """
    Split text into chunks that fit within LLM context limits.
    
    Args:
        text: The full text to chunk.
        max_chunk_size: Maximum characters per chunk.
        overlap: Number of overlapping characters between chunks.
    
    Returns:
        List of text chunks.
    """
    if len(text) <= max_chunk_size:
        return [text]

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + max_chunk_size

        # Try to break at a paragraph boundary
        if end < len(text):
            # Look for double newline (paragraph break) near the end of the chunk
            para_break = text.rfind("\n\n", start + max_chunk_size // 2, end)
            if para_break != -1:
                end = para_break + 2
            else:
                # Fall back to single newline
                line_break = text.rfind("\n", start + max_chunk_size // 2, end)
                if line_break != -1:
                    end = line_break + 1
                else:
                    # Fall back to space
                    space = text.rfind(" ", start + max_chunk_size // 2, end)
                    if space != -1:
                        end = space + 1

        chunks.append(text[start:end].strip())
        start = end - overlap if end < len(text) else end

    return [c for c in chunks if c]


def chunk_by_sections(text: str, max_chunk_size: int = 12000) -> List[str]:
    """
    Split text by Markdown heading boundaries, keeping each section under the max size.
    """
    import re
    sections = re.split(r'(?=^#{1,3}\s)', text, flags=re.MULTILINE)
    
    chunks: List[str] = []
    current_chunk = ""

    for section in sections:
        if not section.strip():
            continue
        if len(current_chunk) + len(section) <= max_chunk_size:
            current_chunk += section
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # If a single section exceeds max size, chunk it further
            if len(section) > max_chunk_size:
                chunks.extend(chunk_text(section, max_chunk_size))
                current_chunk = ""
            else:
                current_chunk = section

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
