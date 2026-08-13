"""Patient data ingestion package for EthiMatch."""

from data_access.csv_factory import (
    get_data_provider,
    get_data_source,
    get_default_csv_provider,
    select_patient_ids_for_screening,
)
from data_access.csv_provider import RealCSVProvider, SyntheticCSVProvider
from data_access.interfaces import PatientDataProvider
from data_access.loader import load_provider, normalise_source
from data_access.mimic_demo import MIMICDualSourceProvider
from data_access.mock_clinical_note import generate_mock_clinical_note
from data_access.records import CarePlanRecord, ConditionRecord, MedicationRecord
from data_access.source_base import PatientDataSource
from data_access.synthea_provider import SyntheaDualSourceProvider
from data_access.types import DATA_SOURCE_LABELS, DEFAULT_MIMIC_DEMO_DIR, DataSource

__all__ = [
    "CarePlanRecord",
    "ConditionRecord",
    "DATA_SOURCE_LABELS",
    "DataSource",
    "DEFAULT_MIMIC_DEMO_DIR",
    "MedicationRecord",
    "MIMICDualSourceProvider",
    "PatientDataProvider",
    "PatientDataSource",
    "RealCSVProvider",
    "SyntheticCSVProvider",
    "SyntheaDualSourceProvider",
    "generate_mock_clinical_note",
    "get_data_provider",
    "get_data_source",
    "get_default_csv_provider",
    "load_provider",
    "normalise_source",
    "select_patient_ids_for_screening",
]
