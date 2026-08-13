"""Evaluation page UI."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from config import DEFAULT_CSV_DIR
from services.evaluation_service import (
    SOURCE_KEYS,
    available_evaluation_sources,
    evaluation_patient_limits,
    load_saved_evaluation,
    run_comparative_evaluation,
    run_evaluation_request,
)
from ui.components import (
    clinical_panel,
    render_clinical_notice,
    render_evaluation_benchmark_chart,
    render_page_header,
    render_section,
)
from ui.pages._common import registry_limit, registry_limit_label

@st.cache_data(show_spinner=False, ttl=3600)
def _load_cached_benchmark_file() -> dict | None:
    root = Path(__file__).resolve().parents[2]
    return load_saved_evaluation(root)

@st.cache_data(show_spinner="Running comparative benchmark…", ttl=3600)
def _cached_comparative_benchmark(data_source: str, n_patients: int) -> dict:
    return run_comparative_evaluation(data_source, n_patients)

def page_evaluation() -> None:
    render_page_header(
        "Research Evaluation",
        "Pipeline Benchmarking",
        "Quantitative comparison of neuro-symbolic matching versus a pure neural baseline.",
        chips=[("Dissertation Metrics", False)],
    )

    try:
        reg_limit = registry_limit()
        eval_default, eval_max = evaluation_patient_limits(reg_limit)

        with clinical_panel("Evaluation Settings"):
            eval_n = st.slider(
                "Patients per benchmark run",
                min_value=10,
                max_value=eval_max,
                value=min(st.session_state.get("eval_n_patients", eval_default), eval_max),
                step=5,
                key="eval_n_patients",
            )
            data_options = available_evaluation_sources()
            data_source_label = st.selectbox("Benchmark dataset", data_options, key="eval_data_source")
            include_dissertation = st.checkbox(
                "Include full CSV dissertation eval (slow)",
                value=False, key="eval_include_dissertation",
            )
            st.checkbox(
                "Benchmark all datasets (synthetic + CSV + MIMIC)",
                value=False, key="eval_run_all_sources",
            )
            st.markdown(f"CSV folder: `{DEFAULT_CSV_DIR}` · Cap: **{registry_limit_label()}**")

        bench_key = SOURCE_KEYS.get(data_source_label, "csv")
        c1, c2 = st.columns(2)
        with c1:
            run_benchmark = st.button(
                f"Run Benchmark ({data_source_label})", type="primary", key="run_eval_benchmark_btn",
            )
        with c2:
            run_full = st.button("Run All Sources + Save", type="secondary", key="run_eval_all_btn")

        if run_benchmark or run_full:
            run_all = run_full or st.session_state.get("eval_run_all_sources", False)
            spinner_msg = (
                f"Running benchmarks for all datasets ({eval_n} patients each)…"
                if run_all else f"Running {data_source_label} benchmark ({eval_n} patients)…"
            )
            with st.spinner(spinner_msg):
                comparative = None
                if not run_all:
                    _cached_comparative_benchmark.clear()
                    comparative = _cached_comparative_benchmark(bench_key, eval_n)
                payload, evaluation_log = run_evaluation_request(
                    source_key=bench_key,
                    n_patients=eval_n,
                    run_all_sources=run_all,
                    include_csv_dissertation=include_dissertation,
                    comparative_result=comparative,
                )
                st.session_state["eval_last_payload"] = payload
                st.session_state["eval_last_log"] = evaluation_log
            render_clinical_notice("Benchmark completed.", "PASS")
            _load_cached_benchmark_file.clear()
            _cached_comparative_benchmark.clear()
            st.rerun()

        payload = st.session_state.get("eval_last_payload")
        if payload is None:
            payload = _load_cached_benchmark_file()
            if payload:
                st.caption("Loaded cached results from `results/comparative_benchmark.json`.")

        comparative = (payload or {}).get("comparative") or {}
        benchmark = comparative.get(bench_key)

        if comparative:
            render_section("System Performance — Neuro-Symbolic vs Pure Neural")
            if benchmark is None and bench_key == "mimic":
                render_clinical_notice("MIMIC-IV benchmark was not run.", "INCONCLUSIVE")
            elif benchmark and not benchmark.get("error"):
                render_evaluation_benchmark_chart(benchmark, chart_key=f"eval_benchmark_{bench_key}")
            elif benchmark and benchmark.get("error"):
                render_clinical_notice(f"Benchmark error: {benchmark['error']}", "FAIL")
            else:
                render_clinical_notice(f"No results for '{data_source_label}'.", "NEUTRAL")

            with st.expander("All benchmark datasets (summary)", expanded=False):
                for label, key in (("Synthetic", "synthetic"), ("CSV", "csv"), ("MIMIC-IV", "mimic")):
                    b = comparative.get(key)
                    if not b or b.get("error"):
                        st.markdown(f"**{label}:** not available")
                        continue
                    ns = b.get("neuro_symbolic", {})
                    pn = b.get("pure_neural", {})
                    st.markdown(
                        f"**{label}** (n={b.get('n_patients', '?')}): "
                        f"Neuro-Symbolic P/R/FPR = "
                        f"{ns.get('precision', 0):.1%} / {ns.get('recall', 0):.1%} / {ns.get('fpr', 0):.1%} · "
                        f"Pure Neural = "
                        f"{pn.get('precision', 0):.1%} / {pn.get('recall', 0):.1%} / {pn.get('fpr', 0):.1%}"
                    )
        else:
            render_clinical_notice("Click **Run Benchmark** to generate comparison charts.", "NEUTRAL")

        if st.session_state.get("eval_last_log"):
            with st.expander("Evaluation console log", expanded=False):
                st.code(st.session_state["eval_last_log"], language=None)

        csv_eval = (payload or {}).get("csv_evaluation")
        if csv_eval and csv_eval.get("aggregate_metrics"):
            render_section("CSV Extraction Fidelity (Neural vs Structured Gold)")
            agg = csv_eval["aggregate_metrics"]
            st.markdown(
                f"Accuracy **{agg.get('accuracy', 0):.1%}** · "
                f"Precision **{agg.get('precision', 0):.1%}** · "
                f"Recall **{agg.get('recall', 0):.1%}** · "
                f"F1 **{agg.get('f1', 0):.1%}**"
            )

    except Exception as exc:
        render_clinical_notice(f"Evaluation module unavailable: {exc}", "FAIL")
