"""Synthetic clinical profiles and EHR note generation."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

SEED = 42
random.seed(SEED)

@dataclass
class PatientProfile:
    patient_id: str
    age: Optional[int] = None
    gender: str = "unknown"
    disease: Optional[str] = None
    stage: Optional[str] = None
    biomarkers: list[str] = field(default_factory=list)
    bmi: Optional[float] = None
    comorbidities: list[str] = field(default_factory=list)
    ecog_ps: Optional[int] = None
    prior_therapies: list[str] = field(default_factory=list)
    ehr_note: str = ""
    active_conditions: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    data_source: str = "Synthea"

class SyntheticNoteGenerator:
    _AGE_PHRASES = [
        "Patient is a {age}-year-old {gender}",
        "{age}yo {gender} patient",
        "{gender}, age {age},",
        "This {age} y/o {gender}",
        "A {age}-yr-old {gender}",
    ]

    _DISEASE_PHRASES = [
        "diagnosed with Stage {stage} {disease}",
        "presenting with {disease}, stage {stage}",
        "with confirmed Stage {stage} {disease}",
        "who has stage {stage} {disease}",
        "found to have {disease} at stage {stage}",
    ]

    _BIOMARKER_PHRASES = [
        "Molecular testing shows {biomarkers}.",
        "Biomarker panel: {biomarkers}.",
        "Genomic profiling reveals {biomarkers}.",
        "Tumour markers: {biomarkers}.",
        "Next-gen sequencing: {biomarkers}.",
    ]

    _BMI_PHRASES = [
        "BMI is {bmi}.",
        "Body mass index: {bmi}.",
        "BMI recorded at {bmi}.",
        "Current BMI {bmi}.",
    ]

    _ECOG_PHRASES = [
        "ECOG performance status {ecog}.",
        "ECOG PS: {ecog}.",
        "Performance status (ECOG): {ecog}.",
        "Functional status: ECOG {ecog}.",
    ]

    _COMORBIDITY_PHRASES = [
        "Medical history includes {comorbidities}.",
        "PMH: {comorbidities}.",
        "Comorbidities: {comorbidities}.",
        "Past medical history notable for {comorbidities}.",
        "No significant comorbidities.",
    ]

    _THERAPY_PHRASES = [
        "Prior therapies include {therapies}.",
        "Previously treated with {therapies}.",
        "Has received {therapies} in the past.",
        "Treatment history: {therapies}.",
    ]

    @classmethod
    def generate_note(cls, profile: PatientProfile) -> str:
        parts: list[str] = []

        if profile.age is not None:
            parts.append(
                random.choice(cls._AGE_PHRASES).format(
                    age=profile.age, gender=profile.gender
                )
            )

        if profile.disease or profile.stage:
            parts.append(
                random.choice(cls._DISEASE_PHRASES).format(
                    stage=profile.stage or "unknown",
                    disease=profile.disease or "unknown",
                )
            )

        if profile.biomarkers:
            parts.append(
                random.choice(cls._BIOMARKER_PHRASES).format(
                    biomarkers=", ".join(profile.biomarkers)
                )
            )

        if profile.bmi is not None:
            parts.append(
                random.choice(cls._BMI_PHRASES).format(bmi=profile.bmi)
            )

        if profile.ecog_ps is not None:
            parts.append(
                random.choice(cls._ECOG_PHRASES).format(ecog=profile.ecog_ps)
            )

        if profile.comorbidities:
            parts.append(
                random.choice(cls._COMORBIDITY_PHRASES[:-1]).format(
                    comorbidities=", ".join(profile.comorbidities)
                )
            )
        else:
            parts.append(cls._COMORBIDITY_PHRASES[-1])

        if profile.prior_therapies:
            parts.append(
                random.choice(cls._THERAPY_PHRASES).format(
                    therapies=", ".join(profile.prior_therapies)
                )
            )

        return " ".join(parts)

def build_synthetic_patients(n: int = 8) -> list[PatientProfile]:
    cohort: list[PatientProfile] = [
        PatientProfile(
            patient_id="SYN-001",
            age=58,
            gender="male",
            disease="NSCLC",
            stage="IIIA",
            biomarkers=["EGFR+", "PD-L1 60%"],
            bmi=24.5,
            comorbidities=[],
            ecog_ps=1,
            prior_therapies=["carboplatin"],
        ),
        PatientProfile(
            patient_id="SYN-002",
            age=32,
            gender="female",
            disease="NSCLC",
            stage="IV",
            biomarkers=["ALK+", "PD-L1 90%"],
            bmi=28.0,
            comorbidities=["type 2 diabetes"],
            ecog_ps=0,
            prior_therapies=[],
        ),
        PatientProfile(
            patient_id="SYN-003",
            age=67,
            gender="male",
            disease="SCLC",
            stage="IV",
            biomarkers=["PD-L1 10%"],
            bmi=22.1,
            comorbidities=["COPD"],
            ecog_ps=2,
            prior_therapies=["cisplatin", "etoposide"],
        ),
        PatientProfile(
            patient_id="SYN-004",
            age=51,
            gender="female",
            disease="Breast Cancer",
            stage="IIB",
            biomarkers=["HER2+", "ER+", "PR-"],
            bmi=26.3,
            comorbidities=[],
            ecog_ps=0,
            prior_therapies=["tamoxifen"],
        ),
        PatientProfile(
            patient_id="SYN-005",
            age=45,
            gender="male",
            disease="NSCLC",
            stage="III",
            biomarkers=["EGFR+"],
            bmi=34.2,
            comorbidities=["hypertension"],
            ecog_ps=1,
            prior_therapies=["pembrolizumab"],
        ),
        PatientProfile(
            patient_id="SYN-006",
            age=73,
            gender="female",
            disease="NSCLC",
            stage="IV",
            biomarkers=["KRAS G12C", "PD-L1 50%"],
            bmi=19.8,
            comorbidities=["CHF", "atrial fibrillation"],
            ecog_ps=3,
            prior_therapies=["docetaxel", "nivolumab"],
        ),
        PatientProfile(
            patient_id="SYN-007",
            age=75,
            gender="female",
            disease="Breast Cancer",
            stage="III",
            biomarkers=["HER2-", "ER+", "PR+"],
            bmi=27.5,
            comorbidities=["osteoporosis"],
            ecog_ps=1,
            prior_therapies=["letrozole"],
        ),
        PatientProfile(
            patient_id="SYN-008",
            age=55,
            gender="male",
            disease="NSCLC",
            stage="IIIB",
            biomarkers=["EGFR+", "PD-L1 70%", "ALK-"],
            bmi=25.0,
            comorbidities=[],
            ecog_ps=0,
            prior_therapies=[],
        ),
    ]

    for patient in cohort[:n]:
        patient.ehr_note = SyntheticNoteGenerator.generate_note(patient)

    return cohort[:n]

def build_trial_criteria() -> list[dict[str, Any]]:
    from trial_registry import load_all_trials, trials_for_export

    loaded = load_all_trials()
    if not loaded:
        raise FileNotFoundError(
            "No trial protocols found. Add JSON files to the trials/ directory."
        )
    return trials_for_export(loaded)

def save_trials_json(
    trials: list[dict],
    path: str | Path = "data/trial_criteria.json",
) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(trials, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[DataSim] Saved {len(trials)} trial criteria -> {out}")
    return out

def save_patients_json(
    patients: list[PatientProfile],
    path: str | Path = "data/synthetic_patients.json",
) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = [asdict(p) for p in patients]
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[DataSim] Saved {len(patients)} patient profiles -> {out}")
    return out

def main() -> None:
    print("EthiMatch — Synthetic Data Generator")
    patients = build_synthetic_patients()
    trials = build_trial_criteria()

    for p in patients:
        print(f"\n{p.patient_id} ({p.disease}, Stage {p.stage})")
        print(f"  Note: {p.ehr_note}")

    for t in trials:
        print(f"\n{t['trial_id']}: {t['trial_name']}")
        print(f"  Diseases: {t['inclusion']['diseases']}")
        print(f"  Stages: {t['inclusion']['stages']}")
        print(f"  Age: {t['inclusion']['age_min']}–{t['inclusion']['age_max']}")

    save_trials_json(trials)
    save_patients_json(patients)
    print("\nData generation complete.\n")

if __name__ == "__main__":
    main()
