"""Cohort Discovery and Evaluation backend helpers."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Any

from ethimatch_pipeline import CohortResult, EthiMatchPipeline

def build_user_trial_from_criteria(criteria: dict[str, Any]) -> dict[str, Any]:
    registered = criteria.get("registered_trial")
    if registered:
        return {k: v for k, v in registered.items() if not str(k).startswith("_")}
    return {
        "trial_id": "USER-001",
        "trial_name": "Custom Cohort Search",
        "description": "Ad-hoc criteria from UI",
        "inclusion": {
            "diseases": criteria["diseases"],
            "stages": criteria["stages"],
            "age_min": criteria["age_min"],
            "age_max": criteria["age_max"],
            "ecog_max": criteria["ecog_max"],
            "bmi_max": criteria["bmi_max"],
            "required_biomarkers": criteria.get("required_biomarkers", []),
            "gender": criteria.get("gender"),
        },
        "exclusion": {
            "excluded_comorbidities": criteria.get("excluded_comorbidities", []),
            "excluded_prior_therapies": criteria.get("excluded_prior_therapies", []),
            "bmi_min": None,
        },
    }

def run_cohort_screening(
    pipeline: EthiMatchPipeline,
    provider: Any,
    criteria: dict[str, Any],
) -> list[CohortResult]:
    user_trial = build_user_trial_from_criteria(criteria)
    return pipeline.run_cohort_search(provider, user_trial)

def cohort_result_counts(results: list[CohortResult]) -> dict[str, int]:
    eligible = sum(1 for r in results if r.is_eligible)
    conditional = sum(1 for r in results if r.is_conditional)
    ineligible = sum(1 for r in results if not r.is_eligible and not r.is_conditional)
    return {
        "eligible": eligible,
        "conditional": conditional,
        "ineligible": ineligible,
        "total": len(results),
    }

def parse_criteria_for_display(criteria: dict[str, Any]) -> dict[str, Any]:
    registered = criteria.get("registered_trial")
    if registered:
        return {
            "protocol_name": registered.get("trial_name"),
            "protocol_id": registered.get("trial_id"),
            "inclusion": registered.get("inclusion") or {},
            "exclusion": registered.get("exclusion") or {},
        }
    return {
        "protocol_name": None,
        "protocol_id": None,
        "inclusion": {
            "age_min": criteria.get("age_min"),
            "age_max": criteria.get("age_max"),
            "gender": criteria.get("gender"),
            "diseases": criteria.get("diseases"),
            "stages": criteria.get("stages"),
            "ecog_max": criteria.get("ecog_max"),
            "bmi_max": criteria.get("bmi_max"),
        },
        "exclusion": {
            "excluded_comorbidities": criteria.get("excluded_comorbidities"),
            "excluded_prior_therapies": criteria.get("excluded_prior_therapies"),
        },
    }

def build_cohort_export_data(
    criteria: dict[str, Any],
    results: list[CohortResult],
) -> dict[str, Any]:
    counts = cohort_result_counts(results)
    return {
        "criteria": criteria,
        "summary": {
            "eligible": counts["eligible"],
            "conditional": counts["conditional"],
            "ineligible": counts["ineligible"],
        },
        "results": [r.to_dict() for r in results],
    }

def cohort_export_csv(results: list[CohortResult]) -> str:
    buf = StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=[
            "patient_id", "status", "match_score", "age", "gender", "disease", "stage",
            "ecog_ps", "bmi", "failed_rule_names", "fail_reasons",
            "confidence_age", "confidence_gender", "confidence_disease",
            "confidence_stage", "confidence_bmi", "confidence_ecog_ps",
        ],
    )
    writer.writeheader()
    for r in results:
        row = r.to_dict()
        profile = row.get("patient_profile") or {}
        conf = row.get("confidence_scores") or {}
        status = "Eligible" if r.is_eligible else ("Conditional" if r.is_conditional else "Ineligible")
        writer.writerow({
            "patient_id": r.patient_id,
            "status": status,
            "match_score": row.get("match_score"),
            "age": profile.get("age"),
            "gender": profile.get("gender"),
            "disease": profile.get("disease"),
            "stage": profile.get("stage"),
            "ecog_ps": profile.get("ecog_ps"),
            "bmi": profile.get("bmi"),
            "failed_rule_names": "; ".join(row.get("failed_rule_names") or []),
            "fail_reasons": "; ".join(row.get("fail_reasons") or []),
            "confidence_age": conf.get("age"),
            "confidence_gender": conf.get("gender"),
            "confidence_disease": conf.get("disease"),
            "confidence_stage": conf.get("stage"),
            "confidence_bmi": conf.get("bmi"),
            "confidence_ecog_ps": conf.get("ecog_ps"),
        })
    return buf.getvalue()

def eval_source_map() -> dict[str, str]:
    return {
        "Synthetic Data": "synthetic",
        "Real CSV Cohort": "csv",
        "MIMIC-IV Benchmark Data": "mimic",
    }

def load_benchmark_file(project_root: Path) -> dict[str, Any] | None:
    import json

    bench_file = project_root / "results" / "comparative_benchmark.json"
    if not bench_file.is_file():
        return None
    try:
        return json.loads(bench_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
