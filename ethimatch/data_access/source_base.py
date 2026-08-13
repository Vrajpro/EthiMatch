"""Extended patient data source with cohort search and pre-extracted entity cache."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from data_simulator import PatientProfile

from data_access.interfaces import PatientDataProvider
from data_access.records import CarePlanRecord, ConditionRecord, MedicationRecord

class PatientDataSource(PatientDataProvider, ABC):
    """Cohort-level patient source with pre-extracted entity cache."""

    @abstractmethod
    def get_patient(self, patient_id: str) -> Optional[PatientProfile]:
        """Fetch a single patient by ID."""
        ...

    @abstractmethod
    def get_all_patients(self) -> list[PatientProfile]:
        """Return the full patient cohort from this source."""
        ...

    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name for logging / audit trails."""
        ...

    @abstractmethod
    def get_pre_extracted(self, patient_id: str) -> Optional[dict[str, Any]]:
        """Return cached pre-extracted entities for one patient."""
        ...

    @abstractmethod
    def get_all_pre_extracted(self) -> dict[str, dict[str, Any]]:
        """Return cached pre-extracted entities for all patients."""
        ...

    @staticmethod
    def _conditions_from_profile(p: PatientProfile) -> list[ConditionRecord]:
        records: list[ConditionRecord] = []
        if p.disease:
            records.append(ConditionRecord(
                description=p.disease, patient_id=p.patient_id,
            ))
        for c in p.comorbidities:
            records.append(ConditionRecord(description=c, patient_id=p.patient_id))
        return records

    @staticmethod
    def _medications_from_profile(p: PatientProfile) -> list[MedicationRecord]:
        return [
            MedicationRecord(description=t, patient_id=p.patient_id)
            for t in p.prior_therapies
        ]

    @staticmethod
    def _careplans_from_profile(p: PatientProfile) -> list[CarePlanRecord]:
        plans: list[CarePlanRecord] = []
        if p.disease:
            plans.append(CarePlanRecord(
                description="Oncology treatment plan",
                reason=p.disease,
                patient_id=p.patient_id,
            ))
            plans.append(CarePlanRecord(
                description="Tumor board follow-up",
                reason=f"{p.disease} — stage {p.stage or 'unknown'}",
                patient_id=p.patient_id,
            ))
        if p.biomarkers:
            plans.append(CarePlanRecord(
                description="Molecular monitoring",
                reason=", ".join(p.biomarkers),
                patient_id=p.patient_id,
            ))
        return plans

    def get_ehr_notes(self) -> list[str]:
        """Return the EHR free-text notes for all patients."""
        return [p.ehr_note for p in self.get_all_patients() if p.ehr_note]

    def get_patient_note(self, patient_id: str) -> Optional[str]:
        """Return the raw EHR note for a specific patient."""
        return PatientDataProvider.get_patient_note(self, patient_id)

    def filter_by_criteria(
        self,
        criteria: dict[str, Any],
    ) -> list[tuple[str, dict[str, Any], bool, list[str]]]:
        """Filter all patients against ad-hoc trial criteria."""
        all_entities = self.get_all_pre_extracted()
        results = []

        for pid, ent in all_entities.items():
            eligible = True
            reasons: list[str] = []

            age = ent.get("age")
            age_min = criteria.get("age_min")
            age_max = criteria.get("age_max")
            if age is not None:
                if age_min is not None and age < age_min:
                    eligible = False
                    reasons.append(f"Age {age} below minimum {age_min}")
                if age_max is not None and age > age_max:
                    eligible = False
                    reasons.append(f"Age {age} exceeds maximum {age_max}")

            gender = ent.get("gender")
            allowed_genders = criteria.get("gender")
            if allowed_genders and gender:
                if gender.lower() not in [g.lower() for g in allowed_genders]:
                    eligible = False
                    reasons.append(f"Gender '{gender}' not in {allowed_genders}")

            disease = ent.get("disease")
            allowed_diseases = criteria.get("diseases")
            if allowed_diseases and disease:
                if disease not in allowed_diseases:
                    eligible = False
                    reasons.append(f"Disease '{disease}' not in {allowed_diseases}")

            stage = ent.get("stage")
            allowed_stages = criteria.get("stages")
            if allowed_stages and stage:
                if stage not in allowed_stages:
                    eligible = False
                    reasons.append(f"Stage '{stage}' not in {allowed_stages}")

            ecog = ent.get("ecog_ps")
            ecog_max = criteria.get("ecog_max")
            if ecog is not None and ecog_max is not None:
                if ecog > ecog_max:
                    eligible = False
                    reasons.append(f"ECOG {ecog} exceeds max {ecog_max}")

            bmi = ent.get("bmi")
            bmi_max = criteria.get("bmi_max")
            if bmi is not None and bmi_max is not None:
                if bmi > bmi_max:
                    eligible = False
                    reasons.append(f"BMI {bmi} exceeds max {bmi_max}")

            bmi_min = criteria.get("bmi_min")
            if bmi is not None and bmi_min is not None:
                if bmi < bmi_min:
                    eligible = False
                    reasons.append(f"BMI {bmi} below min {bmi_min}")

            req_bio = criteria.get("required_biomarkers", [])
            patient_bio = ent.get("biomarkers", [])
            for rb in req_bio:
                if rb not in patient_bio:
                    eligible = False
                    reasons.append(f"Missing required biomarker: {rb}")

            excl_comorb = criteria.get("excluded_comorbidities", [])
            patient_comorb = ent.get("comorbidities", [])
            for ec in excl_comorb:
                if ec.lower() in [c.lower() for c in patient_comorb]:
                    eligible = False
                    reasons.append(f"Excluded comorbidity: {ec}")

            excl_rx = criteria.get("excluded_prior_therapies", [])
            patient_rx = ent.get("prior_therapies", [])
            for er in excl_rx:
                if er.lower() in [t.lower() for t in patient_rx]:
                    eligible = False
                    reasons.append(f"Excluded prior therapy: {er}")

            if eligible:
                reasons = ["All criteria satisfied"]

            results.append((pid, ent, eligible, reasons))

        return results
