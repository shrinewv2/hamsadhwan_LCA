"""Output 3 — Visualization Data Builder."""

from typing import Any

import structlog

from backend.config import get_settings
from backend.storage.s3_client import upload_json
from backend.validation.lca_taxonomy import LIFE_CYCLE_STAGES

logger = structlog.get_logger(__name__)


async def build_viz_data(
    job_id: str,
    synthesis_result: dict[str, Any],
    validation_summaries: list[dict[str, Any]] | None = None,
    file_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build chart-ready data objects for the frontend.

    Outputs:
    - impact_bar_chart: { labels, values, units }
    - hotspot_pareto: { labels, values, cumulative_pct }
    - completeness_gauge: { value, label }
    - stage_coverage_heatmap: { stages, covered }
    - data_quality_scores: { file_ids, scores, labels }
    """
    structured = synthesis_result.get("structured_insights", {})
    file_records = file_records or []
    validation_summaries = validation_summaries or []

    viz_data: dict[str, Any] = {}

    # ─── Impact Bar Chart ───
    impact_results = structured.get("impact_results", [])
    viz_data["impact_bar_chart"] = {
        "labels": [ir.get("category", "Unknown") for ir in impact_results],
        "values": [ir.get("value", 0) for ir in impact_results],
        "units": [ir.get("unit", "") for ir in impact_results],
    }

    # ─── Hotspot Pareto ───
    hotspots = structured.get("hotspots", [])
    # Sort by contribution descending
    sorted_hotspots = sorted(
        hotspots, key=lambda h: h.get("contribution_pct", 0) or 0, reverse=True
    )
    values = [h.get("contribution_pct", 0) or 0 for h in sorted_hotspots]
    cumulative = []
    running = 0.0
    for v in values:
        running += v
        cumulative.append(round(running, 1))

    viz_data["hotspot_pareto"] = {
        "labels": [h.get("process", "Unknown") for h in sorted_hotspots],
        "values": values,
        "cumulative_pct": cumulative,
    }

    # ─── Completeness Gauge ───
    completeness = structured.get("completeness") or 0.0
    viz_data["completeness_gauge"] = {
        "value": completeness,
        "label": f"{int(completeness * 100)}% Complete",
    }

    # ─── Stage Coverage Heatmap ───
    # Check which life cycle stages are mentioned in the synthesis
    cross_doc = synthesis_result.get("cross_doc_synthesis", "")
    insights = synthesis_result.get("insights_markdown", "")
    combined_text = f"{cross_doc}\n{insights}".upper()

    stages = list(LIFE_CYCLE_STAGES.keys())
    covered = []
    for stage in stages:
        covered.append(stage in combined_text)

    viz_data["stage_coverage_heatmap"] = {
        "stages": stages,
        "covered": covered,
    }

    # ─── Data Quality Scores ───
    quality_map = {"Excellent": 4, "Good": 3, "Fair": 2, "Poor": 1, "Unknown": 0}
    file_ids = []
    scores = []
    labels = []

    for vs in validation_summaries:
        file_ids.append(vs.get("file_id", "unknown"))
        rating = vs.get("data_quality_rating", "Unknown")
        scores.append(quality_map.get(rating, 0))
        labels.append(vs.get("filename", "Unknown"))

    viz_data["data_quality_scores"] = {
        "file_ids": file_ids,
        "scores": scores,
        "labels": labels,
    }

    # Store to S3
    s3_key = f"reports/{job_id}/viz_data.json"
    try:
        cfg = get_settings()
        upload_json(cfg.S3_BUCKET_REPORTS, s3_key, viz_data)
        logger.info("viz_data_uploaded", job_id=job_id, s3_key=s3_key)
    except Exception as e:
        logger.error("viz_data_upload_failed", job_id=job_id, error=str(e))

    return viz_data
