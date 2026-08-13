"""
Run ablation (with vs without symbolic layer) plus sampled FP/FN analysis.

Outputs:
  results/ablation_error_analysis.json
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import console  # noqa: F401
from console import json_dumps, safe_print
from data_simulator import build_trial_criteria
from config import DEFAULT_CSV_DIR
from evaluation import (
    _entities_for_csv_benchmark,
    definitive_eligible,
    get_benchmark_extractor,
    is_mimic_benchmark_available,
    load_csv_provider,
    pure_neural_eligibility,
    run_comparative_benchmark,
)
from evaluation_cohort import build_scaled_cohort, compute_gold_standard
from symbolic_validator import RuleVerdict, SymbolicValidator

def _load_source(
    source: str,
    n_patients: int,
) -> tuple[list[Any], dict[str, dict[str, bool]], Any | None]:
    trials = build_trial_criteria()
    validator = SymbolicValidator()
    if source == "synthetic":
        patients = build_scaled_cohort(n=n_patients, seed=42)
        gold = compute_gold_standard(patients, trials, validator)
        return patients, gold, None
    if source == "csv":
        provider = load_csv_provider(DEFAULT_CSV_DIR, n_patients)
        patients = provider.get_all_patients()
        gold: dict[str, dict[str, bool]] = {}
        for p in patients:
            pre = provider.get_pre_extracted(p.patient_id) or {}
            gold[p.patient_id] = {}
            for t in trials:
                gold[p.patient_id][t["trial_id"]] = definitive_eligible(validator.validate(pre, t))
        return patients, gold, provider
    if source == "mimic":
        if not is_mimic_benchmark_available():
            return [], {}, None
        from data_loader import load_provider

        provider = load_provider("MIMIC", limit=n_patients, verbose=False)
        patients = provider.get_all_patients()
        gold = compute_gold_standard(patients, trials, validator)
        return patients, gold, provider
    raise ValueError(f"Unsupported source: {source}")

def _sample_errors(source: str, n_patients: int, sample_size: int, seed: int) -> dict[str, Any]:
    trials = build_trial_criteria()
    validator = SymbolicValidator()
    extractor = get_benchmark_extractor()
    patients, gold, provider = _load_source(source, n_patients)
    errors: list[dict[str, Any]] = []

    for patient in patients:
        pid = patient.patient_id
        note = patient.ehr_note or ""
        if source == "csv" and provider is not None:
            note = provider.get_patient_note(pid)
            entities = _entities_for_csv_benchmark(pid, note, provider, extractor, validator, trials)
        else:
            if not note:
                continue
            entities = extractor.extract(note, silent=True).to_dict()

        for trial in trials:
            tid = trial["trial_id"]
            gold_val = bool(gold.get(pid, {}).get(tid, False))
            neuro_report = validator.validate(entities, trial)
            neuro_pred = definitive_eligible(neuro_report)
            pure_pred = pure_neural_eligibility(entities, trial)

            for model_name, pred in (("neuro_symbolic", neuro_pred), ("pure_neural", pure_pred)):
                if pred == gold_val:
                    continue
                error_type = "FP" if pred and not gold_val else "FN"
                errors.append(
                    {
                        "source": source,
                        "model": model_name,
                        "error_type": error_type,
                        "patient_id": pid,
                        "trial_id": tid,
                        "trial_name": trial.get("trial_name"),
                        "gold_eligible": gold_val,
                        "predicted_eligible": pred,
                        "age": entities.get("age"),
                        "gender": entities.get("gender"),
                        "disease": entities.get("disease"),
                        "stage": entities.get("stage"),
                        "failed_rules": [
                            rr.rule_name
                            for rr in neuro_report.rule_results
                            if rr.verdict == RuleVerdict.FAIL
                        ],
                        "fail_reasons": [
                            rr.explanation
                            for rr in neuro_report.rule_results
                            if rr.verdict == RuleVerdict.FAIL
                        ],
                    },
                )

    rng = random.Random(seed)
    sampled = rng.sample(errors, k=min(sample_size, len(errors))) if errors else []
    by_model = {
        "neuro_symbolic": sum(1 for e in errors if e["model"] == "neuro_symbolic"),
        "pure_neural": sum(1 for e in errors if e["model"] == "pure_neural"),
    }
    by_type = {"FP": sum(1 for e in errors if e["error_type"] == "FP"), "FN": sum(1 for e in errors if e["error_type"] == "FN")}
    return {"total_errors": len(errors), "by_model": by_model, "by_type": by_type, "sampled_cases": sampled}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100, help="Patients per source for ablation/error analysis")
    parser.add_argument("--sample-size", type=int, default=24, help="Sampled FP/FN cases to save (20-30 recommended)")
    args = parser.parse_args()

    n = args.n
    comparative: dict[str, Any] = {}
    for source in ("csv", "synthetic", "mimic"):
        if source == "mimic" and not is_mimic_benchmark_available():
            comparative[source] = {"error": "MIMIC unavailable"}
            continue
        comparative[source] = run_comparative_benchmark(data_source=source, n_patients=n)  # type: ignore[arg-type]

    ablation: dict[str, Any] = {}
    for source, result in comparative.items():
        if "error" in result:
            ablation[source] = result
            continue
        ns = result.get("neuro_symbolic") or {}
        pn = result.get("pure_neural") or {}
        ablation[source] = {
            "n_patients": result.get("n_patients"),
            "f1_neuro_symbolic": ns.get("f1"),
            "f1_pure_neural": pn.get("f1"),
            "f1_delta": float(ns.get("f1", 0.0)) - float(pn.get("f1", 0.0)),
            "fpr_neuro_symbolic": ns.get("fpr"),
            "fpr_pure_neural": pn.get("fpr"),
            "fpr_delta": float(ns.get("fpr", 0.0)) - float(pn.get("fpr", 0.0)),
            "mcnemar": result.get("mcnemar", {}),
        }

    sampled_errors: dict[str, Any] = {}
    for source in ("csv", "synthetic", "mimic"):
        if source == "mimic" and not is_mimic_benchmark_available():
            continue
        safe_print(f"[Error analysis] {source} ...")
        sampled_errors[source] = _sample_errors(source, n, args.sample_size, seed=42)

    payload = {
        "n_patients": n,
        "sample_size_requested": args.sample_size,
        "ablation": ablation,
        "sampled_error_analysis": sampled_errors,
    }
    out = ROOT / "results" / "ablation_error_analysis.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json_dumps(payload, indent=2), encoding="utf-8")
    safe_print(f"Saved: {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
