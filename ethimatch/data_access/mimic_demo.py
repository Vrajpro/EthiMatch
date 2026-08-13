"""MIMIC-IV Demo CSV provider with unified PatientProfile fields."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable, Optional

from config import DEFAULT_MIMIC_DIR, normalize_disease
from console import safe_print
from data_simulator import PatientProfile

from data_access.types import DEFAULT_MIMIC_DEMO_DIR, DataSource
from data_access.mock_clinical_note import generate_mock_clinical_note
from data_access.records import CarePlanRecord, ConditionRecord, MedicationRecord
from data_access.schemas import (
    MIMICAdmission,
    MIMICDiagnosis,
    MIMICDiagnosisDict,
    MIMICPatient,
    MIMICPrescription,
    MIMICProcedureDict,
)
from data_access.source_base import PatientDataSource

class MIMICDualSourceProvider(PatientDataSource):
    """MIMIC-IV Demo CSV provider implementing the unified ``PatientProfile``.

    Expected directory layout (the demo release ships each table inside its
    own subfolder)::

        data/mimic/
            patients.csv/patients.csv
            admissions.csv/admissions.csv
            diagnoses_icd.csv/diagnoses_icd.csv
            d_icd_diagnoses.csv/d_icd_diagnoses.csv
            d_icd_procedures.csv/d_icd_procedures.csv
            prescriptions.csv/prescriptions.csv

    The loader transparently accepts the flat layout (``data/mimic/patients.csv``)
    if present.
    """

    data_source: DataSource = "MIMIC"

    def __init__(
        self,
        data_dir: str | Path | None = None,
        limit: int | None = None,
        verbose: bool = False,
    ) -> None:
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_MIMIC_DEMO_DIR
        self.verbose = verbose
        self.limit = limit if (limit is None or limit > 0) else None

        self._patients: dict[str, PatientProfile] = {}
        self._conditions: dict[str, list[ConditionRecord]] = {}
        self._medications: dict[str, list[MedicationRecord]] = {}
        self._pre_extracted: dict[str, dict[str, Any]] = {}
        self._diagnosis_dict: dict[str, str] = {}
        self._procedure_dict: dict[str, str] = {}

        self._load()

    def _resolve_csv(self, name: str) -> Optional[Path]:
        flat = self.data_dir / f"{name}.csv"
        if flat.is_file():
            return flat
        nested = self.data_dir / f"{name}.csv" / f"{name}.csv"
        if nested.is_file():
            return nested
        gz = self.data_dir / f"{name}.csv.gz"
        if gz.is_file():
            return gz
        return None

    @staticmethod
    def _iter_rows(path: Path) -> Iterable[dict[str, Any]]:
        opener: Any
        if path.suffix == ".gz":
            import gzip

            opener = lambda: gzip.open(path, "rt", encoding="utf-8", errors="replace")
        else:
            opener = lambda: open(path, "rt", encoding="utf-8", errors="replace", newline="")
        with opener() as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                yield row

    def _load(self) -> None:
        diag_path = self._resolve_csv("d_icd_diagnoses")
        if diag_path:
            for row in self._iter_rows(diag_path):
                rec = MIMICDiagnosisDict.from_row(row)
                if rec:
                    self._diagnosis_dict[rec.icd_code] = rec.long_title

        proc_path = self._resolve_csv("d_icd_procedures")
        if proc_path:
            for row in self._iter_rows(proc_path):
                rec = MIMICProcedureDict.from_row(row)
                if rec:
                    self._procedure_dict[rec.icd_code] = rec.long_title

        self._load_patients()
        self._load_diagnoses()
        self._load_prescriptions()

        for pid in list(self._patients.keys()):
            self._finalise_profile(pid)

        if self.verbose:
            safe_print(
                f"[MIMIC] Loaded {len(self._patients)} patients from {self.data_dir}"
            )

    def _load_patients(self) -> None:
        path = self._resolve_csv("patients")
        if not path:
            raise FileNotFoundError(
                f"MIMIC patients.csv not found under {self.data_dir}"
            )
        admissions_by_subject = self._load_admission_years()

        for row in self._iter_rows(path):
            if self.limit is not None and len(self._patients) >= self.limit:
                break
            rec = MIMICPatient.from_row(row)
            if rec is None:
                continue
            pid = f"MIMIC-{rec.subject_id}"

            ref_year = admissions_by_subject.get(rec.subject_id, rec.anchor_year)
            try:
                age = max(0, int(rec.anchor_age) + (ref_year - rec.anchor_year))
            except (TypeError, ValueError):
                age = rec.anchor_age or 0

            gender = "female" if rec.gender.upper().startswith("F") else (
                "male" if rec.gender.upper().startswith("M") else "unknown"
            )

            profile = PatientProfile(patient_id=pid, age=age, gender=gender)
            profile.data_source = "MIMIC"
            self._patients[pid] = profile
            self._conditions[pid] = []
            self._medications[pid] = []

    def _load_admission_years(self) -> dict[int, int]:
        """Take each subject's most recent admit year as an anchor reference."""
        path = self._resolve_csv("admissions")
        years: dict[int, int] = {}
        if not path:
            return years
        for row in self._iter_rows(path):
            rec = MIMICAdmission.from_row(row)
            if rec is None:
                continue
            year = rec.admittime.year if rec.admittime else None
            if year is None:
                continue
            prev = years.get(rec.subject_id)
            if prev is None or year > prev:
                years[rec.subject_id] = year
        return years

    def _load_diagnoses(self) -> None:
        path = self._resolve_csv("diagnoses_icd")
        if not path:
            return
        for row in self._iter_rows(path):
            rec = MIMICDiagnosis.from_row(row)
            if rec is None:
                continue
            pid = f"MIMIC-{rec.subject_id}"
            if pid not in self._patients:
                continue
            description = self._diagnosis_dict.get(rec.icd_code) or self._procedure_dict.get(
                rec.icd_code
            )
            if not description:
                continue
            self._conditions[pid].append(
                ConditionRecord(
                    code=rec.icd_code,
                    description=description,
                    start_date=None,
                    stop_date=None,
                    patient_id=pid,
                )
            )

    def _load_prescriptions(self) -> None:
        path = self._resolve_csv("prescriptions")
        if not path:
            return
        seen: dict[str, set[str]] = {}
        for row in self._iter_rows(path):
            rec = MIMICPrescription.from_row(row)
            if rec is None:
                continue
            pid = f"MIMIC-{rec.subject_id}"
            if pid not in self._patients:
                continue
            key = rec.drug.lower()
            if key in seen.setdefault(pid, set()):
                continue
            seen[pid].add(key)
            self._medications[pid].append(
                MedicationRecord(
                    code="",
                    description=rec.drug,
                    start_date=rec.starttime.isoformat() if rec.starttime else None,
                    stop_date=rec.stoptime.isoformat() if rec.stoptime else None,
                    patient_id=pid,
                )
            )

    def _finalise_profile(self, pid: str) -> None:
        profile = self._patients[pid]
        conditions = self._conditions.get(pid, [])
        medications = self._medications.get(pid, [])

        # Active = no stop_date. MIMIC diagnoses have no stop date — treat as historical
        # condition list (clinically: encounter diagnoses are point-in-time).
        active_descriptions = [c.description for c in conditions if c.description]
        med_descriptions = [m.description for m in medications if m.description]

        # Map any oncology hits onto canonical disease codes (best-effort)
        primary_disease: Optional[str] = None
        comorbidities: list[str] = []
        for desc in active_descriptions:
            mapped = normalize_disease(desc)
            if mapped and primary_disease is None:
                primary_disease = mapped
            else:
                comorbidities.append(desc)

        profile.disease = primary_disease
        profile.comorbidities = comorbidities
        profile.prior_therapies = list(med_descriptions)
        profile.active_conditions = active_descriptions
        profile.medications = med_descriptions
        profile.data_source = "MIMIC"
        # Synthesise a BioBERT-ready note; override any earlier composed note.
        profile.ehr_note = generate_mock_clinical_note(profile)

        self._pre_extracted[pid] = self._profile_to_entities(profile)

    @staticmethod
    def _profile_to_entities(p: PatientProfile) -> dict[str, Any]:
        gender = p.gender if p.gender and p.gender.lower() != "unknown" else None
        return {
            "age": p.age,
            "gender": gender,
            "disease": p.disease,
            "stage": None,        # MIMIC-IV-Demo has no oncology staging
            "biomarkers": [],
            "bmi": None,
            "ecog_ps": None,
            "comorbidities": list(p.comorbidities),
            "prior_therapies": list(p.prior_therapies),
            "data_source": "MIMIC",
            "confidence_scores": {
                "age": 1.0, "gender": 1.0,
                "disease": 0.6 if p.disease else 0.0,
                "comorbidities": 1.0, "prior_therapies": 1.0,
            },
            "extraction_sources": {
                "age": "csv", "gender": "csv",
                "disease": "csv", "comorbidities": "csv", "prior_therapies": "csv",
            },
            "negated_fields": [],
        }

    def source_name(self) -> str:
        return f"MIMIC-IV Demo ({len(self._patients)} patients @ {self.data_dir})"

    def get_patient(self, patient_id: str) -> Optional[PatientProfile]:
        return self._patients.get(patient_id)

    def get_all_patients(self) -> list[PatientProfile]:
        return list(self._patients.values())

    def list_patient_ids(self) -> list[str]:
        return list(self._patients.keys())

    def get_conditions(self, patient_id: str) -> list[ConditionRecord]:
        return list(self._conditions.get(patient_id, []))

    def get_medications(self, patient_id: str) -> list[MedicationRecord]:
        return list(self._medications.get(patient_id, []))

    def get_careplans(self, patient_id: str) -> list[CarePlanRecord]:
        return []

    def get_pre_extracted(self, patient_id: str) -> Optional[dict[str, Any]]:
        return self._pre_extracted.get(patient_id)

    def get_all_pre_extracted(self) -> dict[str, dict[str, Any]]:
        return dict(self._pre_extracted)

    @staticmethod
    def is_available(data_dir: str | Path | None = None) -> bool:
        probe = MIMICDualSourceProvider.__new__(MIMICDualSourceProvider)
        probe.data_dir = Path(data_dir) if data_dir else DEFAULT_MIMIC_DEMO_DIR
        return probe._resolve_csv("patients") is not None