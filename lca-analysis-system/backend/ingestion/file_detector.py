"""Magic-byte file type detection for uploaded files."""
import io
import zipfile
from typing import Optional

from backend.models.enums import FileType
from backend.utils.logger import get_logger

logger = get_logger("file_detector")

# MIME to FileType mapping
MIME_MAP = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": FileType.EXCEL,
    "application/vnd.ms-excel": FileType.EXCEL,
    "text/csv": FileType.CSV,
    "application/csv": FileType.CSV,
    "application/pdf": FileType.PDF,
    "image/png": FileType.IMAGE,
    "image/jpeg": FileType.IMAGE,
    "image/tiff": FileType.IMAGE,
    "image/webp": FileType.IMAGE,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCX,
    "text/plain": FileType.TEXT,
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": FileType.PPTX,
    "text/xml": FileType.UNKNOWN,  # Needs further probing
    "application/xml": FileType.UNKNOWN,
    "application/zip": FileType.UNKNOWN,  # Needs further probing
}


def detect_file_type(file_bytes: bytes, filename: str = "") -> tuple[FileType, str]:
    """
    Detect actual file type from magic bytes, not file extension.
    
    Returns:
        Tuple of (FileType, detected_mime_string)
    """
    try:
        import magic
        mime = magic.from_buffer(file_bytes[:2048], mime=True)
    except ImportError:
        logger.warning("python-magic not installed, falling back to extension-based detection")
        mime = _fallback_mime_from_extension(filename)
    except Exception as e:
        logger.warning("magic detection failed", error=str(e))
        mime = _fallback_mime_from_extension(filename)

    file_type = MIME_MAP.get(mime, FileType.UNKNOWN)

    # Special probe for ZIP files — could be xmind
    if mime == "application/zip" or file_type == FileType.UNKNOWN and mime in ("application/zip",):
        file_type = _probe_zip(file_bytes, filename)

    # Special probe for XML — could be FreeMind
    if mime in ("text/xml", "application/xml"):
        file_type = _probe_xml(file_bytes)

    # Extension-based fallback if still unknown
    if file_type == FileType.UNKNOWN and filename:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        ext_map = {
            "xlsx": FileType.EXCEL, "xls": FileType.EXCEL, "xlsm": FileType.EXCEL,
            "csv": FileType.CSV, "pdf": FileType.PDF,
            "png": FileType.IMAGE, "jpg": FileType.IMAGE, "jpeg": FileType.IMAGE,
            "tiff": FileType.IMAGE, "tif": FileType.IMAGE, "webp": FileType.IMAGE,
            "xmind": FileType.MINDMAP_XMIND, "mm": FileType.MINDMAP_FREEMIND,
            "docx": FileType.DOCX, "doc": FileType.DOCX,
            "txt": FileType.TEXT, "rtf": FileType.TEXT,
            "pptx": FileType.PPTX,
        }
        if ext in ext_map:
            file_type = ext_map[ext]

    return file_type, mime


def _probe_zip(file_bytes: bytes, filename: str) -> FileType:
    """Probe a ZIP file to determine if it's an XMind file."""
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            names = zf.namelist()
            # XMind files contain content.json or content.xml
            if any("content.json" in n or "content.xml" in n for n in names):
                return FileType.MINDMAP_XMIND
            # Check for xmind manifest
            if any("manifest.json" in n or "META-INF" in n for n in names):
                if filename.lower().endswith(".xmind"):
                    return FileType.MINDMAP_XMIND
            # Check for Office formats (docx, xlsx, pptx are also zip)
            if any("[Content_Types].xml" in n for n in names):
                if any("xl/" in n for n in names):
                    return FileType.EXCEL
                if any("word/" in n for n in names):
                    return FileType.DOCX
                if any("ppt/" in n for n in names):
                    return FileType.PPTX
    except zipfile.BadZipFile:
        pass
    return FileType.UNKNOWN


def _probe_xml(file_bytes: bytes) -> FileType:
    """Probe an XML file to check for FreeMind schema."""
    try:
        text = file_bytes[:4096].decode("utf-8", errors="ignore")
        if "<map" in text.lower() and "<node" in text.lower():
            return FileType.MINDMAP_FREEMIND
    except Exception:
        pass
    return FileType.UNKNOWN


def _fallback_mime_from_extension(filename: str) -> str:
    """Fallback MIME type detection from file extension."""
    if not filename:
        return "application/octet-stream"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    ext_mime_map = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
        "xlsm": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "tiff": "image/tiff",
        "tif": "image/tiff",
        "webp": "image/webp",
        "xmind": "application/zip",
        "mm": "text/xml",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    return ext_mime_map.get(ext, "application/octet-stream")


def probe_pdf_structure(file_bytes: bytes) -> dict:
    """
    Perform additional PDF structure analysis using pymupdf.
    Returns dict with has_text_layer, has_embedded_images, is_scanned,
    has_tables_heuristic, page_count.
    """
    result = {
        "has_text_layer": False,
        "has_embedded_images": False,
        "is_scanned": False,
        "has_tables_heuristic": False,
        "page_count": 0,
    }
    try:
        import fitz  # pymupdf
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        result["page_count"] = len(doc)

        total_text_len = 0
        pages_with_images = 0
        pages_with_tables = 0

        for page in doc:
            text = page.get_text()
            text_len = len(text.strip())
            total_text_len += text_len

            images = page.get_images(full=True)
            if images:
                pages_with_images += 1
                result["has_embedded_images"] = True

            # Table heuristic: check for grid-like line patterns
            drawings = page.get_drawings()
            h_lines = 0
            v_lines = 0
            for d in drawings:
                for item in d.get("items", []):
                    if len(item) >= 3 and item[0] == "l":
                        p1, p2 = item[1], item[2]
                        if abs(p1.y - p2.y) < 2:  # horizontal line
                            h_lines += 1
                        if abs(p1.x - p2.x) < 2:  # vertical line
                            v_lines += 1
            if h_lines > 5 and v_lines > 5:
                pages_with_tables += 1

        # Determine text layer presence
        avg_text_per_page = total_text_len / max(result["page_count"], 1)
        result["has_text_layer"] = avg_text_per_page > 50

        # Determine if scanned
        result["is_scanned"] = (
            not result["has_text_layer"]
            or (avg_text_per_page < 50 and result["page_count"] > 3)
        )

        result["has_tables_heuristic"] = pages_with_tables > 0

        doc.close()
    except ImportError:
        logger.warning("pymupdf not installed, skipping PDF structure probing")
    except Exception as e:
        logger.error("pdf_structure_probe_failed", error=str(e))

    return result
