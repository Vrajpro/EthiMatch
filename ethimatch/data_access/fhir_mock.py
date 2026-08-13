"""Mock FHIR R4 patient endpoint for development."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

from data_simulator import PatientProfile, SyntheticNoteGenerator
from console import safe_print

from data_access.records import CarePlanRecord, ConditionRecord, MedicationRecord
from data_access.source_base import PatientDataSource
from data_access.synthetic import SyntheticData

@dataclass
class FHIRPatientBundle:
    """Simulates a FHIR R4 Patient resource bundle response."""
    resource_type: str = "Bundle"
    fhir_version:  str = "4.0.1"
    patient_id:    str = ""
    status:        str = "active"
    raw_resource:  dict = field(default_factory=dict)

class MockFHIRAPI(PatientDataSource):
    """Simulates fetching patients from a hospital FHIR R4 endpoint.

    10 mock patients with diverse clinical profiles.
    """

    _FHIR_RECORDS: dict[str, dict] = {
        "FHIR-PT-00001": {
            "patient_id": "FHIR-PT-00001", "age": 61, "gender": "female",
            "disease": "NSCLC", "stage": "IIIB",
            "biomarkers": ["EGFR+", "PD-L1 45%"], "bmi": 23.8,
            "comorbidities": ["hypertension"], "ecog_ps": 1,
            "prior_therapies": ["carboplatin", "pemetrexed"],
        },
        "FHIR-PT-00002": {
            "patient_id": "FHIR-PT-00002", "age": 47, "gender": "female",
            "disease": "Breast Cancer", "stage": "III",
            "biomarkers": ["HER2+", "ER+"], "bmi": 27.1,
            "comorbidities": [], "ecog_ps": 0,
            "prior_therapies": ["trastuzumab"],
        },
        "FHIR-PT-00003": {
            "patient_id": "FHIR-PT-00003", "age": 70, "gender": "male",
            "disease": "NSCLC", "stage": "IV",
            "biomarkers": ["KRAS G12C", "PD-L1 70%"], "bmi": 21.2,
            "comorbidities": ["COPD", "type 2 diabetes"], "ecog_ps": 2,
            "prior_therapies": ["docetaxel"],
        },
        "FHIR-PT-00004": {
            "patient_id": "FHIR-PT-00004", "age": 38, "gender": "female",
            "disease": "Breast Cancer", "stage": "IIB",
            "biomarkers": ["HER2-", "ER-", "PR-"], "bmi": 24.0,
            "comorbidities": [], "ecog_ps": 0,
            "prior_therapies": [],
        },
        "FHIR-PT-00005": {
            "patient_id": "FHIR-PT-00005", "age": 55, "gender": "male",
            "disease": "NSCLC", "stage": "IIIA",
            "biomarkers": ["ALK+", "PD-L1 80%"], "bmi": 26.5,
            "comorbidities": [], "ecog_ps": 1,
            "prior_therapies": [],
        },
        "FHIR-PT-00006": {
            "patient_id": "FHIR-PT-00006", "age": 59, "gender": "male",
            "disease": "NSCLC", "stage": "IV",
            "biomarkers": ["EGFR+", "PD-L1 30%"], "bmi": 22.4,
            "comorbidities": [], "ecog_ps": 1,
            "prior_therapies": ["bevacizumab"],
        },
        "FHIR-PT-00007": {
            "patient_id": "FHIR-PT-00007", "age": 52, "gender": "female",
            "disease": "Breast Cancer", "stage": "IIA",
            "biomarkers": ["HER2+", "ER+", "PR+"], "bmi": 25.0,
            "comorbidities": [], "ecog_ps": 0,
            "prior_therapies": ["letrozole"],
        },
        "FHIR-PT-00008": {
            "patient_id": "FHIR-PT-00008", "age": 74, "gender": "male",
            "disease": "NSCLC", "stage": "IV",
            "biomarkers": ["PD-L1 15%"], "bmi": 18.5,
            "comorbidities": ["CHF", "COPD"], "ecog_ps": 3,
            "prior_therapies": ["cisplatin", "nivolumab"],
        },
        "FHIR-PT-00009": {
            "patient_id": "FHIR-PT-00009", "age": 43, "gender": "female",
            "disease": "Breast Cancer", "stage": "II",
            "biomarkers": ["HER2+", "ER-", "PR-"], "bmi": 23.2,
            "comorbidities": [], "ecog_ps": 0,
            "prior_therapies": [],
        },
        "FHIR-PT-00010": {
            "patient_id": "FHIR-PT-00010", "age": 66, "gender": "male",
            "disease": "NSCLC", "stage": "IIIB",
            "biomarkers": ["EGFR+", "PD-L1 50%"], "bmi": 25.8,
            "comorbidities": ["asthma"], "ecog_ps": 1,
            "prior_therapies": ["carboplatin"],
        },
    }

    def __init__(
        self,
        base_url: str = "https://mock-fhir.hospital.org/baseR4",
        auth_token: str = "MOCK_BEARER_TOKEN",
        mock_latency_ms: int = 120,
        verbose: bool = False,
    ) -> None:
        self.base_url = base_url
        self.auth_token = auth_token
        self.mock_latency_ms = mock_latency_ms
        self._audit_log: list[str] = []

        # Build pre-extracted cache
        self._pre_extracted: dict[str, dict[str, Any]] = {}
        for pid, rec in self._FHIR_RECORDS.items():
            profile = self._fhir_record_to_profile(rec)
            self._pre_extracted[pid] = SyntheticData._profile_to_entities(
                profile)

        if verbose:
            safe_print(
                f"[MockFHIRAPI] Initialised — {len(self._FHIR_RECORDS)} "
                f"patients, latency {mock_latency_ms}ms"
            )

    def source_name(self) -> str:
        return f"MockFHIRAPI ({self.base_url})"

    def get_patient(self, patient_id: str) -> Optional[PatientProfile]:
        self._simulate_latency(f"GET /Patient/{patient_id}")
        record = self._FHIR_RECORDS.get(patient_id)
        if record is None:
            self._audit_log.append(f"404 NOT FOUND: {patient_id}")
            return None
        profile = self._fhir_record_to_profile(record)
        self._audit_log.append(f"200 OK: {patient_id}")
        return profile

    def get_all_patients(self) -> list[PatientProfile]:
        self._simulate_latency("GET /Patient?_count=100")
        return [self._fhir_record_to_profile(r)
                for r in self._FHIR_RECORDS.values()]

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

    def get_audit_log(self) -> list[str]:
        return list(self._audit_log)

    def _simulate_latency(self, endpoint: str) -> None:
        time.sleep(self.mock_latency_ms / 1000.0)
        self._audit_log.append(
            f"→ {endpoint} (+{self.mock_latency_ms}ms)")

    @staticmethod
    def _fhir_record_to_profile(record: dict) -> PatientProfile:
        profile = PatientProfile(
            patient_id=record["patient_id"],
            age=record["age"],
            gender=record["gender"],
            disease=record["disease"],
            stage=record["stage"],
            biomarkers=list(record.get("biomarkers", [])),
            bmi=record["bmi"],
            comorbidities=list(record.get("comorbidities", [])),
            ecog_ps=record["ecog_ps"],
            prior_therapies=list(record.get("prior_therapies", [])),
        )
        profile.ehr_note = SyntheticNoteGenerator.generate_note(profile)
        return profile
