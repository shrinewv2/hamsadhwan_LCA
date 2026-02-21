"""PDF Hybrid Agent — processes PDFs with any mix of text, scanned, tables, images."""
import io
from typing import Any, Dict, List

from backend.agents.base_agent import BaseAgent
from backend.models.schemas import FileMetadata, ParsedOutput
from backend.processing.pdf_page_classifier import (
    IMAGE_HEAVY, MIXED, TABLE_HEAVY, TEXT_HEAVY, classify_all_pages,
)
from backend.processing.textract_client import (
    analyze_document, detect_document_text, extract_forms,
    extract_tables, extract_text_lines, get_average_confidence,
)
from backend.processing.vlm_client import classify_image, extract_from_image
from backend.utils.logger import append_job_log, get_logger

logger = get_logger("pdf_agent")


class PDFHybridAgent(BaseAgent):
    agent_name = "pdf_hybrid_agent"

    def process(self, file_meta: FileMetadata, file_bytes: bytes) -> ParsedOutput:
        import fitz  # pymupdf

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        is_scanned = file_meta.is_scanned

        page_outputs: List[str] = []
        confidences: List[float] = []
        low_confidence_pages: List[int] = []
        warnings: List[str] = []
        errors: List[str] = []

        if is_scanned:
            # Fully scanned PDF: skip classification, process every page
            page_outputs, confidences, low_confidence_pages, warnings = self._process_scanned(
                doc, file_meta
            )
        else:
            # Hybrid: classify and process each page by type
            classifications = classify_all_pages(doc)
            for i, cls in enumerate(classifications):
                page = doc[i]
                page_num = i + 1
                page_type = cls["type"]

                append_job_log(
                    file_meta.job_id, "INFO", self.agent_name, file_meta.file_id,
                    f"Processing page {page_num}/{len(doc)} (type={page_type})"
                )

                try:
                    if page_type == TEXT_HEAVY:
                        md, conf = self._process_text_page(page)
                    elif page_type == TABLE_HEAVY:
                        md, conf = self._process_table_page(page)
                    elif page_type == IMAGE_HEAVY:
                        md, conf = self._process_image_page(page, doc)
                    else:  # MIXED
                        md, conf = self._process_mixed_page(page, doc)

                    page_outputs.append(md)
                    confidences.append(conf)

                    if conf < 0.6:
                        low_confidence_pages.append(page_num)
                        warnings.append(f"Page {page_num}: low confidence ({conf:.2f})")

                except Exception as e:
                    error_msg = f"Page {page_num} processing error: {str(e)}"
                    errors.append(error_msg)
                    page_outputs.append(f"<!-- Error processing page {page_num}: {str(e)} -->")
                    confidences.append(0.0)
                    low_confidence_pages.append(page_num)

        doc.close()

        # Assembly
        full_markdown = "\n\n---\n\n".join(page_outputs)
        avg_confidence = sum(confidences) / max(len(confidences), 1)

        return ParsedOutput(
            file_id=file_meta.file_id,
            job_id=file_meta.job_id,
            agent=self.agent_name,
            markdown=full_markdown,
            structured_json={
                "page_count": len(page_outputs),
                "page_types": [c["type"] if not is_scanned else "scanned" for c in (classify_all_pages(fitz.open(stream=file_bytes, filetype="pdf")) if not is_scanned else [{"type": "scanned"}] * len(page_outputs))],
            },
            lca_relevant=True,
            confidence=round(min(avg_confidence, 1.0), 3),
            low_confidence_pages=low_confidence_pages,
            word_count=len(full_markdown.split()),
            errors=errors,
            warnings=warnings,
        )

    def _process_scanned(self, doc, file_meta) -> tuple:
        """Process a fully scanned PDF."""
        import fitz
        page_outputs = []
        confidences = []
        low_confidence_pages = []
        warnings = []

        for i in range(len(doc)):
            page = doc[i]
            page_num = i + 1

            append_job_log(
                file_meta.job_id, "INFO", self.agent_name, file_meta.file_id,
                f"Processing scanned page {page_num}/{len(doc)}"
            )

            # Render to PNG at 200 DPI
            pix = page.get_pixmap(dpi=200)
            png_bytes = pix.tobytes("png")

            # Textract analysis
            try:
                textract_resp = analyze_document(png_bytes, features=["TABLES"])
                lines = extract_text_lines(textract_resp)
                text = "\n".join([l["text"] for l in lines])
                tables = extract_tables(textract_resp)
                textract_conf = get_average_confidence(textract_resp) / 100.0
            except Exception as e:
                text = ""
                tables = []
                textract_conf = 0.0
                warnings.append(f"Page {page_num}: Textract failed: {str(e)}")

            # VLM holistic description
            try:
                vlm_desc = extract_from_image(png_bytes, "other")
                vlm_conf = 0.7
            except Exception as e:
                vlm_desc = ""
                vlm_conf = 0.0

            # Combine outputs
            parts = [f"### Page {page_num}\n"]
            if text:
                parts.append(text)
            if tables:
                for t in tables:
                    parts.append(f"\n{t}\n")
            if vlm_desc:
                parts.append(f"\n*VLM Description:* {vlm_desc}")

            md = "\n".join(parts)
            conf = (textract_conf + vlm_conf) / 2
            page_outputs.append(md)
            confidences.append(conf)

            if conf < 0.6:
                low_confidence_pages.append(page_num)

        return page_outputs, confidences, low_confidence_pages, warnings

    def _process_text_page(self, page) -> tuple[str, float]:
        """Process a text-heavy page using Textract DetectDocumentText."""
        pix = page.get_pixmap(dpi=150)
        png_bytes = pix.tobytes("png")

        response = detect_document_text(png_bytes)
        lines = extract_text_lines(response)
        text = "\n".join([l["text"] for l in lines])
        confidence = get_average_confidence(response) / 100.0

        if not text.strip():
            # Fallback to pymupdf text extraction
            text = page.get_text()
            confidence = 0.7

        return text, confidence

    def _process_table_page(self, page) -> tuple[str, float]:
        """Process a table-heavy page using Textract AnalyzeDocument."""
        pix = page.get_pixmap(dpi=200)
        png_bytes = pix.tobytes("png")

        response = analyze_document(png_bytes, features=["TABLES", "FORMS"])
        tables = extract_tables(response)
        forms = extract_forms(response)
        lines = extract_text_lines(response)
        confidence = get_average_confidence(response) / 100.0

        parts = []
        # Add non-table text
        non_table_text = "\n".join([l["text"] for l in lines])
        if non_table_text.strip():
            parts.append(non_table_text)

        # Add tables
        for table_md in tables:
            parts.append(f"\n{table_md}\n")

        # Add forms as key-value list
        if forms:
            parts.append("\n**Form Data:**\n")
            for kv in forms:
                parts.append(f"- **{kv['key']}**: {kv['value']}")

        return "\n".join(parts), confidence

    def _process_image_page(self, page, doc) -> tuple[str, float]:
        """Process an image-heavy page using VLM."""
        parts = []
        avg_conf = 0.0
        count = 0

        images = page.get_images(full=True)
        for img_info in images:
            xref = img_info[0]
            try:
                img_data = doc.extract_image(xref)
                img_bytes = img_data["image"]

                # Two-pass VLM
                classification = classify_image(img_bytes)
                visual_type = classification.get("visual_type", "other")
                vlm_conf = classification.get("confidence", 3) / 5.0

                extraction = extract_from_image(img_bytes, visual_type)

                parts.append(f"**[{visual_type}]** {classification.get('brief_description', '')}\n\n{extraction}")
                avg_conf += vlm_conf
                count += 1
            except Exception as e:
                parts.append(f"<!-- Failed to extract image: {str(e)} -->")

        final_conf = (avg_conf / max(count, 1))
        return "\n\n".join(parts) if parts else "*No images extracted*", final_conf

    def _process_mixed_page(self, page, doc) -> tuple[str, float]:
        """Process a mixed page with both text and images."""
        # Get text via Textract
        pix = page.get_pixmap(dpi=150)
        png_bytes = pix.tobytes("png")

        response = detect_document_text(png_bytes)
        lines = extract_text_lines(response)
        text_conf = get_average_confidence(response) / 100.0

        # Get images via VLM
        image_parts = []
        img_conf = 0.0
        img_count = 0

        images = page.get_images(full=True)
        for img_info in images:
            xref = img_info[0]
            try:
                img_data = doc.extract_image(xref)
                classification = classify_image(img_data["image"])
                extraction = extract_from_image(img_data["image"], classification.get("visual_type", "other"))
                image_parts.append({
                    "content": extraction,
                    "y_pos": 0.5,  # Approximate mid-page
                })
                img_conf += classification.get("confidence", 3) / 5.0
                img_count += 1
            except Exception:
                pass

        # Merge in reading order
        parts = []
        for line in lines:
            parts.append((line["top"], line["text"]))
        for img_part in image_parts:
            parts.append((img_part["y_pos"], f"\n{img_part['content']}\n"))

        parts.sort(key=lambda x: x[0])
        merged = "\n".join([p[1] for p in parts])

        confidence = (text_conf + (img_conf / max(img_count, 1))) / 2
        return merged, confidence


# Convenience aliases for routing
class PDFTextAgent(PDFHybridAgent):
    agent_name = "pdf_text_agent"


class PDFScannedAgent(PDFHybridAgent):
    agent_name = "pdf_scanned_agent"

    def process(self, file_meta: FileMetadata, file_bytes: bytes) -> ParsedOutput:
        # Force scanned mode
        file_meta.is_scanned = True
        return super().process(file_meta, file_bytes)
