"""ClamAV virus scanning integration (stub if unavailable)."""
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger("virus_scanner")


def scan_file(file_bytes: bytes, filename: str = "") -> dict:
    """
    Scan a file for viruses using ClamAV.
    Returns dict with 'clean' (bool) and 'details' (str).
    
    If VIRUS_SCAN_ENABLED is False or ClamAV is unavailable, returns clean.
    """
    if settings and not settings.VIRUS_SCAN_ENABLED:
        logger.info("virus_scan_skipped", reason="disabled_by_config")
        return {"clean": True, "details": "Scan disabled"}

    try:
        import pyclamd
        cd = pyclamd.ClamdUnixSocket()
        if not cd.ping():
            logger.warning("clamav_not_available", detail="ClamAV daemon not responding")
            return {"clean": True, "details": "ClamAV unavailable — skipped"}

        result = cd.scan_stream(file_bytes)
        if result is None:
            return {"clean": True, "details": "No threats found"}
        else:
            detail = str(result)
            logger.error("virus_detected", filename=filename, detail=detail)
            return {"clean": False, "details": detail}

    except ImportError:
        logger.info("virus_scan_skipped", reason="pyclamd_not_installed")
        return {"clean": True, "details": "pyclamd not installed — skipped"}
    except Exception as e:
        logger.warning("virus_scan_error", error=str(e))
        return {"clean": True, "details": f"Scan error: {str(e)} — skipped"}
