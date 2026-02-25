"""Generic Agent — handles DOCX, TXT, RTF, PPTX, ODT via pandoc + unstructured."""
import json
import os
import subprocess
import tempfile
from typing import Any, Dict, List

from backend.agents.base_agent import BaseAgent
from backend.models.schemas import FileMetadata, ParsedOutput
from backend.models.enums import FileType
from backend.processing.bedrock_client import invoke_claude_haiku, parse_json_response
from backend.utils.logger import append_job_log, get_logger

logger = get_logger("generic_agent")

# Map file extensions to pandoc input formats
PANDOC_FORMAT_MAP = {
    "docx": "docx",
    "doc": "docx",
    "txt": "plain",
    "rtf": "rtf",
    "pptx": "pptx",
    "odt": "odt",
    "csv": "csv",
}


class GenericAgent(BaseAgent):
    agent_name = "generic_agent"

    def process(self, file_meta: FileMetadata, file_bytes: bytes) -> ParsedOutput:
        ext = file_meta.original_name.rsplit(".", 1)[-1].lower() if "." in file_meta.original_name else ""

        # Try pandoc first
        markdown = self._convert_with_pandoc(file_bytes, ext, file_meta)

        if not markdown:
            # Fallback: try unstructured library
            append_job_log(
                file_meta.job_id, "INFO", self.agent_name, file_meta.file_id,
                "Pandoc failed or unavailable, trying unstructured library"
            )
            markdown = self._convert_with_unstructured(file_bytes, file_meta)

        if not markdown:
            markdown = f"# Unable to extract content from {file_meta.original_name}"

        # Section Detection via LLM
        key_sections = []
        structured = {"sections": [], "key_sections": []}

        if len(markdown) > 50:
            key_sections, all_sections = self._detect_key_sections(markdown, file_meta)
            structured["sections"] = all_sections
            structured["key_sections"] = key_sections

            # Build primary markdown from high-relevance sections
            if key_sections:
                primary_md = "\n\n".join([
                    f"## {s['section_title']}\n\n{s['content']}"
                    for s in key_sections
                ])
                markdown = f"# Key Content from {file_meta.original_name}\n\n{primary_md}\n\n---\n\n# Full Document Content\n\n{markdown}"

        return ParsedOutput(
            file_id=file_meta.file_id,
            job_id=file_meta.job_id,
            agent=self.agent_name,
            markdown=markdown,
            structured_json=structured,
            lca_relevant=True,  # Let downstream analysis determine relevance
            confidence=0.75 if markdown else 0.1,
            word_count=len(markdown.split()),
        )

    def _convert_with_pandoc(self, file_bytes: bytes, ext: str, file_meta: FileMetadata) -> str:
        """Convert file to Markdown using system pandoc binary."""
        input_format = PANDOC_FORMAT_MAP.get(ext, ext)
        if not input_format:
            return ""

        try:
            with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp_in:
                tmp_in.write(file_bytes)
                tmp_in_path = tmp_in.name

            tmp_out_path = tmp_in_path + ".md"

            result = subprocess.run(
                ["pandoc", "-f", input_format, "-t", "markdown", "--wrap=none", tmp_in_path, "-o", tmp_out_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0 and os.path.exists(tmp_out_path):
                with open(tmp_out_path, "r", encoding="utf-8") as f:
                    markdown = f.read()
                append_job_log(
                    file_meta.job_id, "INFO", self.agent_name, file_meta.file_id,
                    f"Pandoc conversion successful ({len(markdown)} chars)"
                )
                return markdown
            else:
                logger.warning("pandoc_failed", stderr=result.stderr[:500])
                return ""

        except FileNotFoundError:
            logger.info("pandoc_not_installed")
            return ""
        except subprocess.TimeoutExpired:
            logger.warning("pandoc_timeout")
            return ""
        except Exception as e:
            logger.warning("pandoc_error", error=str(e))
            return ""
        finally:
            try:
                os.unlink(tmp_in_path)
                if os.path.exists(tmp_out_path):
                    os.unlink(tmp_out_path)
            except Exception:
                pass

    def _convert_with_unstructured(self, file_bytes: bytes, file_meta: FileMetadata) -> str:
        """Convert file to Markdown using the unstructured library."""
        import sys

        # Skip unstructured on Windows due to import performance issues
        if sys.platform == "win32":
            logger.info("unstructured_skipped_on_windows")
            # For txt files, just decode the content directly
            ext = file_meta.original_name.rsplit(".", 1)[-1].lower() if "." in file_meta.original_name else ""
            if ext in ("txt", "text"):
                try:
                    return file_bytes.decode("utf-8", errors="replace")
                except Exception:
                    return file_bytes.decode("latin-1", errors="replace")
            return ""

        try:
            from unstructured.partition.auto import partition

            with tempfile.NamedTemporaryFile(
                suffix=f".{file_meta.original_name.rsplit('.', 1)[-1]}", delete=False
            ) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                elements = partition(filename=tmp_path)
                md_parts = []
                for elem in elements:
                    elem_type = type(elem).__name__
                    text = str(elem)
                    if "Title" in elem_type:
                        md_parts.append(f"## {text}")
                    elif "Table" in elem_type:
                        md_parts.append(f"\n{text}\n")
                    elif "Image" in elem_type:
                        md_parts.append(f"[Image: embedded image]")
                    else:
                        md_parts.append(text)

                markdown = "\n\n".join(md_parts)
                append_job_log(
                    file_meta.job_id, "INFO", self.agent_name, file_meta.file_id,
                    f"Unstructured conversion successful ({len(markdown)} chars)"
                )
                return markdown
            finally:
                os.unlink(tmp_path)

        except ImportError:
            logger.info("unstructured_not_installed")
            return ""
        except Exception as e:
            logger.warning("unstructured_error", error=str(e))
            return ""

    def _detect_key_sections(self, markdown: str, file_meta: FileMetadata) -> tuple:
        """Use LLM to detect key sections in the document."""
        try:
            # Truncate if too long
            text = markdown[:8000] if len(markdown) > 8000 else markdown

            prompt = (
                "Identify and extract the most important sections from this document. "
                "Return a JSON array of objects with keys: section_title, content (brief excerpt), "
                "relevance_score (0-10). Only include sections with relevance >= 5.\n\n"
                f"Document:\n{text}"
            )
            system = "You are a document analyst. Return ONLY a JSON array, no explanation."
            response = invoke_claude_haiku(prompt, system, max_tokens=2048)

            sections = parse_json_response(response)
            if not isinstance(sections, list):
                sections = sections.get("sections", [])

            key_sections = [s for s in sections if s.get("relevance_score", 0) >= 5]
            return key_sections, sections

        except Exception as e:
            logger.warning("section_detection_failed", error=str(e))
            return [], []
