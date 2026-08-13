"""Backward-compatible facade for patient data provider contracts."""

from data_access.interfaces import PatientDataProvider
from data_access.note_composition import _calc_age, compose_clinical_note
from data_access.records import CarePlanRecord, ConditionRecord, MedicationRecord

__all__ = [
    "CarePlanRecord",
    "ConditionRecord",
    "MedicationRecord",
    "PatientDataProvider",
    "_calc_age",
    "compose_clinical_note",
]
