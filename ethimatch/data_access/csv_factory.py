"""CSV provider factory and patient ID selection helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from data_access.csv_provider import RealCSVProvider
from data_access.interfaces import PatientDataProvider
from data_access.source_base import PatientDataSource

_ACTIVE_SOURCES = frozenset({"csv", "default", "synthetic_csv"})
_FUTURE_SOURCES = frozenset({"synthetic", "fhir", "mimic"})

def select_patient_ids_for_screening(
    provider: PatientDataSource,
    *,
    max_patients: int,
    oncology_only: bool = True,
    disease_codes: list[str] | None = None,
) -> list[str]:
    """Return a bounded patient ID list for BioBERT batch screening.

    When *disease_codes* is set, keeps patients whose structured profile maps to
    any of those codes (including related variants via ``disease_filter_variants``).

    When *oncology_only* is True (and no *disease_codes*), keeps patients whose
    pre-extracted profile maps to a trial disease in ``config.ALLOWED_DISEASES``.

    Otherwise returns all loaded patient IDs (up to *max_patients*).
    """
    from config import ALLOWED_DISEASES, disease_filter_variants, normalize_disease

    def _codes_for_patient(pid: str) -> set[str]:
        found: set[str] = set()
        if hasattr(provider, "get_pre_extracted"):
            ent = provider.get_pre_extracted(pid) or {}
            d = ent.get("disease")
            if isinstance(d, str) and d.strip():
                found.add(d.strip())
        patient = provider.get_patient(pid)
        if patient is None:
            return found
        if patient.disease:
            found.add(patient.disease)
        for cond in getattr(patient, "active_conditions", None) or []:
            mapped = normalize_disease(cond)
            if mapped:
                found.add(mapped)
        for cond in patient.comorbidities or []:
            mapped = normalize_disease(cond)
            if mapped:
                found.add(mapped)
        return found

    ids = provider.list_patient_ids()

    if disease_codes:
        wanted: set[str] = set()
        for code in disease_codes:
            wanted.update(disease_filter_variants(code))
        ids = [pid for pid in ids if _codes_for_patient(pid) & wanted]
    elif oncology_only and hasattr(provider, "get_pre_extracted"):
        filtered: list[str] = []
        for pid in ids:
            ent = provider.get_pre_extracted(pid) or {}
            disease = ent.get("disease")
            if disease in ALLOWED_DISEASES:
                filtered.append(pid)
        ids = filtered

    if max_patients > 0 and len(ids) > max_patients:
        ids = ids[:max_patients]
    return ids

def get_default_csv_provider(
    data_dir: str | Path | None = None,
    limit: int | None = None,
    verbose: bool = False,
    **kwargs: Any,
) -> RealCSVProvider:
    """Load patients from the configured local CSV directory."""
    from config import DEFAULT_CSV_DIR, DEFAULT_CSV_UI_PATIENT_LIMIT

    resolved_dir = Path(data_dir) if data_dir is not None else DEFAULT_CSV_DIR
    if limit == 0:
        patient_limit = None
    elif limit is not None:
        patient_limit = limit
    else:
        patient_limit = DEFAULT_CSV_UI_PATIENT_LIMIT
    return RealCSVProvider(
        data_dir=resolved_dir,
        limit=patient_limit,
        verbose=verbose,
        **kwargs,
    )

def get_data_source(
    source: str = "csv", **kwargs: Any,
) -> PatientDataSource:
    """Factory — returns the active patient data provider.

    This build loads **local CSV files only** via :class:`RealCSVProvider`.
    Alternate backends (:class:`SyntheticData`, :class:`MockFHIRAPI`,
    ``MIMICDataSource``) remain in the codebase for future plug-in but are
    not wired here.
    """
    key = (source or "csv").lower()
    if key in _FUTURE_SOURCES:
        raise NotImplementedError(
            f"Data source '{source}' is not enabled. EthiMatch currently reads "
            "patients from local CSV files only (patients.csv, conditions.csv, "
            "medications.csv). Implement PatientDataProvider and register it in "
            "get_data_source() when ready."
        )
    if key in _ACTIVE_SOURCES:
        if "data_dir" not in kwargs:
            from config import DEFAULT_CSV_DIR
            kwargs.setdefault("data_dir", DEFAULT_CSV_DIR)
        return RealCSVProvider(**kwargs)
    raise ValueError(
        f"Unknown data source '{source}'. Supported: {', '.join(sorted(_ACTIVE_SOURCES))}."
    )

def get_data_provider(source: str = "csv", **kwargs: Any) -> PatientDataProvider:
    """Alias for get_data_source — pipeline ingestion entry point."""
    return get_data_source(source, **kwargs)