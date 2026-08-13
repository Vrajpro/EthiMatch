"""Backward-compatible facade for CSV and legacy patient data providers."""

from data_access.csv_factory import (
    get_data_provider,
    get_data_source,
    get_default_csv_provider,
    select_patient_ids_for_screening,
)
from data_access.csv_provider import RealCSVProvider, SyntheticCSVProvider
from data_access.fhir_mock import FHIRPatientBundle, MockFHIRAPI
from data_access.source_base import PatientDataSource
from data_access.synthetic import SyntheticData

__all__ = [
    "FHIRPatientBundle",
    "MockFHIRAPI",
    "PatientDataSource",
    "RealCSVProvider",
    "SyntheticCSVProvider",
    "SyntheticData",
    "get_data_provider",
    "get_data_source",
    "get_default_csv_provider",
    "select_patient_ids_for_screening",
]
