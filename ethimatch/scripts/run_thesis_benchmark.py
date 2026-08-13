"""
Run n=100 comparative benchmarks and save thesis-ready numbers.

Usage:
  python scripts/run_thesis_benchmark.py
  python scripts/run_thesis_benchmark.py --n 100
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import console  # noqa: F401
from console import json_dumps, safe_print
from evaluation import is_mimic_benchmark_available, run_comparative_benchmark, save_dashboard_benchmark_payload

def _fmt_metrics(label: str, m: dict) -> None:
    safe_print(f"\n  {label}")
    safe_print(f"    Precision : {m.get('precision', 0):.1%}")
    safe_print(f"    Recall    : {m.get('recall', 0):.1%}")
    safe_print(f"    F1        : {m.get('f1', 0):.1%}")
    safe_print(f"    FPR       : {m.get('fpr', 0):.1%}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100, help="Patients per dataset")
    args = parser.parse_args()
    n = args.n

    safe_print(f"EthiMatch thesis benchmark — n={n} per dataset")
    safe_print("=" * 56)

    comparative: dict = {}
    for key in ("csv", "synthetic", "mimic"):
        safe_print(f"\n[{key.upper()}] Running comparative benchmark…")
        try:
            if key == "mimic" and not is_mimic_benchmark_available():
                comparative[key] = {"error": "MIMIC-IV Demo not available"}
                safe_print("  SKIP — MIMIC data not found")
                continue
            result = run_comparative_benchmark(data_source=key, n_patients=n)  # type: ignore[arg-type]
            comparative[key] = result
            ns = result.get("neuro_symbolic") or {}
            pn = result.get("pure_neural") or {}
            mc = result.get("mcnemar") or {}
            safe_print(f"  Patients evaluated: {result.get('n_patients')}")
            _fmt_metrics("Neuro-Symbolic", ns)
            _fmt_metrics("Pure Neural", pn)
            safe_print(
                f"  McNemar p≈{mc.get('p_value_approx', '—')} "
                f"significant@0.05={mc.get('significant_at_0.05')}"
            )
        except Exception as exc:  # noqa: BLE001
            comparative[key] = {"error": str(exc)}
            safe_print(f"  ERROR: {exc}")

    comparative["mimic_available"] = is_mimic_benchmark_available()
    payload = {"comparative": comparative, "n_patients": n}
    out = save_dashboard_benchmark_payload(payload)
    safe_print(f"\nSaved: {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
