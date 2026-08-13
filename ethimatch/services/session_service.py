"""Session-state cache invalidation when registry settings change."""

from __future__ import annotations

from typing import Any

_SCREENING_CACHE_KEYS = (
    "matching_results",
    "matching_results_by_id",
    "matching_selected_patient_id",
    "matching_registry_page",
    "cohort_results",
    "cohort_results_by_id",
    "cohort_export_data",
    "cohort_pdf_bytes",
    "cohort_selected_patient_id",
    "cohort_registry_page",
)

def clear_screening_cache_if_changed(session: dict[str, Any], source: str, limit: int) -> None:
    cache_key = (source, limit)
    if session.get("_screening_registry_state") == cache_key:
        return
    for key in _SCREENING_CACHE_KEYS:
        session.pop(key, None)
    session["_screening_registry_state"] = cache_key
    session["_screening_registry_limit"] = limit
