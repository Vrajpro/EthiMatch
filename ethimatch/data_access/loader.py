"""Dual-source provider factory (MIMIC-IV Demo and Synthea)."""

from __future__ import annotations

from pathlib import Path

from data_access.source_base import PatientDataSource
from data_access.types import DataSource

def normalise_source(source: str | None) -> DataSource:
    """Coerce loose user input to one of the canonical literals."""
    if not source:
        return "Synthea"
    key = str(source).strip().lower()
    if key in ("mimic", "mimic-iv", "mimic-iv demo", "mimic_iv", "mimic_iv_demo"):
        return "MIMIC"
    return "Synthea"

from data_access.mimic_demo import MIMICDualSourceProvider
from data_access.synthea_provider import SyntheaDualSourceProvider

def load_provider(
    source: str | DataSource = "Synthea",
    *,
    limit: int | None = None,
    data_dir: str | Path | None = None,
    verbose: bool = False,
) -> PatientDataSource:
    """Factory returning the configured patient data provider.

    Parameters
    ----------
    source:
        ``"MIMIC"`` or ``"Synthea"`` (case-insensitive; loose strings are
        normalised via :func:`normalise_source`).
    limit:
        Optional row cap (``None`` or ``0`` = load all rows).
    data_dir:
        Override the default CSV root for the chosen source.
    """
    src = normalise_source(source)
    eff_limit = None if (limit is None or limit == 0) else int(limit)
    if src == "MIMIC":
        return MIMICDualSourceProvider(
            data_dir=data_dir, limit=eff_limit, verbose=verbose,
        )
    return SyntheaDualSourceProvider(
        data_dir=data_dir, limit=eff_limit, verbose=verbose,
    )
