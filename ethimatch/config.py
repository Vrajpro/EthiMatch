"""Clinical vocabulary, paths, and display labels for EthiMatch."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

ETHIMATCH_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ETHIMATCH_ROOT.parent

# Synthea / OMOP-style CSV folder (patients.csv, conditions.csv, medications.csv, …)
DEFAULT_CSV_DIR = PROJECT_ROOT / "data" / "synthea"

# MIMIC-IV Demo structured tables (patients, diagnoses, prescriptions, …)
DEFAULT_MIMIC_DIR = PROJECT_ROOT / "data" / "mimic"

# Optional cap for Streamlit registry load (None = all rows in patients.csv)
DEFAULT_CSV_UI_PATIENT_LIMIT: int = 100

# BioBERT batch screening (Patient Matching) — keep small for responsive UI
MATCHING_BIOBERT_BATCH_DEFAULT: int = 25
MATCHING_BIOBERT_BATCH_MAX: int = 100

# Evaluation tab — smaller default = faster interactive benchmarks
EVAL_BENCHMARK_PATIENTS_DEFAULT: int = 100
EVAL_BENCHMARK_PATIENTS_MAX: int = 500

# Sidebar presets for how many CSV rows to load into memory (0 = all rows)
CSV_REGISTRY_LIMIT_ALL: int = 0
CSV_REGISTRY_LIMIT_OPTIONS: list[int] = [50, 100, 200, 500, CSV_REGISTRY_LIMIT_ALL]

# Silver tier — materialized neural extractions (data/silver/*.json)
SILVER_DIR = ETHIMATCH_ROOT / "data" / "silver"

ALLOWED_DISEASES: list[str] = [
    "NSCLC",
    "SCLC",
    "Breast Cancer",
    "Lung Cancer",
    "Colorectal Cancer",
    "Pancreatic Cancer",
]

# User-friendly labels shown in Streamlit; backend always uses ALLOWED_DISEASES codes.
DISEASE_DISPLAY_LABELS: dict[str, str] = {
    "NSCLC": "Non-small cell lung cancer (NSCLC)",
    "SCLC": "Small cell lung cancer (SCLC)",
    "Breast Cancer": "Breast cancer",
    "Lung Cancer": "Lung cancer",
    "Colorectal Cancer": "Colorectal cancer",
    "Pancreatic Cancer": "Pancreatic cancer",
}

# SNOMED / Synthea / NER free-text → internal disease code
DISEASE_SYNONYM_MAPPING: dict[str, str] = {
    # SNOMED / Synthea condition DESCRIPTION (RealCSVProvider)
    "Non-small cell lung cancer (disorder)": "NSCLC",
    "Non-small cell lung cancer": "NSCLC",
    "Non-small cell carcinoma of lung (disorder)": "NSCLC",
    "Primary malignant neoplasm of lung (disorder)": "NSCLC",
    "Malignant neoplasm of lung (disorder)": "NSCLC",
    "Small cell lung cancer (disorder)": "SCLC",
    "Small cell lung cancer": "SCLC",
    "Breast cancer (disorder)": "Breast Cancer",
    "Breast cancer": "Breast Cancer",
    "Malignant neoplasm of breast (disorder)": "Breast Cancer",
    # NER / clinical-note phrases (matched case-insensitively in normalize_disease)
    "non-small cell lung cancer": "NSCLC",
    "non small cell lung cancer": "NSCLC",
    "nsclc": "NSCLC",
    "sclc": "SCLC",
    "small cell lung cancer": "SCLC",
    "breast cancer": "Breast Cancer",
    "lung cancer": "Lung Cancer",
    "colorectal cancer": "Colorectal Cancer",
    "pancreatic cancer": "Pancreatic Cancer",
}

ALLOWED_STAGES: list[str] = [
    "I", "IA", "IB",
    "II", "IIA", "IIB",
    "III", "IIIA", "IIIB",
    "IV",
]

COHORT_STAGE_DEFAULTS: list[str] = ["III", "IIIA", "IIIB", "IV"]

ECOG_LEVELS: list[int] = [0, 1, 2, 3, 4]
ECOG_MAX_LEVELS: list[int] = [0, 1, 2, 3]

GENDERS: list[str] = ["male", "female"]

BIOMARKERS: list[str] = [
    "EGFR+", "EGFR-",
    "ALK+", "ALK-",
    "HER2+", "HER2-",
    "ER+", "ER-",
    "PR+", "PR-",
    "PD-L1 50%", "PD-L1 60%", "PD-L1 70%",
    "KRAS G12C",
    "BRAF V600E",
]

COMORBIDITIES: list[str] = [
    "type 1 diabetes",
    "type 2 diabetes",
    "diabetes",
    "hypertension",
    "uncontrolled hypertension",
    "COPD",
    "CHF",
    "congestive heart failure",
    "atrial fibrillation",
    "uncontrolled cardiac arrhythmia",
    "osteoporosis",
    "CKD",
    "asthma",
    "coronary artery disease",
]

PRIOR_THERAPIES: list[str] = [
    "carboplatin",
    "cisplatin",
    "pembrolizumab",
    "nivolumab",
    "atezolizumab",
    "docetaxel",
    "paclitaxel",
    "etoposide",
    "tamoxifen",
    "letrozole",
    "trastuzumab",
    "doxorubicin",
    "bevacizumab",
    "pemetrexed",
    "gemcitabine",
    "fentanyl",
]

# Sensible Streamlit defaults (subset of master lists)
COHORT_DISEASE_DEFAULTS: list[str] = ["NSCLC"]
COHORT_EXCLUDED_COMORBIDITY_DEFAULTS: list[str] = ["type 2 diabetes", "COPD", "CHF"]
COHORT_EXCLUDED_THERAPY_DEFAULTS: list[str] = ["pembrolizumab", "docetaxel"]
COHORT_REQUIRED_BIOMARKER_OPTIONS: list[str] = ["EGFR+", "ALK+", "PD-L1 50%"]

AGE_MIN: int = 18
AGE_MAX: int = 95
BMI_MIN: float = 12.0
BMI_MAX: float = 60.0
BMI_COHORT_MAX_DEFAULT: float = 35.0

# Entity keys validated by SymbolicValidator (labels for low-confidence warnings)
ENTITY_FIELD_LABELS: dict[str, str] = {
    "age": "Age",
    "gender": "Gender",
    "disease": "Disease",
    "stage": "Stage",
    "bmi": "BMI",
    "ecog_ps": "ECOG",
    "biomarkers": "Biomarkers",
}

THEME: dict[str, dict[str, str]] = {
    "PASS": {
        "color": "#047857",
        "background": "#ECFDF5",
        "text": "#0F172A",
    },
    "INCONCLUSIVE": {
        "color": "#B45309",
        "background": "#FFFBEB",
        "text": "#0F172A",
    },
    "FAIL": {
        "color": "#B91C1C",
        "background": "#FEF2F2",
        "text": "#0F172A",
    },
    "NEUTRAL": {
        "color": "#1D4ED8",
        "background": "#EFF6FF",
        "text": "#0F172A",
    },
}

_VERDICT_THEME: dict[str, str] = {
    "Eligible": "PASS",
    "Inconclusive": "INCONCLUSIVE",
    "Conditional": "INCONCLUSIVE",
    "Ineligible": "FAIL",
    "Blocked": "FAIL",
}

def theme_token(verdict_label: str) -> str:
    """Map a clinician-facing verdict label to a THEME key."""
    return _VERDICT_THEME.get(verdict_label, "NEUTRAL")

def theme_colors(token: str) -> dict[str, str]:
    """Return color dict for a THEME token (PASS, INCONCLUSIVE, FAIL, NEUTRAL)."""
    return THEME.get(token, THEME["NEUTRAL"])

def theme_css_variables() -> str:
    """Emit CSS custom properties from THEME for injection in ui/theme.py."""
    lines: list[str] = []
    for key, palette in THEME.items():
        slug = key.lower()
        lines.append(f"  --status-{slug}: {palette['color']};")
        lines.append(f"  --status-{slug}-bg: {palette['background']};")
        lines.append(f"  --status-{slug}-text: {palette['text']};")
    return "\n".join(lines)

def disease_display_options() -> list[str]:
    """Return user-friendly disease labels for Streamlit selectboxes."""
    return [DISEASE_DISPLAY_LABELS.get(code, code) for code in ALLOWED_DISEASES]

def disease_code_from_display(label: str) -> Optional[str]:
    """Map a UI display label (or synonym) to an internal disease code."""
    for code in ALLOWED_DISEASES:
        if DISEASE_DISPLAY_LABELS.get(code, code) == label:
            return code
    return normalize_disease(label)

def disease_label_for_code(code: str) -> str:
    """Return the user-friendly label for an internal disease code."""
    return DISEASE_DISPLAY_LABELS.get(code, code)

def normalize_disease(description: str | None) -> Optional[str]:
    """Map SNOMED / free-text disease text to an internal ALLOWED_DISEASES code."""
    if not description or not str(description).strip():
        return None
    text = str(description).strip()
    if text in DISEASE_SYNONYM_MAPPING:
        return DISEASE_SYNONYM_MAPPING[text]
    if text in ALLOWED_DISEASES:
        return text
    lower = text.lower()
    for key, code in DISEASE_SYNONYM_MAPPING.items():
        if key.lower() == lower:
            return code
    # Substring fallback for SNOMED / note variants
    if "non-small cell" in lower and "lung" in lower:
        return "NSCLC"
    if "small cell" in lower and "lung" in lower:
        return "SCLC"
    if "breast" in lower and any(w in lower for w in ("cancer", "carcinoma", "neoplasm")):
        return "Breast Cancer"
    if "colorectal" in lower and "cancer" in lower:
        return "Colorectal Cancer"
    if "pancreatic" in lower and "cancer" in lower:
        return "Pancreatic Cancer"
    if "lung" in lower and "cancer" in lower:
        return "Lung Cancer"
    return None

def disease_filter_variants(code: str | None) -> frozenset[str]:
    """Expand a trial disease code to related CSV profile matches for cohort filters."""
    if not code:
        return frozenset()
    variants = {code}
    if code == "NSCLC":
        variants.add("Lung Cancer")
    elif code == "Lung Cancer":
        variants.update({"NSCLC", "SCLC", "Lung Cancer"})
    elif code == "SCLC":
        variants.add("Lung Cancer")
    return frozenset(variants)

def parse_oncology_stage_from_text(text: str | None) -> Optional[str]:
    """Map Synthea condition/observation text to an ``ALLOWED_STAGES`` code.

    Handles strings such as ``TNM stage 1`` and ``Stage 3A (qualifier value)``.
    Ignores non-oncology staging (e.g. CKD stage 1).
    """
    if not text or not str(text).strip():
        return None
    import re

    lower = str(text).strip().lower()
    oncology_ctx = any(
        token in lower
        for token in (
            "qualifier value",
            "tnm",
            "cancer",
            "carcinoma",
            "malignant",
            "neoplasm",
            "stage group",
            "lung",
            "breast",
            "nsclc",
            "sclc",
        )
    )
    if not oncology_ctx:
        return None

    m = re.search(r"stage\s+(\d+)\s*([abc])\b", lower)
    if m:
        num, letter = int(m.group(1)), m.group(2).upper()
        roman = {1: "I", 2: "II", 3: "III", 4: "IV"}.get(num)
        if roman:
            return normalize_stage(roman + letter)

    m = re.search(r"(?:tnm\s+)?stage\s+(\d+)\b", lower)
    if m:
        num = int(m.group(1))
        roman = {1: "I", 2: "II", 3: "III", 4: "IV"}.get(num)
        if roman:
            return normalize_stage(roman)

    m = re.search(r"\bstage\s+(iv|iii[ab]?|ii[ab]?|i[ab]?)\b", lower)
    if m:
        token = m.group(1).upper().replace(" ", "")
        return normalize_stage(token)

    return None

def normalize_stage(value: str | None) -> Optional[str]:
    """Return stage if it is a known ALLOWED_STAGES value."""
    if not value or not str(value).strip():
        return None
    text = str(value).strip().upper()
    # Roman numerals from regex (already uppercase)
    for stage in ALLOWED_STAGES:
        if stage.upper() == text:
            return stage
    return None

def normalize_gender(value: str | None) -> Optional[str]:
    if not value:
        return None
    lower = str(value).strip().lower()
    if lower in ("male", "m", "man"):
        return "male"
    if lower in ("female", "f", "woman"):
        return "female"
    if lower in GENDERS:
        return lower
    return None

def sanitize_list_values(values: list[Any] | None, allowed: list[str]) -> list[str]:
    """Keep only values present in *allowed* (exact match, preserves order)."""
    if not values:
        return []
    allowed_set = set(allowed)
    out: list[str] = []
    for v in values:
        if isinstance(v, str) and v in allowed_set and v not in out:
            out.append(v)
    return out

def sanitize_trial_criteria(trial: dict[str, Any]) -> dict[str, Any]:
    """Normalize inclusion/exclusion disease lists to internal codes."""
    trial = dict(trial)
    inclusion = dict(trial.get("inclusion") or {})
    exclusion = dict(trial.get("exclusion") or {})

    diseases = inclusion.get("diseases")
    if isinstance(diseases, list):
        inclusion["diseases"] = [
            normalize_disease(d) or d for d in diseases
            if (normalize_disease(d) or d) in ALLOWED_DISEASES
        ]

    stages = inclusion.get("stages")
    if isinstance(stages, list):
        inclusion["stages"] = sanitize_list_values(stages, ALLOWED_STAGES)

    gender = inclusion.get("gender")
    if isinstance(gender, list):
        inclusion["gender"] = sanitize_list_values(gender, GENDERS)

    req_bio = inclusion.get("required_biomarkers")
    if isinstance(req_bio, list):
        inclusion["required_biomarkers"] = sanitize_list_values(req_bio, BIOMARKERS)

    excl_comorb = exclusion.get("excluded_comorbidities")
    if isinstance(excl_comorb, list):
        exclusion["excluded_comorbidities"] = sanitize_list_values(excl_comorb, COMORBIDITIES)

    excl_rx = exclusion.get("excluded_prior_therapies")
    if isinstance(excl_rx, list):
        exclusion["excluded_prior_therapies"] = sanitize_list_values(excl_rx, PRIOR_THERAPIES)

    trial["inclusion"] = inclusion
    trial["exclusion"] = exclusion
    return trial
