"""Comparative evaluation harness and metrics export."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

sys.path.insert(0, str(Path(__file__).resolve().parent))

import console  # noqa: F401 — UTF-8 stdout on Windows
from console import json_dumps, safe_print
from data_interface import PatientDataProvider
from data_simulator import (
    PatientProfile,
    SyntheticNoteGenerator,
    build_trial_criteria,
)
from evaluation_cohort import compute_gold_standard
from mock_database import RealCSVProvider, get_default_csv_provider
from neural_extractor import NeuralExtractor
from symbolic_validator import SymbolicValidator, ValidationReport
from xai_explainer import build_clinical_narrative

from config import DEFAULT_CSV_DIR
from ethimatch_pipeline import try_structured_early_exit
from silver_cache import load_silver_entities, save_silver_entities

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "results" / "evaluation_metrics.json"
_BENCHMARK_EXTRACTOR: NeuralExtractor | None = None

DeltaLabel = Literal["TP", "TN", "FP", "FN", "INCONCLUSIVE"]
VerdictLabel = Literal["ELIGIBLE", "INELIGIBLE", "INCONCLUSIVE"]

#  Legacy 20-patient cohort (backward compatible)

def build_evaluation_cohort() -> list[PatientProfile]:
    """Hand-crafted 20-patient cohort with deterministic gold labels."""
    cohort: list[PatientProfile] = [
        PatientProfile(
            patient_id="EVAL-001", age=55, gender="male",
            disease="NSCLC", stage="IIIA",
            biomarkers=["EGFR+", "PD-L1 60%"], bmi=24.5,
            comorbidities=[], ecog_ps=1, prior_therapies=["carboplatin"],
        ),
        PatientProfile(
            patient_id="EVAL-002", age=62, gender="female",
            disease="NSCLC", stage="IV",
            biomarkers=["ALK+", "PD-L1 80%"], bmi=26.0,
            comorbidities=[], ecog_ps=0, prior_therapies=[],
        ),
        PatientProfile(
            patient_id="EVAL-003", age=71, gender="male",
            disease="NSCLC", stage="IIIB",
            biomarkers=["KRAS G12C", "PD-L1 30%"], bmi=22.1,
            comorbidities=["COPD"], ecog_ps=2, prior_therapies=["docetaxel"],
        ),
        PatientProfile(
            patient_id="EVAL-004", age=45, gender="female",
            disease="NSCLC", stage="III",
            biomarkers=["EGFR-", "PD-L1 50%"], bmi=30.0,
            comorbidities=["type 2 diabetes"], ecog_ps=1,
            prior_therapies=[],
        ),
        PatientProfile(
            patient_id="EVAL-005", age=78, gender="male",
            disease="NSCLC", stage="IV",
            biomarkers=["PD-L1 70%"], bmi=21.0,
            comorbidities=["CHF"], ecog_ps=1,
            prior_therapies=["nivolumab"],
        ),
        PatientProfile(
            patient_id="EVAL-006", age=52, gender="male",
            disease="NSCLC", stage="IIIA",
            biomarkers=["BRAF V600E", "PD-L1 20%"], bmi=27.5,
            comorbidities=[], ecog_ps=1, prior_therapies=[],
        ),
        PatientProfile(
            patient_id="EVAL-007", age=35, gender="female",
            disease="NSCLC", stage="IV",
            biomarkers=["EGFR+", "ALK-"], bmi=34.2,
            comorbidities=["hypertension"], ecog_ps=3,
            prior_therapies=["pembrolizumab"],
        ),
        PatientProfile(
            patient_id="EVAL-008", age=60, gender="male",
            disease="NSCLC", stage="IIIB",
            biomarkers=["PD-L1 90%"], bmi=23.0,
            comorbidities=[], ecog_ps=0, prior_therapies=[],
        ),
        PatientProfile(
            patient_id="EVAL-009", age=49, gender="female",
            disease="Breast Cancer", stage="IIB",
            biomarkers=["HER2+", "ER+", "PR-"], bmi=26.3,
            comorbidities=[], ecog_ps=0, prior_therapies=["tamoxifen"],
        ),
        PatientProfile(
            patient_id="EVAL-010", age=58, gender="female",
            disease="Breast Cancer", stage="III",
            biomarkers=["HER2+", "ER-"], bmi=29.0,
            comorbidities=[], ecog_ps=1, prior_therapies=["trastuzumab"],
        ),
        PatientProfile(
            patient_id="EVAL-011", age=76, gender="female",
            disease="Breast Cancer", stage="II",
            biomarkers=["HER2+", "PR+"], bmi=28.5,
            comorbidities=["osteoporosis"], ecog_ps=1, prior_therapies=[],
        ),
        PatientProfile(
            patient_id="EVAL-012", age=41, gender="female",
            disease="Breast Cancer", stage="IV",
            biomarkers=["HER2-", "ER+", "PR+"], bmi=23.0,
            comorbidities=[], ecog_ps=0, prior_therapies=[],
        ),
        PatientProfile(
            patient_id="EVAL-013", age=54, gender="female",
            disease="Breast Cancer", stage="IIIA",
            biomarkers=["HER2+"], bmi=31.0,
            comorbidities=["CHF"], ecog_ps=0,
            prior_therapies=["doxorubicin"],
        ),
        PatientProfile(
            patient_id="EVAL-014", age=67, gender="female",
            disease="Breast Cancer", stage="IIA",
            biomarkers=["HER2+", "ER-"], bmi=25.5,
            comorbidities=[], ecog_ps=1, prior_therapies=[],
        ),
        PatientProfile(
            patient_id="EVAL-015", age=65, gender="male",
            disease="SCLC", stage="IV",
            biomarkers=["PD-L1 10%"], bmi=22.0,
            comorbidities=["COPD"], ecog_ps=2,
            prior_therapies=["cisplatin", "etoposide"],
        ),
        PatientProfile(
            patient_id="EVAL-016", age=57, gender="male",
            disease="Colorectal Cancer", stage="III",
            biomarkers=["KRAS G12C"], bmi=27.0,
            comorbidities=[], ecog_ps=1, prior_therapies=["bevacizumab"],
        ),
        PatientProfile(
            patient_id="EVAL-017", age=44, gender="female",
            disease="Pancreatic Cancer", stage="IV",
            biomarkers=[], bmi=20.0,
            comorbidities=[], ecog_ps=2, prior_therapies=["gemcitabine"],
        ),
        PatientProfile(
            patient_id="EVAL-018", age=80, gender="male",
            disease="NSCLC", stage="IIIA",
            biomarkers=["EGFR+", "PD-L1 40%"], bmi=19.0,
            comorbidities=[], ecog_ps=2,
            prior_therapies=["carboplatin"],
        ),
        PatientProfile(
            patient_id="EVAL-019", age=55, gender="female",
            disease="Breast Cancer", stage="III",
            biomarkers=["HER2+", "ER+", "PR+"], bmi=23.5,
            comorbidities=[], ecog_ps=0, prior_therapies=[],
        ),
        PatientProfile(
            patient_id="EVAL-020", age=63, gender="male",
            disease="NSCLC", stage="IV",
            biomarkers=["EGFR+", "PD-L1 55%"], bmi=25.0,
            comorbidities=[], ecog_ps=1, prior_therapies=[],
        ),
    ]
    for p in cohort:
        p.ehr_note = SyntheticNoteGenerator.generate_note(p)
    return cohort

LEGACY_GOLD_STANDARD: dict[str, dict[str, bool]] = {
    "EVAL-001": {"NCT-FAKE-001": True,  "NCT-FAKE-002": False},
    "EVAL-002": {"NCT-FAKE-001": True,  "NCT-FAKE-002": False},
    "EVAL-003": {"NCT-FAKE-001": True,  "NCT-FAKE-002": False},
    "EVAL-004": {"NCT-FAKE-001": False, "NCT-FAKE-002": False},
    "EVAL-005": {"NCT-FAKE-001": False, "NCT-FAKE-002": False},
    "EVAL-006": {"NCT-FAKE-001": True,  "NCT-FAKE-002": False},
    "EVAL-007": {"NCT-FAKE-001": False, "NCT-FAKE-002": False},
    "EVAL-008": {"NCT-FAKE-001": True,  "NCT-FAKE-002": False},
    "EVAL-009": {"NCT-FAKE-001": False, "NCT-FAKE-002": True},
    "EVAL-010": {"NCT-FAKE-001": False, "NCT-FAKE-002": True},
    "EVAL-011": {"NCT-FAKE-001": False, "NCT-FAKE-002": False},
    "EVAL-012": {"NCT-FAKE-001": False, "NCT-FAKE-002": False},
    "EVAL-013": {"NCT-FAKE-001": False, "NCT-FAKE-002": False},
    "EVAL-014": {"NCT-FAKE-001": False, "NCT-FAKE-002": True},
    "EVAL-015": {"NCT-FAKE-001": False, "NCT-FAKE-002": False},
    "EVAL-016": {"NCT-FAKE-001": False, "NCT-FAKE-002": False},
    "EVAL-017": {"NCT-FAKE-001": False, "NCT-FAKE-002": False},
    "EVAL-018": {"NCT-FAKE-001": True,  "NCT-FAKE-002": False},
    "EVAL-019": {"NCT-FAKE-001": False, "NCT-FAKE-002": True},
    "EVAL-020": {"NCT-FAKE-001": True,  "NCT-FAKE-002": False},
}

# Backward-compatible alias (Streamlit Evaluation page, external imports)
GOLD_STANDARD = LEGACY_GOLD_STANDARD

#  Metrics

@dataclass
class TrialMetrics:
    trial_id:     str
    trial_name:   str
    tp: int = 0
    tn: int = 0
    fp: int = 0
    fn: int = 0
    inconclusive: int = 0

    @property
    def total(self) -> int:
        return self.tp + self.tn + self.fp + self.fn

    @property
    def accuracy(self) -> float:
        return (self.tp + self.tn) / self.total if self.total else 0.0

    @property
    def precision(self) -> float:
        d = self.tp + self.fp
        return self.tp / d if d else 0.0

    @property
    def recall(self) -> float:
        d = self.tp + self.fn
        return self.tp / d if d else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    @property
    def specificity(self) -> float:
        d = self.tn + self.fp
        return self.tn / d if d else 0.0

    @property
    def fpr(self) -> float:
        d = self.tn + self.fp
        return self.fp / d if d else 0.0

def compute_metrics(
    predictions: dict[str, dict[str, bool]],
    gold: dict[str, dict[str, bool]],
    trials: list[dict[str, Any]],
    inconclusive_map: dict[str, dict[str, bool]],
) -> list[TrialMetrics]:
    trial_name_map = {t["trial_id"]: t["trial_name"] for t in trials}
    metrics_map = {
        t["trial_id"]: TrialMetrics(t["trial_id"], trial_name_map.get(t["trial_id"], t["trial_id"]))
        for t in trials
    }

    for patient_id, gold_verdicts in gold.items():
        pred_verdicts = predictions.get(patient_id, {})
        cond_verdicts = inconclusive_map.get(patient_id, {})

        for trial_id, gold_eligible in gold_verdicts.items():
            m = metrics_map.get(trial_id)
            if m is None:
                continue
            pred = pred_verdicts.get(trial_id)
            if pred is None:
                continue
            if cond_verdicts.get(trial_id, False):
                m.inconclusive += 1
                continue
            if pred and gold_eligible:
                m.tp += 1
            elif not pred and not gold_eligible:
                m.tn += 1
            elif pred and not gold_eligible:
                m.fp += 1
            else:
                m.fn += 1

    return list(metrics_map.values())

def macro_average(metrics_list: list[TrialMetrics]) -> dict[str, float]:
    if not metrics_list:
        return {"accuracy": 0, "precision": 0, "recall": 0, "f1": 0, "specificity": 0, "fpr": 0}
    n = len(metrics_list)
    return {
        "accuracy": sum(m.accuracy for m in metrics_list) / n,
        "precision": sum(m.precision for m in metrics_list) / n,
        "recall": sum(m.recall for m in metrics_list) / n,
        "f1": sum(m.f1 for m in metrics_list) / n,
        "specificity": sum(m.specificity for m in metrics_list) / n,
        "fpr": sum(m.fpr for m in metrics_list) / n,
    }

def mcnemar_test(
    gold: dict[str, dict[str, bool]],
    pred_a: dict[str, dict[str, bool]],
    pred_b: dict[str, dict[str, bool]],
    trial_ids: list[str],
) -> dict[str, Any]:
    """McNemar's test: is EthiMatch significantly better than baseline?"""
    b_count = 0  # A correct, B wrong
    c_count = 0  # A wrong, B correct

    for pid, gold_trials in gold.items():
        for tid in trial_ids:
            g = gold_trials.get(tid)
            if g is None:
                continue
            a = pred_a.get(pid, {}).get(tid)
            bb = pred_b.get(pid, {}).get(tid)
            if a is None or bb is None:
                continue
            a_ok = a == g
            b_ok = bb == g
            if a_ok and not b_ok:
                b_count += 1
            elif not a_ok and b_ok:
                c_count += 1

    # Chi-square with continuity correction (df=1)
    if b_count + c_count == 0:
        chi2, p_value = 0.0, 1.0
    else:
        chi2 = (abs(b_count - c_count) - 1) ** 2 / (b_count + c_count)
        from math import erfc, sqrt
        p_value = erfc(sqrt(chi2 / 2))

    return {
        "ethimatch_correct_baseline_wrong": b_count,
        "ethimatch_wrong_baseline_correct": c_count,
        "chi2": round(chi2, 4),
        "p_value_approx": round(p_value, 4),
        "significant_at_0.05": p_value < 0.05,
    }

#  Pipeline helpers

def run_pipeline_on_note(
    note: str,
    extractor: NeuralExtractor,
    validator: SymbolicValidator,
    trials: list[dict[str, Any]],
) -> tuple[dict[str, bool], dict[str, bool]]:
    entities = extractor.extract(note, silent=True).to_dict()
    reports = validator.validate_all_trials(entities, trials)
    verdict_map = {r.trial_id: r.eligible for r in reports}
    conditional_map = {r.trial_id: r.is_conditionally_eligible for r in reports}
    return verdict_map, conditional_map

def _bar(value: float, width: int = 30) -> str:
    filled = int(value * width)
    return f"[{'#' * filled}{'.' * (width - filled)}] {value:.1%}"

def print_header(text: str, char: str = "=", width: int = 68) -> None:
    safe_print("\n" + char * width)
    safe_print(f"  {text}")
    safe_print(char * width)

def print_trial_metrics(m: TrialMetrics) -> None:
    safe_print(f"\n  --- {m.trial_id}: {m.trial_name}")
    safe_print(f"  Accuracy   : {_bar(m.accuracy)}")
    safe_print(f"  Precision  : {_bar(m.precision)}")
    safe_print(f"  Recall     : {_bar(m.recall)}")
    safe_print(f"  F1-Score   : {_bar(m.f1)}")
    safe_print(f"  Specificity: {_bar(m.specificity)}")
    safe_print(f"  FPR        : {_bar(m.fpr)}")
    safe_print(f"  Inconclusive (excluded): {m.inconclusive}")

def load_patients(args: argparse.Namespace) -> list[PatientProfile]:
    if args.legacy:
        return build_evaluation_cohort()
    provider = load_csv_provider(Path(args.csv_dir), limit=args.n_patients)
    return provider.get_all_patients()

def load_gold(
    patients: list[PatientProfile],
    trials: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, dict[str, bool]] | None:
    if args.skip_gold:
        return None
    if args.gold_file:
        path = Path(args.gold_file)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        safe_print(f"[Eval] WARN: gold file not found: {path}")
        return None
    if args.legacy:
        return LEGACY_GOLD_STANDARD
    return compute_gold_standard(patients, trials)

#  CSV dissertation evaluation (Neural Extractor vs Symbolic gold)

def verdict_label(report: ValidationReport) -> VerdictLabel:
    if report.is_conditionally_eligible:
        return "INCONCLUSIVE"
    if report.eligible:
        return "ELIGIBLE"
    return "INELIGIBLE"

def definitive_eligible(report: ValidationReport) -> bool:
    """Binary eligibility excluding inconclusive (conditional) verdicts."""
    return report.eligible and not report.is_conditionally_eligible

def compute_eligibility_delta(
    pred_report: ValidationReport,
    gold_report: ValidationReport,
) -> DeltaLabel:
    if pred_report.is_conditionally_eligible:
        return "INCONCLUSIVE"
    pred = definitive_eligible(pred_report)
    gold = definitive_eligible(gold_report)
    if pred and gold:
        return "TP"
    if not pred and not gold:
        return "TN"
    if pred and not gold:
        return "FP"
    return "FN"

def aggregate_delta_counts(deltas: list[DeltaLabel]) -> dict[str, int]:
    counts = {"TP": 0, "TN": 0, "FP": 0, "FN": 0, "INCONCLUSIVE": 0}
    for d in deltas:
        counts[d] += 1
    return counts

def compute_classifier_metrics(counts: dict[str, int]) -> dict[str, float]:
    tp, tn, fp, fn = counts["TP"], counts["TN"], counts["FP"], counts["FN"]
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    fpr_denom = fp + tn
    fpr = fp / fpr_denom if fpr_denom else 0.0
    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "fpr": round(fpr, 4),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "inconclusive": counts["INCONCLUSIVE"],
        "total_definitive": total,
    }

def pure_neural_eligibility(entities: dict[str, Any], trial: dict[str, Any]) -> bool:
    """Loose eligibility from extracted entities only — no symbolic safety layer.

    Mimics a pure neural / LLM-style matcher: partial fields and missing data
    often treated as pass, with no INCONCLUSIVE guardrails.
    """
    from baseline_llm import HeuristicLLMBaseline

    note_parts = []
    age = entities.get("age")
    if age is not None:
        note_parts.append(f"{age}-year-old")
    gender = entities.get("gender")
    if gender:
        note_parts.append(str(gender))
    disease = entities.get("disease")
    if disease:
        note_parts.append(str(disease))
    stage = entities.get("stage")
    if stage:
        note_parts.append(f"stage {stage}")
    for bio in entities.get("biomarkers") or []:
        note_parts.append(str(bio))
    bmi = entities.get("bmi")
    if bmi is not None:
        note_parts.append(f"bmi {bmi}")
    ecog = entities.get("ecog_ps")
    if ecog is not None:
        note_parts.append(f"ecog {ecog}")
    for c in entities.get("comorbidities") or []:
        note_parts.append(str(c))
    for rx in entities.get("prior_therapies") or []:
        note_parts.append(str(rx))

    note = " ".join(note_parts) or "unknown patient"
    baseline = HeuristicLLMBaseline()
    return baseline.predict_patient(note, [trial]).get(trial["trial_id"], False)

def is_mimic_benchmark_available(mimic_dir: Path | None = None) -> bool:
    """True when the MIMIC-IV-Demo structured CSVs are present locally.

    Checks the dual-source provider that powers the live UI (reads from the
    ``data/mimic/`` directory), not the older note-only fallback that requires
    credentialed MIMIC-IV-Note downloads.
    """
    try:
        from data_loader import MIMICDualSourceProvider

        return MIMICDualSourceProvider.is_available(mimic_dir)
    except Exception:
        return False

def get_benchmark_extractor() -> NeuralExtractor:
    """Reuse one BioBERT instance across benchmark runs (faster dashboard eval)."""
    global _BENCHMARK_EXTRACTOR
    if _BENCHMARK_EXTRACTOR is None:
        _BENCHMARK_EXTRACTOR = NeuralExtractor(device=-1, verbose=False)
    return _BENCHMARK_EXTRACTOR

def _entities_for_csv_benchmark(
    pid: str,
    note: str,
    provider: PatientDataProvider,
    extractor: NeuralExtractor,
    validator: SymbolicValidator,
    trials: list[dict[str, Any]],
) -> dict[str, Any]:
    """Silver cache → structured early exit → BioBERT (then persist silver)."""
    cached = load_silver_entities(pid)
    if cached is not None:
        return cached

    pre = provider.get_pre_extracted(pid) or {}
    skip, _, _reason = try_structured_early_exit(pre, validator, trials)
    if skip and pre:
        return pre

    if not (note or "").strip():
        return pre

    entities = extractor.extract(note, silent=True).to_dict()
    try:
        save_silver_entities(pid, entities)
    except OSError:
        pass
    return entities

def run_comparative_benchmark(
    *,
    data_source: Literal["synthetic", "csv", "mimic"] = "csv",
    n_patients: int = 20,
    csv_dir: str | Path | None = None,
    mimic_dir: str | Path | None = None,
    seed: int = 42,
) -> dict[str, Any]:
    """Compare Neuro-Symbolic (BioBERT + rules) vs Pure Neural (BioBERT + heuristic).

    Returns macro precision, recall, and FPR suitable for dashboard Plotly charts.
    """
    from evaluation_cohort import build_scaled_cohort, compute_gold_standard

    trials = build_trial_criteria()
    extractor = get_benchmark_extractor()
    validator = SymbolicValidator()

    if data_source == "synthetic":
        patients = build_scaled_cohort(n=n_patients, seed=seed)
        gold = compute_gold_standard(patients, trials, validator)
        provider = None
    elif data_source == "mimic":
        # Use the same dual-source provider that powers the live UI — reads the
        # real MIMIC-IV-Demo CSVs from ``data/mimic/`` and synthesises ehr_note
        # consistently with the production pipeline.
        if not is_mimic_benchmark_available(
            Path(mimic_dir) if mimic_dir else None,
        ):
            raise FileNotFoundError(
                "MIMIC-IV-Demo CSVs not found. Expected patients.csv under the "
                "data/mimic/ directory (or pass --mimic-dir)."
            )
        from data_loader import load_provider

        provider = load_provider(
            "MIMIC",
            limit=n_patients,
            data_dir=Path(mimic_dir) if mimic_dir else None,
            verbose=False,
        )
        patients = provider.get_all_patients()
        gold = compute_gold_standard(patients, trials, validator)
    else:
        provider = load_csv_provider(Path(csv_dir or DEFAULT_CSV_DIR), n_patients)
        patients = provider.get_all_patients()
        gold = {}
        for p in patients:
            pre = provider.get_pre_extracted(p.patient_id) or {}
            gold[p.patient_id] = {}
            for trial in trials:
                report = validator.validate(pre, trial)
                gold[p.patient_id][trial["trial_id"]] = definitive_eligible(report)

    neuro_preds: dict[str, dict[str, bool]] = {}
    pure_preds: dict[str, dict[str, bool]] = {}
    neuro_cond: dict[str, dict[str, bool]] = {}

    for patient in patients:
        pid = patient.patient_id
        if data_source == "csv" and provider is not None:
            note = provider.get_patient_note(pid)
        else:
            note = patient.ehr_note or ""
        if data_source == "csv" and provider is not None:
            entities = _entities_for_csv_benchmark(
                pid, note, provider, extractor, validator, trials,
            )
        else:
            if not note:
                continue
            entities = extractor.extract(note, silent=True).to_dict()

        reports = validator.validate_all_trials(entities, trials)
        neuro_preds[pid] = {
            r.trial_id: definitive_eligible(r) for r in reports
        }
        neuro_cond[pid] = {
            r.trial_id: r.is_conditionally_eligible for r in reports
        }
        pure_preds[pid] = {
            t["trial_id"]: pure_neural_eligibility(entities, t) for t in trials
        }

    if not gold:
        raise RuntimeError("No gold-standard labels available for benchmark.")

    neuro_metrics = macro_average(
        compute_metrics(neuro_preds, gold, trials, neuro_cond),
    )
    pure_metrics = macro_average(
        compute_metrics(pure_preds, gold, trials, {}),
    )

    # Paired McNemar test: is Neuro-Symbolic significantly different from Pure Neural
    # on the SAME (patient, trial) decisions? Uses existing gold/preds — no recompute.
    trial_ids = [t["trial_id"] for t in trials]
    mcnemar = mcnemar_test(gold, neuro_preds, pure_preds, trial_ids)

    return {
        "data_source": data_source,
        "n_patients": len(neuro_preds),
        "n_patients_loaded": len(patients),
        "n_trials": len(trials),
        "neuro_symbolic": neuro_metrics,
        "pure_neural": pure_metrics,
        "mcnemar": mcnemar,
        "gold_description": (
            "Symbolic validator on structured profiles (synthetic/MIMIC) "
            "or CSV pre-extraction (csv source)"
        ),
    }

def print_verdict_distribution(
    distribution: dict[str, int],
    title: str = "Predicted Verdict Distribution",
) -> None:
    total = sum(distribution.values()) or 1
    print_header(title)
    safe_print(f"  {'Verdict':14s}  {'Count':>6s}  {'Pct':>7s}  Chart")
    safe_print(f"  {'-' * 14}  {'-' * 6}  {'-' * 7}  {'-' * 32}")
    for label in ("ELIGIBLE", "INELIGIBLE", "INCONCLUSIVE"):
        count = distribution.get(label, 0)
        pct = count / total
        safe_print(f"  {label:14s}  {count:6d}  {pct:6.1%}  {_bar(pct, width=24)}")

def print_metrics_table(metrics: dict[str, Any]) -> None:
    print_header("Neural Extractor vs Symbolic Ground Truth")
    safe_print("  Compares BioBERT+Regex extraction path against Symbolic Validator")
    safe_print("  ground truth built from structured CSV rows (active conditions only).")
    safe_print("")
    for key in ("accuracy", "precision", "recall", "f1"):
        val = metrics[key]
        safe_print(f"  {key.capitalize():12s}: {_bar(val)}  ({val:.4f})")
    safe_print("")
    safe_print(
        f"  TP={metrics['tp']}  TN={metrics['tn']}  "
        f"FP={metrics['fp']}  FN={metrics['fn']}  "
        f"INCONCLUSIVE={metrics['inconclusive']}"
    )

def load_csv_provider(csv_dir: Path, limit: int) -> RealCSVProvider:
    if not csv_dir.exists():
        raise FileNotFoundError(
            f"CSV directory not found: {csv_dir}\n"
            f"Expected patients.csv, conditions.csv, medications.csv under that folder.\n"
            f"Default path: {DEFAULT_CSV_DIR}"
        )
    return get_default_csv_provider(data_dir=csv_dir, limit=limit, verbose=False)

def evaluate_patient_csv(
    patient_id: str,
    provider: PatientDataProvider,
    extractor: NeuralExtractor,
    validator: SymbolicValidator,
    trials: list[dict[str, Any]],
) -> dict[str, Any]:
    """Evaluate one patient: neural predicted vs symbolic gold on CSV data."""
    note = provider.get_patient_note(patient_id)
    if not note:
        raise ValueError(f"No note for patient {patient_id}")

    # Gold: structured CSV entities → Symbolic Validator (active conditions only)
    gold_entities = {}
    if hasattr(provider, "get_pre_extracted"):
        gold_entities = provider.get_pre_extracted(patient_id) or {}

    gold_reports = validator.validate_all_trials(gold_entities, trials)

    # Predicted: Neural Extractor on composed note → Symbolic Validator
    pred_entities = extractor.extract(note, silent=True).to_dict()
    pred_reports = validator.validate_all_trials(pred_entities, trials)

    gold_by_id = {r.trial_id: r for r in gold_reports}
    pred_by_id = {r.trial_id: r for r in pred_reports}

    trial_results: dict[str, Any] = {}
    deltas: list[DeltaLabel] = []

    for trial in trials:
        tid = trial["trial_id"]
        gold_r = gold_by_id[tid]
        pred_r = pred_by_id[tid]
        delta = compute_eligibility_delta(pred_r, gold_r)
        deltas.append(delta)

        trial_results[tid] = {
            "trial_name": trial["trial_name"],
            "predicted_eligibility": pred_r.eligible,
            "predicted_definitive_eligible": definitive_eligible(pred_r),
            "gold_standard_eligibility": gold_r.eligible,
            "gold_definitive_eligible": definitive_eligible(gold_r),
            "predicted_verdict": verdict_label(pred_r),
            "gold_verdict": verdict_label(gold_r),
            "eligibility_delta": delta,
            "xai_reasoning": build_clinical_narrative(pred_r, pred_entities).replace("**", ""),
        }

    active_conditions = provider.get_conditions(patient_id)
    return {
        "patient_id": patient_id,
        "active_condition_count": len(active_conditions),
        "active_conditions": [c.description for c in active_conditions],
        "trials": trial_results,
        "eligibility_delta_counts": aggregate_delta_counts(deltas),
    }

def run_csv_dissertation_evaluation(args: argparse.Namespace) -> dict[str, Any]:
    """Batch-evaluate n patients from RealCSVProvider and save JSON results."""
    csv_dir = Path(args.csv_dir)
    trials = build_trial_criteria()

    print_header("EthiMatch Dissertation Evaluation (7005SCN)")
    safe_print(f"  CSV folder : {csv_dir}")
    safe_print(f"  Patients   : {args.n_patients}")
    safe_print(f"  Trials     : {len(trials)}")
    safe_print(f"  Output     : {args.output}")
    safe_print(
        "  Safety rule: conditions.csv filtered to STOP is null/NaN/empty only"
    )

    provider = load_csv_provider(csv_dir, limit=args.n_patients)
    patient_ids = provider.list_patient_ids()
    if not patient_ids:
        raise RuntimeError(f"No patients loaded from {csv_dir}")

    safe_print(f"\n[Eval] Loaded {len(patient_ids)} patients from {provider.source_name()}")
    safe_print("[Eval] Initialising BioBERT + Symbolic Validator …")
    extractor = NeuralExtractor(device=-1, verbose=False)
    validator = SymbolicValidator()

    print_header(f"Batch Evaluation — {len(patient_ids)} Patients", "-")
    t0 = time.time()
    per_patient: list[dict[str, Any]] = []
    all_deltas: list[DeltaLabel] = []
    verdict_dist: dict[str, int] = {"ELIGIBLE": 0, "INELIGIBLE": 0, "INCONCLUSIVE": 0}

    for i, pid in enumerate(patient_ids, 1):
        if i % 10 == 1 or len(patient_ids) <= 20:
            safe_print(f"  [{i:03d}/{len(patient_ids)}] {pid}")
        try:
            record = evaluate_patient_csv(pid, provider, extractor, validator, trials)
        except (ValueError, KeyError) as exc:
            safe_print(f"  [{i:03d}] SKIP {pid}: {exc}")
            continue

        per_patient.append(record)
        for tid, tr in record["trials"].items():
            all_deltas.append(tr["eligibility_delta"])
            verdict_dist[tr["predicted_verdict"]] = (
                verdict_dist.get(tr["predicted_verdict"], 0) + 1
            )

    elapsed = time.time() - t0
    delta_counts = aggregate_delta_counts(all_deltas)
    metrics = compute_classifier_metrics(delta_counts)

    per_trial_metrics: dict[str, Any] = {}
    for trial in trials:
        tid = trial["trial_id"]
        trial_deltas = [
            p["trials"][tid]["eligibility_delta"]
            for p in per_patient
            if tid in p["trials"]
        ]
        per_trial_metrics[tid] = {
            "trial_name": trial["trial_name"],
            **compute_classifier_metrics(aggregate_delta_counts(trial_deltas)),
        }

    results: dict[str, Any] = {
        "metadata": {
            "module": "7005SCN",
            "n_patients": len(per_patient),
            "n_patients_requested": args.n_patients,
            "source": provider.source_name(),
            "csv_dir": str(csv_dir.resolve()),
            "elapsed_seconds": round(elapsed, 2),
            "seconds_per_patient": round(elapsed / max(len(per_patient), 1), 2),
            "trials": [{"trial_id": t["trial_id"], "trial_name": t["trial_name"]} for t in trials],
            "active_conditions_filter": (
                "conditions.csv: only rows where STOP is null, NaN, or empty"
            ),
            "comparison": (
                "predicted = Neural Extractor + Symbolic Validator; "
                "gold = Symbolic Validator on structured CSV pre-extraction"
            ),
        },
        "aggregate_metrics": metrics,
        "per_trial_metrics": per_trial_metrics,
        "verdict_distribution": verdict_dist,
        "eligibility_delta_totals": delta_counts,
        "per_patient": per_patient,
    }

    safe_print(
        f"\n[Eval] Complete in {elapsed:.1f}s "
        f"({elapsed / max(len(per_patient), 1):.2f}s per patient)."
    )
    print_metrics_table(metrics)
    print_verdict_distribution(verdict_dist)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json_dumps(results, indent=2), encoding="utf-8")
    safe_print(f"\n[Eval] Results saved to {out_path.resolve()}")

    return results

#  Legacy / synthetic evaluation main path

def run_legacy_evaluation(args: argparse.Namespace) -> None:
    trials = build_trial_criteria()
    trial_ids = [t["trial_id"] for t in trials]
    patients = load_patients(args)
    gold = load_gold(patients, trials, args)

    print_header("EthiMatch Research Evaluation")
    safe_print(f"  Cohort     : {len(patients)} patients ({args.source})")
    safe_print(f"  Trials     : {len(trials)}")
    safe_print(f"  Gold labels: {'yes' if gold else 'skipped'}")

    safe_print("\n[Eval] Initialising BioBERT + Symbolic Validator …")
    extractor = NeuralExtractor(device=-1, verbose=False)
    validator = SymbolicValidator()

    print_header(f"Running EthiMatch Pipeline — {len(patients)} Patients", "-")
    t0 = time.time()
    all_predictions: dict[str, dict[str, bool]] = {}
    all_conditional: dict[str, dict[str, bool]] = {}

    for i, patient in enumerate(patients, 1):
        if not patient.ehr_note:
            safe_print(f"  [{i}/{len(patients)}] {patient.patient_id} — no note, skipping")
            continue
        if i % 10 == 1 or len(patients) <= 20:
            safe_print(
                f"  [{i:03d}/{len(patients)}] {patient.patient_id} — "
                f"{patient.disease or 'unknown'}, Stage {patient.stage or '?'}"
            )
        verdict_map, cond_map = run_pipeline_on_note(
            patient.ehr_note, extractor, validator, trials,
        )
        all_predictions[patient.patient_id] = verdict_map
        all_conditional[patient.patient_id] = cond_map

    elapsed = time.time() - t0
    safe_print(
        f"\n[Eval] Pipeline complete in {elapsed:.1f}s "
        f"({elapsed / max(len(patients), 1):.2f}s per patient)."
    )

    results: dict[str, Any] = {
        "n_patients": len(patients),
        "source": args.source,
        "elapsed_seconds": round(elapsed, 2),
        "ethimatch": {},
    }

    if gold:
        ethi_metrics = compute_metrics(all_predictions, gold, trials, all_conditional)
        ethi_macro = macro_average(ethi_metrics)
        results["ethimatch"] = {
            "macro": ethi_macro,
            "per_trial": [
                {
                    "trial_id": m.trial_id,
                    "accuracy": m.accuracy,
                    "precision": m.precision,
                    "recall": m.recall,
                    "f1": m.f1,
                    "fpr": m.fpr,
                    "inconclusive": m.inconclusive,
                }
                for m in ethi_metrics
            ],
        }

        print_header("EthiMatch — Per-Trial Metrics")
        for m in ethi_metrics:
            print_trial_metrics(m)

        print_header("EthiMatch — Macro-Averaged Metrics")
        for name, val in ethi_macro.items():
            safe_print(f"  {name.capitalize():12s}: {_bar(val)}  ({val:.4f})")

        total_evals = len(patients) * len(trials)
        total_cond = sum(sum(v.values()) for v in all_conditional.values())
        inconcl_rate = total_cond / total_evals if total_evals else 0.0
        print_header("Missing-Data Coverage (INCONCLUSIVE Rate)")
        safe_print(f"  Inconclusive rate: {_bar(inconcl_rate)} ({total_cond}/{total_evals})")

    if args.baseline != "none" and gold:
        from baseline_llm import get_baseline

        safe_print(f"\n[Eval] Running {args.baseline} LLM baseline …")
        baseline = get_baseline(args.baseline)
        notes = [p.ehr_note for p in patients]
        pids = [p.patient_id for p in patients]
        baseline_preds = baseline.predict_batch(notes, pids, trials)

        base_metrics = compute_metrics(baseline_preds, gold, trials, {})
        base_macro = macro_average(base_metrics)
        results["baseline"] = {
            "mode": args.baseline,
            "macro": base_macro,
            "per_trial": [
                {
                    "trial_id": m.trial_id,
                    "accuracy": m.accuracy,
                    "precision": m.precision,
                    "recall": m.recall,
                    "f1": m.f1,
                    "fpr": m.fpr,
                }
                for m in base_metrics
            ],
        }

        print_header(f"Baseline ({args.baseline}) — Macro Metrics")
        for name, val in base_macro.items():
            safe_print(f"  {name.capitalize():12s}: {_bar(val)}  ({val:.4f})")

        mcnemar = mcnemar_test(gold, all_predictions, baseline_preds, trial_ids)
        results["mcnemar"] = mcnemar
        print_header("McNemar Paired Significance Test (EthiMatch vs Baseline)")
        safe_print(
            f"  EthiMatch correct / Baseline wrong : "
            f"{mcnemar['ethimatch_correct_baseline_wrong']}"
        )
        safe_print(
            f"  EthiMatch wrong / Baseline correct : "
            f"{mcnemar['ethimatch_wrong_baseline_correct']}"
        )
        safe_print(f"  Chi-square (approx)                : {mcnemar['chi2']}")
        safe_print(f"  p-value (approx)                   : {mcnemar['p_value_approx']}")
        sig = "YES" if mcnemar["significant_at_0.05"] else "NO"
        safe_print(f"  Significant at p<0.05              : {sig}")

        print_header("Head-to-Head Summary")
        safe_print(f"  {'Metric':12s}  {'EthiMatch':>10}  {'Baseline':>10}  {'Delta':>8}")
        for key in ("accuracy", "precision", "recall", "f1", "fpr"):
            e = ethi_macro[key]
            b = base_macro[key]
            delta = e - b
            safe_print(f"  {key.capitalize():12s}  {e:>10.2%}  {b:>10.2%}  {delta:>+8.2%}")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json_dumps(results, indent=2), encoding="utf-8")
        safe_print(f"\n[Eval] Results saved to {out_path}")

def run_dashboard_evaluation(
    *,
    n_patients: int = 20,
    include_baseline: bool = True,
    data_sources: list[str] | None = None,
    include_csv_dissertation: bool = False,
) -> dict[str, Any]:
    """Run evaluation from the Streamlit Evaluation page.

    By default only runs the comparative benchmark for ``data_sources`` (fast).
    Set ``include_csv_dissertation=True`` for the full per-patient CSV dissertation pass.
    """
    sources = data_sources or ["csv"]
    csv_results: dict[str, Any] | None = None
    if include_csv_dissertation:
        args = argparse.Namespace(
            source="csv",
            legacy=False,
            csv_dir=str(DEFAULT_CSV_DIR),
            n_patients=n_patients,
            limit=n_patients,
            seed=42,
            baseline="heuristic" if include_baseline else "none",
            skip_gold=False,
            gold_file="",
            output=str(DEFAULT_OUTPUT),
        )
        csv_results = run_csv_dissertation_evaluation(args)

    comparative: dict[str, Any] = {}
    source_runners = {
        "csv": lambda: run_comparative_benchmark(
            data_source="csv", n_patients=n_patients,
        ),
        "synthetic": lambda: run_comparative_benchmark(
            data_source="synthetic", n_patients=n_patients, seed=42,
        ),
        "mimic": lambda: run_comparative_benchmark(
            data_source="mimic", n_patients=n_patients,
        ),
    }
    for key in sources:
        if key not in source_runners:
            continue
        try:
            comparative[key] = source_runners[key]()
        except Exception as exc:
            comparative[key] = {"error": str(exc)}

    comparative["mimic_available"] = is_mimic_benchmark_available()
    payload = {"csv_evaluation": csv_results, "comparative": comparative}
    save_dashboard_benchmark_payload(payload)
    return payload

def save_dashboard_benchmark_payload(payload: dict[str, Any]) -> Path:
    """Persist evaluation page results for fast reload without re-running BioBERT."""
    bench_path = DEFAULT_OUTPUT.parent / "comparative_benchmark.json"
    bench_path.parent.mkdir(parents=True, exist_ok=True)
    bench_path.write_text(json_dumps(payload, indent=2), encoding="utf-8")
    return bench_path

def main() -> None:
    parser = argparse.ArgumentParser(
        description="EthiMatch dissertation evaluation (7005SCN)",
    )
    parser.add_argument(
        "--source",
        choices=["csv"],
        default="csv",
        help="Data source (local CSV via RealCSVProvider)",
    )
    parser.add_argument(
        "--csv-dir",
        type=str,
        default=str(DEFAULT_CSV_DIR),
        help="Path to folder with patients.csv, conditions.csv, medications.csv",
    )
    parser.add_argument(
        "--n-patients", type=int, default=150,
        help="Number of patients to evaluate",
    )
    parser.add_argument("--legacy", action="store_true", help="Hand-crafted 20-patient cohort (no CSV)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--baseline", choices=["none", "heuristic", "openai"], default="none")
    parser.add_argument("--skip-gold", action="store_true")
    parser.add_argument("--gold-file", type=str, default="")
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help="JSON output path (default: results/evaluation_metrics.json)",
    )
    args = parser.parse_args()

    if args.legacy:
        run_legacy_evaluation(args)
    else:
        run_csv_dissertation_evaluation(args)

    print_header("Evaluation Complete")
    safe_print("  Done.\n")

if __name__ == "__main__":
    main()
