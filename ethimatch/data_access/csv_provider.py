"""Local Synthea / OMOP CSV patient provider."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from config import DISEASE_SYNONYM_MAPPING, normalize_disease
from console import safe_print
from data_simulator import PatientProfile

from data_access.note_composition import _calc_age, compose_clinical_note
from data_access.records import CarePlanRecord, ConditionRecord, MedicationRecord
from data_access.source_base import PatientDataSource

class RealCSVProvider(PatientDataSource):
    """Load patients, conditions, and medications from local CSV files.

    Expected files (Synthea / OMOP-style layout):
      data_dir/patients.csv
      data_dir/conditions.csv
      data_dir/medications.csv

    Critical rule: ``get_conditions`` returns ONLY active conditions —
    rows where the STOP column is null, NaN, or empty.

    Subclass locally as ``SyntheticCSVProvider`` to point at your paths::

        class SyntheticCSVProvider(RealCSVProvider):
            def __init__(self):
                super().__init__(data_dir="/path/to/your/csvs")
    """

    # Backward-compatible alias (SNOMED / free-text → internal code)
    DISEASE_MAPPING = DISEASE_SYNONYM_MAPPING

    @classmethod
    def map_disease(cls, description: str) -> Optional[str]:
        """Map a conditions.csv DESCRIPTION to internal trial disease code."""
        return normalize_disease(description)

    def __init__(
        self,
        data_dir: str | Path,
        patients_file: str = "patients.csv",
        conditions_file: str = "conditions.csv",
        medications_file: str = "medications.csv",
        careplans_file: str = "careplans.csv",
        notes_file: str | None = None,
        limit: int | None = None,
        verbose: bool = False,
    ) -> None:
        import pandas as pd

        self.data_dir = Path(data_dir)
        self.verbose = verbose
        self._patients: dict[str, PatientProfile] = {}
        self._conditions: dict[str, list[ConditionRecord]] = {}
        self._medications: dict[str, list[MedicationRecord]] = {}
        self._careplans: dict[str, list[CarePlanRecord]] = {}
        self._pre_extracted: dict[str, dict[str, Any]] = {}
        self._notes: dict[str, str] = {}
        self._oncology_stages: dict[str, str] = {}

        patients_path = self.data_dir / patients_file
        if not patients_path.exists():
            raise FileNotFoundError(f"patients CSV not found: {patients_path}")

        df_pat = pd.read_csv(patients_path, dtype=str, low_memory=False)
        id_col = self._resolve_column(df_pat.columns, ("id", "patient", "patient_id"))
        gender_col = self._resolve_column(df_pat.columns, ("gender", "sex"))
        birth_col = self._resolve_column(df_pat.columns, ("birthdate", "dob", "birth_date"))

        for i, row in df_pat.iterrows():
            if limit is not None and len(self._patients) >= limit:
                break
            pid = str(row[id_col]).strip()
            gender_raw = str(row.get(gender_col, "unknown")).strip().lower()
            gender = "female" if gender_raw.startswith("f") else (
                "male" if gender_raw.startswith("m") else gender_raw
            )
            age_raw = _calc_age(str(row.get(birth_col, ""))) if birth_col else None
            age = age_raw if age_raw else None

            profile = PatientProfile(
                patient_id=pid,
                age=age,
                gender=gender,
            )
            self._patients[pid] = profile
            self._conditions[pid] = []
            self._medications[pid] = []
            self._careplans[pid] = []

        self._load_conditions(self.data_dir / conditions_file)
        self._load_medications(self.data_dir / medications_file)
        self._load_careplans(self.data_dir / careplans_file)
        self._load_oncology_stages(self.data_dir / "observations.csv")

        if notes_file:
            self._load_notes(self.data_dir / notes_file)

        for pid, profile in self._patients.items():
            self._enrich_profile_from_rows(pid, profile)
            if pid in self._notes:
                profile.ehr_note = self._notes[pid]
            elif not profile.ehr_note:
                profile.ehr_note = compose_clinical_note(
                    profile,
                    self._conditions.get(pid, []),
                    self._medications.get(pid, []),
                )
            self._pre_extracted[pid] = self._profile_to_entities(profile)

        if verbose:
            safe_print(
                f"[RealCSVProvider] Loaded {len(self._patients)} patients "
                f"from {self.data_dir}"
            )

    @staticmethod
    def _resolve_column(columns: Any, candidates: tuple[str, ...]) -> str:
        lower_map = {str(c).lower(): c for c in columns}
        for cand in candidates:
            if cand in lower_map:
                return lower_map[cand]
        for col in columns:
            if any(cand in str(col).lower() for cand in candidates):
                return col
        raise KeyError(f"Could not find column among {candidates} in {list(columns)}")

    @staticmethod
    def _resolve_column_optional(columns: Any, candidates: tuple[str, ...]) -> str | None:
        try:
            return RealCSVProvider._resolve_column(columns, candidates)
        except KeyError:
            return None

    def _load_conditions(self, path: Path) -> None:
        if not path.exists():
            return
        import pandas as pd

        df = pd.read_csv(path, dtype=str, low_memory=False)
        pid_col = self._resolve_column(df.columns, ("patient", "patient_id", "id"))
        desc_col = self._resolve_column(df.columns, ("description", "desc"))
        code_col = self._resolve_column_optional(df.columns, ("code",))
        start_col = self._resolve_column_optional(df.columns, ("start", "start_date"))
        stop_col = self._resolve_column_optional(df.columns, ("stop", "stop_date"))

        for _, row in df.iterrows():
            pid = str(row[pid_col]).strip()
            if pid not in self._patients:
                continue

            # Active conditions only: STOP must be null / NaN / empty
            if stop_col is not None:
                stop_val = row.get(stop_col)
                if stop_val is not None and str(stop_val).strip().lower() not in (
                    "", "nan", "none", "nat",
                ):
                    continue

            record = ConditionRecord(
                code=str(row.get(code_col, "")) if code_col else "",
                description=str(row.get(desc_col, "")).strip(),
                start_date=str(row.get(start_col, "")) if start_col else None,
                stop_date=None,
                patient_id=pid,
            )
            if record.description:
                self._conditions.setdefault(pid, []).append(record)

    def _load_medications(self, path: Path) -> None:
        if not path.exists():
            return
        import pandas as pd

        df = pd.read_csv(path, dtype=str, low_memory=False)
        pid_col = self._resolve_column(df.columns, ("patient", "patient_id", "id"))
        desc_col = self._resolve_column(df.columns, ("description", "desc"))
        code_col = self._resolve_column_optional(df.columns, ("code",))
        start_col = self._resolve_column_optional(df.columns, ("start", "start_date"))
        stop_col = self._resolve_column_optional(df.columns, ("stop", "stop_date"))

        for _, row in df.iterrows():
            pid = str(row[pid_col]).strip()
            if pid not in self._patients:
                continue
            if stop_col is not None:
                stop_val = row.get(stop_col)
                if stop_val is not None and str(stop_val).strip().lower() not in (
                    "", "nan", "none", "nat",
                ):
                    continue
            record = MedicationRecord(
                code=str(row.get(code_col, "")) if code_col else "",
                description=str(row.get(desc_col, "")).strip(),
                start_date=str(row.get(start_col, "")) if start_col else None,
                stop_date=str(row.get(stop_col, "")) if stop_col else None,
                patient_id=pid,
            )
            if record.description:
                self._medications.setdefault(pid, []).append(record)

    def _load_careplans(self, path: Path) -> None:
        if not path.exists():
            return
        import pandas as pd

        df = pd.read_csv(path, dtype=str, low_memory=False)
        pid_col = self._resolve_column(df.columns, ("patient", "patient_id", "id"))
        desc_col = self._resolve_column(df.columns, ("description", "desc"))
        reason_col = self._resolve_column_optional(
            df.columns, ("reasondescription", "reason", "reason_description"),
        )
        code_col = self._resolve_column_optional(df.columns, ("code",))
        start_col = self._resolve_column_optional(df.columns, ("start", "start_date"))
        stop_col = self._resolve_column_optional(df.columns, ("stop", "stop_date"))

        for _, row in df.iterrows():
            pid = str(row[pid_col]).strip()
            if pid not in self._patients:
                continue

            if stop_col is not None:
                stop_val = row.get(stop_col)
                if stop_val is not None and str(stop_val).strip().lower() not in (
                    "", "nan", "none", "nat",
                ):
                    continue

            record = CarePlanRecord(
                code=str(row.get(code_col, "")) if code_col else "",
                description=str(row.get(desc_col, "")).strip(),
                reason=str(row.get(reason_col, "")).strip() if reason_col else "",
                start_date=str(row.get(start_col, "")) if start_col else None,
                stop_date=None,
                patient_id=pid,
            )
            if record.description:
                self._careplans.setdefault(pid, []).append(record)

    def _load_notes(self, path: Path) -> None:
        import pandas as pd

        df = pd.read_csv(path, dtype=str, low_memory=False)
        pid_col = self._resolve_column(df.columns, ("patient", "patient_id", "id", "note_id"))
        text_col = self._resolve_column(df.columns, ("text", "note", "ehr_note", "content"))
        for _, row in df.iterrows():
            pid = str(row[pid_col]).strip()
            text = str(row.get(text_col, "")).strip()
            if pid and text:
                self._notes[pid] = text

    def _load_oncology_stages(self, path: Path) -> None:
        """Index cancer stage observations (Synthea ``observations.csv``)."""
        self._oncology_stages = {}
        if not path.exists():
            return
        import pandas as pd
        from config import parse_oncology_stage_from_text

        try:
            header = pd.read_csv(path, nrows=0, dtype=str).columns
            pid_col = self._resolve_column_optional(header, ("patient", "patient_id", "id"))
            desc_col = self._resolve_column_optional(header, ("description", "desc"))
            val_col = self._resolve_column_optional(header, ("value",))
            if not pid_col or not desc_col:
                return
            usecols = [c for c in (pid_col, desc_col, val_col) if c]
        except (OSError, KeyError, ValueError):
            return

        for chunk in pd.read_csv(path, dtype=str, low_memory=False, usecols=usecols, chunksize=100_000):
            mask = chunk[desc_col].str.contains("stage group", case=False, na=False)
            if not mask.any():
                continue
            for _, row in chunk.loc[mask].iterrows():
                pid = str(row[pid_col]).strip()
                if pid not in self._patients:
                    continue
                value_text = str(row.get(val_col, "")) if val_col else ""
                desc_text = str(row.get(desc_col, ""))
                stage = parse_oncology_stage_from_text(value_text) or parse_oncology_stage_from_text(desc_text)
                if not stage:
                    continue
                prev = self._oncology_stages.get(pid)
                if prev is None or len(stage) > len(prev):
                    self._oncology_stages[pid] = stage

    def _infer_oncology_stage(self, pid: str, descriptions: list[str]) -> str | None:
        from config import parse_oncology_stage_from_text

        best: str | None = self._oncology_stages.get(pid)
        for desc in descriptions:
            stage = parse_oncology_stage_from_text(desc)
            if not stage:
                continue
            if best is None or len(stage) > len(best):
                best = stage
        return best

    def _enrich_profile_from_rows(self, pid: str, profile: PatientProfile) -> None:
        """Map condition/medication rows to profile fields with disease normalization."""
        conds = self._conditions.get(pid, [])
        meds = self._medications.get(pid, [])

        descriptions = [c.description for c in conds if c.description]
        primary_disease: str | None = None
        comorbidities: list[str] = []

        for desc in descriptions:
            mapped = self.map_disease(desc)
            if mapped and primary_disease is None:
                primary_disease = mapped
                continue
            comorbidities.append(desc)

        profile.disease = primary_disease
        profile.comorbidities = comorbidities
        profile.prior_therapies = [m.description for m in meds if m.description]
        profile.stage = self._infer_oncology_stage(pid, descriptions)

    @staticmethod
    def _profile_to_entities(p: PatientProfile) -> dict[str, Any]:
        """Convert CSV profile to entity dict — None for absent fields, not 0/Unknown."""
        gender = p.gender if p.gender and p.gender.lower() != "unknown" else None
        return {
            "age": p.age,
            "gender": gender,
            "disease": p.disease,
            "stage": p.stage,
            "biomarkers": list(p.biomarkers),
            "bmi": p.bmi,
            "ecog_ps": p.ecog_ps,
            "comorbidities": list(p.comorbidities),
            "prior_therapies": list(p.prior_therapies),
            "confidence_scores": {
                k: 1.0 for k in (
                    "age", "gender", "disease", "stage", "bmi", "ecog_ps",
                    "biomarkers", "comorbidities", "prior_therapies",
                )
            },
            "extraction_sources": {
                k: "csv" for k in (
                    "age", "gender", "disease", "stage", "bmi", "ecog_ps",
                    "biomarkers", "comorbidities", "prior_therapies",
                )
            },
            "negated_fields": [],
        }

    def source_name(self) -> str:
        return f"RealCSVProvider ({len(self._patients)} patients @ {self.data_dir})"

    def get_patient(self, patient_id: str) -> Optional[PatientProfile]:
        return self._patients.get(patient_id)

    def get_all_patients(self) -> list[PatientProfile]:
        return list(self._patients.values())

    def get_conditions(self, patient_id: str) -> list[ConditionRecord]:
        return list(self._conditions.get(patient_id, []))

    def get_medications(self, patient_id: str) -> list[MedicationRecord]:
        return list(self._medications.get(patient_id, []))

    def get_careplans(self, patient_id: str) -> list[CarePlanRecord]:
        return list(self._careplans.get(patient_id, []))

    def get_pre_extracted(self, patient_id: str) -> Optional[dict[str, Any]]:
        return self._pre_extracted.get(patient_id)

    def get_all_pre_extracted(self) -> dict[str, dict[str, Any]]:
        return dict(self._pre_extracted)

class SyntheticCSVProvider(RealCSVProvider):
    """Production CSV provider — point at your local dataset directory.

    Example::

        provider = SyntheticCSVProvider(data_dir=r\"C:\\data\\synthea\\csv\")
        pipeline = EthiMatchPipeline(data_provider=provider, verbose=False)
        report = pipeline.run_patient(\"<patient-uuid>\")
    """

    def __init__(self, data_dir: str | Path, **kwargs: Any) -> None:
        super().__init__(data_dir=data_dir, **kwargs)