"""Backward-compatible facade for dual-source provider loading."""

from data_access.loader import load_provider, normalise_source
from data_access.mimic_demo import MIMICDualSourceProvider
from data_access.mock_clinical_note import generate_mock_clinical_note
from data_access.synthea_provider import SyntheaDualSourceProvider
from data_access.types import DATA_SOURCE_LABELS, DEFAULT_MIMIC_DEMO_DIR, DataSource

__all__ = [
    "DATA_SOURCE_LABELS",
    "DataSource",
    "DEFAULT_MIMIC_DEMO_DIR",
    "MIMICDualSourceProvider",
    "SyntheaDualSourceProvider",
    "generate_mock_clinical_note",
    "load_provider",
    "normalise_source",
]
