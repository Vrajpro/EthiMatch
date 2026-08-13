"""Backend operations used by the Evaluation page."""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

import config

SOURCE_KEYS = {
    "Synthetic Data": "synthetic",
    "Real CSV Cohort": "csv",
    "MIMIC-IV Benchmark Data": "mimic",
}

def evaluation_patient_limits(registry_limit: int) -> tuple[int, int]:
    default = int(getattr(config, "EVAL_BENCHMARK_PATIENTS_DEFAULT", 15))
    configured_max = int(getattr(config, "EVAL_BENCHMARK_PATIENTS_MAX", 50))
    effective_max = min(
        configured_max,
        max(registry_limit, 10) if registry_limit else configured_max,
    )
    return min(default, effective_max), effective_max

def available_evaluation_sources() -> list[str]:
    from evaluation import is_mimic_benchmark_available

    sources = ["Synthetic Data", "Real CSV Cohort"]
    if is_mimic_benchmark_available():
        sources.append("MIMIC-IV Benchmark Data")
    return sources

def run_comparative_evaluation(data_source: str, n_patients: int) -> dict[str, Any]:
    from evaluation import run_comparative_benchmark

    return run_comparative_benchmark(
        data_source=data_source,
        n_patients=n_patients,
    )

def run_evaluation_request(
    *,
    source_key: str,
    n_patients: int,
    run_all_sources: bool,
    include_csv_dissertation: bool,
    comparative_result: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    from evaluation import (
        is_mimic_benchmark_available,
        run_dashboard_evaluation,
        save_dashboard_benchmark_payload,
    )

    output = io.StringIO()
    with redirect_stdout(output):
        if run_all_sources:
            payload = run_dashboard_evaluation(
                n_patients=n_patients,
                data_sources=["csv", "synthetic", "mimic"],
                include_csv_dissertation=include_csv_dissertation,
            )
        else:
            benchmark = comparative_result or run_comparative_evaluation(
                source_key,
                n_patients,
            )
            payload = {
                "comparative": {
                    source_key: benchmark,
                    "mimic_available": is_mimic_benchmark_available(),
                },
                "csv_evaluation": None,
            }
            save_dashboard_benchmark_payload(payload)
            if include_csv_dissertation:
                full = run_dashboard_evaluation(
                    n_patients=n_patients,
                    data_sources=[],
                    include_csv_dissertation=True,
                )
                payload["csv_evaluation"] = full.get("csv_evaluation")

    return payload, output.getvalue()[-5000:]

def load_saved_evaluation(project_root: Path) -> dict[str, Any] | None:
    import json

    benchmark_file = project_root / "results" / "comparative_benchmark.json"
    if not benchmark_file.is_file():
        return None
    try:
        return json.loads(benchmark_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
