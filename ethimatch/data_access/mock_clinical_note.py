"""Synthesise BioBERT-ready clinical notes from unified profiles."""

from __future__ import annotations

from typing import Optional

from config import normalize_disease
from data_simulator import PatientProfile

# Common comorbidities the mock note explicitly states the patient does NOT have.
# Drives a "no history of …" sentence so BioBERT's negation filter is exercised.
_NEGATION_SCREEN: tuple[str, ...] = (
    "Diabetes",
    "Congestive heart failure",
    "COPD",
)

# Caps to keep the synthesised note compact (BioBERT input is bounded).
_MAX_CONDITIONS_IN_NOTE: int = 6
_MAX_MEDICATIONS_IN_NOTE: int = 6

# Suffixes Synthea uses for non-clinical social-determinants-of-health rows;
# we de-prioritise these so the note's bounded comorbidity slots are spent on
# real clinical findings (Diabetes, Anemia, etc.) instead of lifestyle entries.
_SOH_SUFFIXES: tuple[str, ...] = ("(finding)", "(situation)", "(qualifier value)")

def _is_clinical(description: str) -> bool:
    text = (description or "").strip().lower()
    return not any(text.endswith(sfx) for sfx in _SOH_SUFFIXES)

def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"

def _clean_list(items: list[str], cap: int) -> list[str]:
    """Trim and de-dupe a list while preserving order; cap for note length."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in items:
        text = (raw or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) >= cap:
            break
    return out

def _condition_matches_primary(description: str, primary: Optional[str]) -> bool:
    """Treat a raw condition string as a duplicate of the primary disease."""
    if not primary:
        return False
    text = (description or "").strip()
    if not text:
        return False
    if text.lower() == primary.lower():
        return True
    mapped = normalize_disease(text)
    if mapped and mapped.lower() == primary.lower():
        return True
    return False

def generate_mock_clinical_note(profile: PatientProfile) -> str:
    age = profile.age if isinstance(profile.age, int) and profile.age > 0 else None
    gender = (profile.gender or "patient").lower()
    if gender not in ("male", "female"):
        gender = "patient"

    primary = profile.disease
    raw_conditions = [
        c for c in (profile.active_conditions or [])
        if c and not _condition_matches_primary(c, primary)
    ]
    raw_conditions.sort(key=lambda c: 0 if _is_clinical(c) else 1)
    extra_conditions = _clean_list(raw_conditions, cap=_MAX_CONDITIONS_IN_NOTE)
    medications = _clean_list(list(profile.medications or []), cap=_MAX_MEDICATIONS_IN_NOTE)

    parts: list[str] = []

    opener_demo = (
        f"{age}-year-old {gender}" if age else f"{gender} patient"
    )
    if primary:
        parts.append(
            f"Patient is {_article(opener_demo)} {opener_demo} "
            f"presenting with active {primary}."
        )
    elif extra_conditions:
        parts.append(
            f"Patient is {_article(opener_demo)} {opener_demo} "
            f"presenting with active {extra_conditions[0]}."
        )
        extra_conditions = extra_conditions[1:]
    else:
        parts.append(
            f"Patient is {_article(opener_demo)} {opener_demo} "
            "presenting for routine evaluation."
        )

    if extra_conditions:
        parts.append(
            f"Active comorbidities include {', '.join(extra_conditions)}."
        )

    if medications:
        parts.append(
            f"Current medications include {', '.join(medications)}."
        )
    else:
        parts.append("No active medications recorded.")

    haystack = " ".join(
        [primary or ""]
        + [c for c in (profile.active_conditions or []) if c]
        + [c for c in (profile.comorbidities or []) if c]
        + [m for m in (profile.medications or []) if m]
        + [t for t in (profile.prior_therapies or []) if t]
    ).lower()
    absent = [c for c in _NEGATION_SCREEN if c.lower() not in haystack]
    if absent:
        parts.append(
            f"Patient has no history of {', '.join(absent)}."
        )

    return " ".join(parts)

def _stamp_mock_note(profile: PatientProfile) -> None:
    """Populate ``profile.ehr_note`` only when no real note exists.

    Real notes (e.g. an attached discharge summary) always take precedence —
    we never overwrite a clinician-authored text with a synthesised one.
    """
    if profile.ehr_note and profile.ehr_note.strip():
        return
    profile.ehr_note = generate_mock_clinical_note(profile)