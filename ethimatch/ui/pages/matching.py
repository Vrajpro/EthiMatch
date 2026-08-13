"""Patient Matching page UI."""

from __future__ import annotations

import streamlit as st

from config import disease_code_from_display, disease_display_options, disease_label_for_code
from console import json_dumps
from ethimatch_pipeline import MatchingPatientResult
from services.matching_service import (
    build_matching_export_data,
    build_quick_entry_profile,
    resolve_batch_filter,
    run_csv_batch_screening,
    run_quick_entry_screening,
    sort_matching_results,
)
from services.runtime import load_pipeline
from silver_cache import count_silver_entities
from ui.components import (
    _matching_verdict_sort_order,
    clinical_panel,
    matching_registry_verdict,
    render_clinical_notice,
    render_cohort_banner,
    render_hint_text,
    render_matching_batch_summary,
    render_matching_expandable_registry,
    render_page_header,
    render_pipeline_stepper,
    render_section,
)
from ui.pages._common import (
    MATCHING_BIOBERT_BATCH_DEFAULT,
    MATCHING_BIOBERT_BATCH_MAX,
    clear_cache_if_needed,
    data_source_label,
    get_patient_provider,
    quick_entry_fields,
    registry_limit_label,
)

def _render_batch_filter_controls() -> tuple[bool, list[str] | None, str, bool]:
    qe_label_raw = st.session_state.get("qe_disease")
    qe_code = disease_code_from_display(str(qe_label_raw)) if qe_label_raw else None
    qe_label = disease_label_for_code(qe_code) if qe_code else "not set in sidebar"

    st.markdown("**CSV batch — which patients to screen**")
    render_hint_text(
        "CSV batch screens **real patients from the dataset**. Quick Entry age, stage, "
        "BMI, and ECOG do **not** filter the batch list unless you choose a disease filter below."
    )

    mode_labels = {
        "oncology_any": "Oncology only — any trial cancer (lung, breast, etc.)",
        "quick_entry_disease": f"Filter CSV by Quick Entry disease only ({qe_label})",
        "pick_disease": "Pick a specific disease from the list",
        "all_patients": "All loaded patients (include non-oncology / inconclusive)",
    }
    mode = st.radio(
        "Patient filter",
        options=list(mode_labels.keys()),
        format_func=lambda k: mode_labels[k],
        key="matching_batch_filter",
        label_visibility="collapsed",
    )

    picked = None
    if mode == "pick_disease":
        picked = st.selectbox("Disease", disease_display_options(), key="matching_pick_disease")

    oncology_only, disease_codes, filter_label, can_run = resolve_batch_filter(
        mode, str(qe_label_raw) if qe_label_raw else None, picked,
    )

    if mode == "quick_entry_disease" and not can_run:
        st.warning("Set **Primary Disease** in the sidebar Quick Entry builder first.")
    elif mode == "quick_entry_disease" and can_run:
        render_hint_text(
            "This filter uses **disease only** from Quick Entry. Age, stage, BMI, ECOG, "
            "and therapies are **not** applied to CSV selection."
        )
    return oncology_only, disease_codes, filter_label, can_run

def _render_results_panel(results: list[MatchingPatientResult]) -> None:
    st.session_state["matching_results_by_id"] = {r.patient_id: r for r in results}
    with clinical_panel("Patient Registry"):
        render_matching_expandable_registry(results, provider=get_patient_provider())

def _render_export(results: list[MatchingPatientResult]) -> None:
    render_section("Export Matching Report")
    with clinical_panel("Downloads"):
        export_data = build_matching_export_data(results, data_source_label(), matching_registry_verdict)
        export_json = json_dumps(export_data, indent=2)
        c_json, c_pdf = st.columns(2)
        with c_json:
            st.download_button(
                "Download JSON", export_json, "ethimatch_matching.json", "application/json",
                use_container_width=True, key="matching_download_json",
            )
        with c_pdf:
            try:
                from pdf_export import matching_batch_report_to_pdf

                pdf_bytes = matching_batch_report_to_pdf(
                    export_data, [r.audit_report for r in results],
                )
                st.download_button(
                    "Download PDF", pdf_bytes, "ethimatch_matching.pdf", "application/pdf",
                    use_container_width=True, key="matching_download_pdf",
                )
            except ImportError:
                st.caption("Install fpdf2 for PDF export: pip install fpdf2")

def page_matching(quick_note: str | None = None) -> None:
    render_page_header(
        "Patient Matching",
        "Cohort Neuro-Symbolic Screening",
        "",
        chips=[("Human-in-the-Loop", False)],
    )

    clear_cache_if_needed()
    provider = get_patient_provider()
    loaded_count = len(provider.get_all_patients())
    render_hint_text(
        f"**{loaded_count}** patients loaded (CSV cap: **{registry_limit_label()}** from sidebar). "
        f"Silver cache: **{count_silver_entities()}** materialized extraction(s)."
    )

    render_pipeline_stepper(active=0)
    render_section("Cohort Neuro-Symbolic Screening")

    with clinical_panel("Pipeline Controls"):
        render_clinical_notice(
            "**Two separate actions:** "
            "**Screen Quick Entry Note** tests your synthetic note only. "
            "**Run CSV batch** screens real patients using the filter below.",
            "NEUTRAL",
        )

        c1, c2 = st.columns(2)
        with c1:
            batch_size = st.slider(
                "BioBERT batch size",
                min_value=5,
                max_value=min(MATCHING_BIOBERT_BATCH_MAX, max(loaded_count, 5)),
                value=min(MATCHING_BIOBERT_BATCH_DEFAULT, max(loaded_count, 5)),
                step=5,
                key="matching_batch_size",
            )
        with c2:
            render_hint_text(f"Up to **{batch_size}** patients per batch run.")

        oncology_only, disease_codes, filter_label, batch_filter_ok = _render_batch_filter_controls()

        run_quick = False
        run_batch = False
        active_quick_note = quick_note or st.session_state.get("quick_entry_note")
        if active_quick_note:
            render_hint_text("Quick Entry note is ready — click **Screen Quick Entry Note**.")
            run_quick = st.button(
                "Screen Quick Entry Note (instant — 1 note)",
                type="primary", key="run_matching_quick",
            )
            run_batch = st.button(
                f"Screen CSV Batch — {filter_label} (max {batch_size})",
                type="secondary", key="run_matching_cohort", disabled=not batch_filter_ok,
            )
        else:
            run_batch = st.button(
                f"Run CSV Batch — {filter_label} (max {batch_size})",
                type="primary", key="run_matching_cohort", disabled=not batch_filter_ok,
            )

    if run_quick and active_quick_note:
        pipeline = load_pipeline()
        profile = build_quick_entry_profile(quick_entry_fields())
        with st.spinner("Processing Quick Entry note…"):
            result = run_quick_entry_screening(pipeline, active_quick_note, profile)
        results = [result]
        st.session_state["matching_results"] = results
        st.session_state["matching_results_by_id"] = {r.patient_id: r for r in results}
        st.session_state["matching_selected_patient_id"] = "QUICK-ENTRY"
        st.session_state["matching_registry_page"] = 1
        verdict, _, score = matching_registry_verdict(result.audit_report)
        token = "PASS" if verdict == "Eligible" else (
            "INCONCLUSIVE" if verdict in ("Inconclusive", "Conditional") else "FAIL"
        )
        render_clinical_notice(
            f"Quick Entry screening complete — verdict: **{verdict}** (match score **{score:.0f}%**).",
            token,
        )
        render_pipeline_stepper(active=4)

    if run_batch and not batch_filter_ok:
        render_clinical_notice("Fix the CSV batch filter above before running.", "FAIL")
    elif run_batch and batch_filter_ok:
        pipeline = load_pipeline()
        progress = st.progress(0.0)
        status = st.empty()

        def _on_progress(done: int, total: int, pid: str) -> None:
            status.caption(f"Screening {done} / {total} — `{pid[:18]}…`")
            progress.progress(done / total)

        results, path_counts = run_csv_batch_screening(
            pipeline, provider,
            batch_size=batch_size,
            oncology_only=oncology_only,
            disease_codes=disease_codes,
            progress_callback=_on_progress,
        )
        progress.empty()
        status.empty()

        if not results:
            render_clinical_notice(
                f"No patients matched filter **{filter_label}**. "
                "Try a broader filter or increase the CSV cap.",
                "FAIL",
            )
            return

        results = sort_matching_results(results, matching_registry_verdict, _matching_verdict_sort_order)
        st.session_state["matching_results"] = results
        st.session_state["matching_results_by_id"] = {r.patient_id: r for r in results}
        st.session_state["matching_selected_patient_id"] = None
        st.session_state["matching_registry_page"] = 1
        render_matching_batch_summary(total=len(results), filter_label=filter_label, path_counts=path_counts)
        render_pipeline_stepper(active=4)

    results = st.session_state.get("matching_results")
    if not results:
        render_clinical_notice(
            "**Screen Quick Entry Note** tests one synthetic note. "
            f"**Run CSV Batch** screens up to **{MATCHING_BIOBERT_BATCH_DEFAULT}** patients.",
            "NEUTRAL",
        )
        return

    if not run_quick and not run_batch:
        render_pipeline_stepper(active=4)

    eligible = sum(1 for r in results if matching_registry_verdict(r.audit_report)[0] == "Eligible")
    inconclusive = sum(
        1 for r in results
        if matching_registry_verdict(r.audit_report)[0] in ("Inconclusive", "Conditional")
    )
    blocked = sum(1 for r in results if matching_registry_verdict(r.audit_report)[0] == "Blocked")
    render_cohort_banner(eligible, inconclusive, blocked, len(results))
    render_hint_text(
        "Each row shows the **primary trial** driving status and match %. "
        "This is a rule-compliance estimate — final enrollment requires clinician review."
    )
    _render_results_panel(results)
    _render_export(results)
