"""Abstract patient data ingestion contract for the EthiMatch pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from data_simulator import PatientProfile

from data_access.note_composition import compose_clinical_note
from data_access.records import CarePlanRecord, ConditionRecord, MedicationRecord

class PatientDataProvider(ABC):
    """Abstract contract for patient data ingestion."""

    @abstractmethod
    def get_patient(self, patient_id: str) -> Optional[PatientProfile]:
        """Fetch demographic / profile data for one patient."""
        ...

    @abstractmethod
    def get_conditions(self, patient_id: str) -> list[ConditionRecord]:
        """Return clinical conditions for a patient."""
        ...

    @abstractmethod
    def get_medications(self, patient_id: str) -> list[MedicationRecord]:
        """Return medications / prior therapies for a patient."""
        ...

    def get_careplans(self, patient_id: str) -> list[CarePlanRecord]:
        """Return active care plans for a patient (optional — default empty)."""
        return []

    def list_patient_ids(self) -> list[str]:
        """All patient IDs available from this provider."""
        return [p.patient_id for p in self.get_all_patients()]

    def get_all_patients(self) -> list[PatientProfile]:
        """Default: iterate known IDs. Override for efficiency."""
        return []

    def source_name(self) -> str:
        return self.__class__.__name__

    def get_patient_note(self, patient_id: str) -> Optional[str]:
        """Return unstructured note text, composing from structured rows if needed."""
        patient = self.get_patient(patient_id)
        if patient is None:
            return None
        if patient.ehr_note:
            return patient.ehr_note
        return compose_clinical_note(
            patient,
            self.get_conditions(patient_id),
            self.get_medications(patient_id),
        )
