"""
EthiMatch — Scaled evaluation cohort generator (100–200+ patients).

Generates procedurally varied oncology profiles, synthetic EHR notes,
and programmatic gold-standard labels via the SymbolicValidator.
"""

from __future__ import annotations

import random
from typing import Any

from data_simulator import PatientProfile, SyntheticNoteGenerator, build_trial_criteria
from symbolic_validator import SymbolicValidator

DISEASES = ["NSCLC", "SCLC", "Breast Cancer", "Lung Cancer", "Colorectal Cancer"]
STAGES = ["I", "IA", "IB", "II", "IIA", "IIB", "III", "IIIA", "IIIB", "IV"]
BIOMARKERS = [
    "EGFR+", "EGFR-", "ALK+", "ALK-", "HER2+", "HER2-", "ER+", "ER-",
    "PR+", "PR-", "PD-L1 10%", "PD-L1 30%", "PD-L1 50%", "PD-L1 70%",
    "KRAS G12C", "BRAF V600E",
]
COMORBIDITIES = [
    [], ["type 2 diabetes"], ["hypertension"], ["COPD"], ["CHF"],
    ["type 2 diabetes", "hypertension"], ["osteoporosis"],
]
THERAPIES = [
    [], ["carboplatin"], ["pembrolizumab"], ["docetaxel"],
    ["nivolumab"], ["cisplatin"], ["trastuzumab"], ["tamoxifen"],
]

def profile_to_entities(p: PatientProfile) -> dict[str, Any]:
    """Convert structured profile to validator entity dict."""
    return {
        "age": p.age,
        "gender": p.gender,
        "disease": p.disease,
        "stage": p.stage,
        "biomarkers": list(p.biomarkers),
        "bmi": p.bmi,
        "ecog_ps": p.ecog_ps,
        "comorbidities": list(p.comorbidities),
        "prior_therapies": list(p.prior_therapies),
        "confidence_scores": {k: 1.0 for k in (
            "age", "gender", "disease", "stage", "bmi", "ecog_ps",
            "biomarkers", "comorbidities", "prior_therapies",
        )},
        "extraction_sources": {k: "gold" for k in (
            "age", "gender", "disease", "stage", "bmi", "ecog_ps",
            "biomarkers", "comorbidities", "prior_therapies",
        )},
        "negated_fields": [],
    }

def compute_gold_standard(
    patients: list[PatientProfile],
    trials: list[dict[str, Any]] | None = None,
    validator: SymbolicValidator | None = None,
) -> dict[str, dict[str, bool]]:
    """Derive gold labels from structured profiles + symbolic rules."""
    trials = trials or build_trial_criteria()
    validator = validator or SymbolicValidator()
    gold: dict[str, dict[str, bool]] = {}

    for p in patients:
        entities = profile_to_entities(p)
        gold[p.patient_id] = {}
        for trial in trials:
            report = validator.validate(entities, trial)
            # Definitively eligible only if eligible AND no inconclusive rules
            gold[p.patient_id][trial["trial_id"]] = (
                report.eligible and not report.is_conditionally_eligible
            )
    return gold

def build_scaled_cohort(n: int = 150, seed: int = 42) -> list[PatientProfile]:
    """Generate n procedurally varied patients with EHR notes."""
    random.seed(seed)
    cohort: list[PatientProfile] = []

    for i in range(1, n + 1):
        disease = random.choice(DISEASES)
        gender = "female" if disease == "Breast Cancer" else random.choice(["male", "female"])
        if disease == "Breast Cancer" and gender == "male":
            gender = "female"

        biomarkers = random.sample(BIOMARKERS, k=random.randint(0, 3))
        if disease == "Breast Cancer" and random.random() < 0.7:
            biomarkers = list(set(biomarkers + ["HER2+"]))

        p = PatientProfile(
            patient_id=f"EVAL-{i:03d}",
            age=random.randint(28, 82),
            gender=gender,
            disease=disease,
            stage=random.choice(STAGES),
            biomarkers=biomarkers,
            bmi=round(random.uniform(17.0, 38.0), 1),
            comorbidities=list(random.choice(COMORBIDITIES)),
            ecog_ps=random.randint(0, 3),
            prior_therapies=list(random.choice(THERAPIES)),
        )
        p.ehr_note = SyntheticNoteGenerator.generate_note(p)
        cohort.append(p)

    return cohort
