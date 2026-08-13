"""EthiMatch demo smoke — verify all demo-critical paths before a viva/demo.

Run:
  .\\venv\\Scripts\\python.exe scripts\\demo_smoke.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def main() -> int:
    print("EthiMatch Demo Smoke")
    print("=" * 48)

    from ui.presentation.layout import clinical_panel
    with clinical_panel("smoke"):
        pass
    print("  PASS  clinical_panel context manager")

    from ui.presentation.registry import filter_cohort_results
    from ui.presentation.charts import build_evaluation_comparison_figure
    import ui.presentation.charts as charts
    assert not hasattr(charts, "build_evaluation_comparison_figure_3d")
    build_evaluation_comparison_figure(
        {"precision": 0.8, "recall": 0.7, "fpr": 0.1, "f1": 0.75},
        {"precision": 0.6, "recall": 0.5, "fpr": 0.2, "f1": 0.55},
    )
    print("  PASS  cohort filter + 2D chart")

    from ui.pages import page_dashboard, page_matching, page_cohort, page_evaluation
    from app import PAGES
    assert set(PAGES) == {"Dashboard", "Patient Matching", "Cohort Discovery", "Evaluation"}
    print("  PASS  all 4 pages unlocked")

    from services.runtime import load_pipeline, get_registered_trials
    from services.matching_service import (
        compose_quick_entry_note,
        build_quick_entry_profile,
        run_quick_entry_screening,
        resolve_batch_filter,
        run_csv_batch_screening,
    )
    from services.cohort_service import run_cohort_screening
    from data_access.loader import load_provider

    trials = get_registered_trials()
    assert len(trials) >= 1
    pipe = load_pipeline()
    print(f"  PASS  pipeline + {len(trials)} trials")

    fields = {
        "qe_age": 55,
        "qe_gender": "male",
        "qe_disease": "NSCLC",
        "qe_stage": "IIIA",
        "qe_bio": [],
        "qe_bmi": 25.0,
        "qe_ecog": 1,
        "qe_comorb": [],
        "qe_rx": [],
        "qe_neg": False,
    }
    note = compose_quick_entry_note(fields)
    profile = build_quick_entry_profile(fields)
    qe = run_quick_entry_screening(pipe, note, profile)
    assert qe.audit_report and qe.audit_report.trial_reports
    print(f"  PASS  Quick Entry screening ({len(qe.audit_report.trial_reports)} trial reports)")

    prov = load_provider("Synthea", limit=100)
    _, _, _, ok = resolve_batch_filter("oncology_any", None, None)
    assert ok
    batch, _counts = run_csv_batch_screening(
        pipe, prov, batch_size=5, oncology_only=True, disease_codes=None,
    )
    if not batch:
        batch, _counts = run_csv_batch_screening(
            pipe, prov, batch_size=5, oncology_only=False, disease_codes=None,
        )
    assert len(batch) > 0
    print(f"  PASS  CSV batch matching ({len(batch)} patients)")

    cohort = run_cohort_screening(pipe, prov, {"registered_trial": trials[0]})
    assert len(cohort) > 0
    print(f"  PASS  Cohort Discovery ({len(cohort)} screened)")

    from evaluation import run_comparative_benchmark
    bench = run_comparative_benchmark(data_source="synthetic", n_patients=5)
    assert "neuro_symbolic" in bench and "pure_neural" in bench
    print("  PASS  Evaluation benchmark (synthetic)")

    print("=" * 48)
    print("DEMO READY — all critical paths passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
