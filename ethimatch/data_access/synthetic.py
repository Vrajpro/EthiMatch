"""In-memory synthetic patient cohort provider."""

from __future__ import annotations

import random
from typing import Any, Optional

from data_simulator import PatientProfile, SyntheticNoteGenerator, build_synthetic_patients
from console import safe_print

from data_access.records import CarePlanRecord, ConditionRecord, MedicationRecord
from data_access.source_base import PatientDataSource

# Extra patients beyond the 8 in data_simulator.py
_EXTRA_PATIENTS: list[dict[str, Any]] = [
    {
        "patient_id": "SYN-009", "age": 62, "gender": "male",
        "disease": "NSCLC", "stage": "IV",
        "biomarkers": ["EGFR+", "PD-L1 55%"], "bmi": 23.0,
        "comorbidities": ["asthma"], "ecog_ps": 1,
        "prior_therapies": ["pemetrexed"],
    },
    {
        "patient_id": "SYN-010", "age": 44, "gender": "female",
        "disease": "Breast Cancer", "stage": "IIA",
        "biomarkers": ["HER2+", "ER-", "PR-"], "bmi": 22.8,
        "comorbidities": [], "ecog_ps": 0,
        "prior_therapies": [],
    },
    {
        "patient_id": "SYN-011", "age": 71, "gender": "male",
        "disease": "NSCLC", "stage": "IIIA",
        "biomarkers": ["ALK-", "PD-L1 20%"], "bmi": 27.2,
        "comorbidities": ["COPD"], "ecog_ps": 2,
        "prior_therapies": ["carboplatin", "paclitaxel"],
    },
    {
        "patient_id": "SYN-012", "age": 39, "gender": "female",
        "disease": "Breast Cancer", "stage": "III",
        "biomarkers": ["HER2+", "ER+", "PR+"], "bmi": 25.5,
        "comorbidities": [], "ecog_ps": 0,
        "prior_therapies": ["trastuzumab"],
    },
    {
        "patient_id": "SYN-013", "age": 56, "gender": "male",
        "disease": "NSCLC", "stage": "IIIB",
        "biomarkers": ["KRAS G12C", "PD-L1 60%"], "bmi": 29.8,
        "comorbidities": ["hypertension"], "ecog_ps": 1,
        "prior_therapies": [],
    },
    {
        "patient_id": "SYN-014", "age": 65, "gender": "female",
        "disease": "NSCLC", "stage": "IV",
        "biomarkers": ["EGFR+", "ALK-"], "bmi": 20.5,
        "comorbidities": ["osteoporosis"], "ecog_ps": 1,
        "prior_therapies": ["cisplatin", "bevacizumab"],
    },
    {
        "patient_id": "SYN-015", "age": 48, "gender": "male",
        "disease": "NSCLC", "stage": "III",
        "biomarkers": ["PD-L1 80%"], "bmi": 31.0,
        "comorbidities": ["type 2 diabetes"], "ecog_ps": 0,
        "prior_therapies": [],
    },
    {
        "patient_id": "SYN-016", "age": 53, "gender": "female",
        "disease": "Breast Cancer", "stage": "IIB",
        "biomarkers": ["HER2+", "ER-"], "bmi": 26.0,
        "comorbidities": [], "ecog_ps": 1,
        "prior_therapies": ["tamoxifen"],
    },
    {
        "patient_id": "SYN-017", "age": 69, "gender": "male",
        "disease": "NSCLC", "stage": "IV",
        "biomarkers": ["BRAF V600E", "PD-L1 40%"], "bmi": 24.2,
        "comorbidities": ["CHF"], "ecog_ps": 2,
        "prior_therapies": ["nivolumab"],
    },
    {
        "patient_id": "SYN-018", "age": 41, "gender": "female",
        "disease": "Breast Cancer", "stage": "II",
        "biomarkers": ["HER2+", "ER+", "PR-"], "bmi": 23.5,
        "comorbidities": [], "ecog_ps": 0,
        "prior_therapies": [],
    },
    {
        "patient_id": "SYN-019", "age": 77, "gender": "male",
        "disease": "SCLC", "stage": "IV",
        "biomarkers": ["PD-L1 5%"], "bmi": 19.5,
        "comorbidities": ["COPD", "atrial fibrillation"], "ecog_ps": 3,
        "prior_therapies": ["cisplatin", "etoposide"],
    },
    {
        "patient_id": "SYN-020", "age": 50, "gender": "female",
        "disease": "NSCLC", "stage": "IIIA",
        "biomarkers": ["EGFR+", "PD-L1 75%"], "bmi": 24.8,
        "comorbidities": [], "ecog_ps": 0,
        "prior_therapies": ["carboplatin"],
    },
]

class SyntheticData(PatientDataSource):
    """In-memory synthetic cohort with optional pre-extracted entity cache."""

    def __init__(self, n: int = 20, seed: int = 42, verbose: bool = False) -> None:
        random.seed(seed)

        core = build_synthetic_patients(min(n, 8))
        self._patients: list[PatientProfile] = list(core)

        extras_needed = max(0, n - len(core))
        for rec in _EXTRA_PATIENTS[:extras_needed]:
            p = PatientProfile(
                patient_id=rec["patient_id"],
                age=rec["age"],
                gender=rec["gender"],
                disease=rec["disease"],
                stage=rec["stage"],
                biomarkers=list(rec["biomarkers"]),
                bmi=rec["bmi"],
                comorbidities=list(rec["comorbidities"]),
                ecog_ps=rec["ecog_ps"],
                prior_therapies=list(rec["prior_therapies"]),
            )
            p.ehr_note = SyntheticNoteGenerator.generate_note(p)
            self._patients.append(p)

        self._index: dict[str, PatientProfile] = {
            p.patient_id: p for p in self._patients
        }

        # Pre-extract entities from structured profiles (no NER needed)
        self._pre_extracted: dict[str, dict[str, Any]] = {}
        for p in self._patients:
            self._pre_extracted[p.patient_id] = self._profile_to_entities(p)

        if verbose:
            safe_print(
                f"[SyntheticData] Loaded {len(self._patients)} patients "
                f"with pre-extracted entity cache."
            )

    @staticmethod
    def _profile_to_entities(p: PatientProfile) -> dict[str, Any]:
        """Convert a PatientProfile to the entity dict format.

        This mirrors ExtractedEntities.to_dict() output so the
        SymbolicValidator can consume it directly.
        """
        return {
            "age":               p.age,
            "gender":            p.gender,
            "disease":           p.disease,
            "stage":             p.stage,
            "biomarkers":        list(p.biomarkers),
            "bmi":               p.bmi,
            "ecog_ps":           p.ecog_ps,
            "comorbidities":     list(p.comorbidities),
            "prior_therapies":   list(p.prior_therapies),
            "confidence_scores": {
                "age": 1.0, "gender": 1.0, "disease": 1.0,
                "stage": 1.0, "bmi": 1.0, "ecog_ps": 1.0,
                "biomarkers": 1.0, "comorbidities": 1.0,
                "prior_therapies": 1.0,
            },
            "extraction_sources": {
                "age": "gold", "gender": "gold", "disease": "gold",
                "stage": "gold", "bmi": "gold", "ecog_ps": "gold",
                "biomarkers": "gold", "comorbidities": "gold",
                "prior_therapies": "gold",
            },
        }

    def source_name(self) -> str:
        return f"SyntheticData ({len(self._patients)} patients, in-memory)"

    def get_patient(self, patient_id: str) -> Optional[PatientProfile]:
        patient = self._index.get(patient_id)
        if patient is None:
            safe_print(f"[SyntheticData] WARN: Patient '{patient_id}' not found.")
        return patient

    def get_all_patients(self) -> list[PatientProfile]:
        return list(self._patients)

    def get_pre_extracted(self, patient_id: str) -> Optional[dict[str, Any]]:
        return self._pre_extracted.get(patient_id)

    def get_all_pre_extracted(self) -> dict[str, dict[str, Any]]:
        return dict(self._pre_extracted)

    def get_conditions(self, patient_id: str) -> list[ConditionRecord]:
        p = self.get_patient(patient_id)
        return self._conditions_from_profile(p) if p else []

    def get_medications(self, patient_id: str) -> list[MedicationRecord]:
        p = self.get_patient(patient_id)
        return self._medications_from_profile(p) if p else []

    def get_careplans(self, patient_id: str) -> list[CarePlanRecord]:
        p = self.get_patient(patient_id)
        return self._careplans_from_profile(p) if p else []

    def add_patient(self, profile: PatientProfile) -> None:
        """Inject an additional patient (useful for evaluation tests)."""
        if not profile.ehr_note:
            profile.ehr_note = SyntheticNoteGenerator.generate_note(profile)
        self._patients.append(profile)
        self._index[profile.patient_id] = profile
        self._pre_extracted[profile.patient_id] = self._profile_to_entities(
            profile)
