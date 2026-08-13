"""Compose free-text clinical notes from structured provider rows."""

from __future__ import annotations

from datetime import date
from typing import Optional

from data_simulator import PatientProfile

from data_access.records import ConditionRecord, MedicationRecord

def compose_clinical_note(
    patient: PatientProfile,
    conditions: list[ConditionRecord],
    medications: list[MedicationRecord],
) -> str:
    """Build a free-text clinical note from structured provider data."""
    parts: list[str] = []

    if patient.age and patient.gender:
        parts.append(f"Patient is a {patient.age}-year-old {patient.gender}.")
    elif patient.age:
        parts.append(f"Patient age: {patient.age}.")

    if patient.disease or patient.stage:
        parts.append(
            f"Primary diagnosis: {patient.disease or 'unknown'}, "
            f"stage {patient.stage or 'unknown'}."
        )

    active = [c.description for c in conditions if c.description]
    if active:
        parts.append(f"Active conditions: {', '.join(active)}.")
    elif patient.comorbidities:
        parts.append(f"Comorbidities: {', '.join(patient.comorbidities)}.")

    if patient.biomarkers:
        parts.append(f"Biomarkers: {', '.join(patient.biomarkers)}.")

    if patient.bmi:
        parts.append(f"BMI: {patient.bmi}.")

    if patient.ecog_ps is not None:
        parts.append(f"ECOG performance status: {patient.ecog_ps}.")

    med_names = [m.description for m in medications if m.description]
    if med_names:
        parts.append(f"Medications / prior therapies: {', '.join(med_names)}.")
    elif patient.prior_therapies:
        parts.append(f"Prior therapies: {', '.join(patient.prior_therapies)}.")

    return " ".join(parts)

def _calc_age(birthdate: str, ref: Optional[date] = None) -> int:
    """Approximate age from ISO birthdate string."""
    ref = ref or date.today()
    try:
        parts = birthdate[:10].split("-")
        born = date(int(parts[0]), int(parts[1]), int(parts[2]))
        return ref.year - born.year - (
            (ref.month, ref.day) < (born.month, born.day)
        )
    except (ValueError, IndexError):
        return 0
