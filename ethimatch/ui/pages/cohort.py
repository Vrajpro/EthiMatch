"""Cohort Discovery page UI."""

from __future__ import annotations

from typing import Any

import streamlit as st

from console import json_dumps
from ethimatch_pipeline import CohortResult
from services.cohort_service import (
    build_cohort_export_data,
    cohort_export_csv,
    cohort_result_counts,
    parse_criteria_for_display,
    run_cohort_screening,
)
from services.runtime import load_pipeline
from ui.components import (
    clinical_panel,
    render_clinical_notice,
    render_cohort_banner,
    render_cohort_expandable_registry,
    render_hint_text,
    render_page_header,
    render_section,
)
from ui.pages._common import clear_cache_if_needed, get_patient_provider, registry_limit_label

_COHORT_RESULT_KEYS = (
    "cohort_results",
    "cohort_results_by_id",
    "cohort_export_data",
    "cohort_pdf_bytes",
)

def _reset_cohort_session() -> None:
    for key in _COHORT_RESULT_KEYS:
        st.session_state.pop(key, None)
    st.session_state["cohort_selected_patient_id"] = None
    st.session_state["cohort_registry_page"] = 1
    st.session_state["cohort_master_filter"] = "Eligible"

def _render_criteria_summary(criteria: dict[str, Any]) -> None:
    display = parse_criteria_for_display(criteria)
    inc = display["inclusion"]
    excl = display["exclusion"]

    with st.expander("Search Criteria Summary", expanded=False):
        if display["protocol_name"]:
            st.markdown(
                f"**Protocol:** {display['protocol_name']} (`{display['protocol_id']}`)"
            )
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Inclusion**")
            st.markdown(f"- Age: {inc.get('age_min')}–{inc.get('age_max')}")
            st.markdown(f"- Gender: {', '.join(inc.get('gender') or []) or 'any'}")
            st.markdown(f"- Diseases: {', '.join(inc.get('diseases') or []) or 'any'}")
            st.markdown(f"- Stages: {', '.join(inc.get('stages') or []) or 'any'}")
            if inc.get("ecog_max") is not None:
                st.markdown(f"- ECOG ≤ {inc.get('ecog_max')}")
            else:
                st.markdown("- ECOG: any")
            if inc.get("bmi_max") is not None:
                st.markdown(f"- BMI ≤ {inc.get('bmi_max')}")
            else:
                st.markdown("- BMI: any")
        with c2:
            st.markdown("**Exclusion**")
            st.markdown(
                f"- Comorbidities: {', '.join(excl.get('excluded_comorbidities') or ['None'])}"
            )
            st.markdown(
                f"- Prior therapies: {', '.join(excl.get('excluded_prior_therapies') or ['None'])}"
            )

def _render_master_detail(results: list[CohortResult]) -> None:
    st.session_state["cohort_results_by_id"] = {r.patient_id: r for r in results}
    with clinical_panel("Patient Registry"):
        render_cohort_expandable_registry(results, provider=get_patient_provider())

def _render_exports(criteria: dict[str, Any], results: list[CohortResult]) -> None:
    render_section("Export Cohort Report")
    with clinical_panel("Downloads"):
        export_data = st.session_state.get("cohort_export_data")
        if export_data is None:
            export_data = build_cohort_export_data(criteria, results)
            st.session_state["cohort_export_data"] = export_data

        export_json = json_dumps(export_data, indent=2)
        export_csv = cohort_export_csv(results)
        c_json, c_csv, c_pdf = st.columns(3)
        with c_json:
            st.download_button(
                "Download JSON",
                export_json,
                "ethimatch_cohort.json",
                "application/json",
                use_container_width=True,
                key="cohort_download_json",
            )
        with c_csv:
            st.download_button(
                "Download CSV",
                export_csv,
                "ethimatch_cohort.csv",
                "text/csv",
                use_container_width=True,
                key="cohort_download_csv",
            )
        with c_pdf:
            try:
                from pdf_export import cohort_report_to_pdf

                pdf_bytes = cohort_report_to_pdf(export_data)
                st.download_button(
                    "Download PDF",
                    pdf_bytes,
                    "ethimatch_cohort.pdf",
                    "application/pdf",
                    use_container_width=True,
                    key="cohort_download_pdf",
                )
            except ImportError:
                st.caption("Install fpdf2 for PDF export: pip install fpdf2")

def page_cohort(criteria: dict[str, Any] | None = None) -> None:
    render_page_header(
        "Cohort Discovery",
        "Trial-Centric Patient Screening",
        "Symbolic-only screening on pre-extracted CSV fields — no BioBERT.",
    )

    clear_cache_if_needed()
    provider = get_patient_provider()
    loaded_count = len(provider.get_all_patients())
    render_hint_text(
        f"**{loaded_count}** patients in registry (CSV cap: **{registry_limit_label()}**). "
        "Symbolic-only — no BioBERT."
    )

    if criteria is not None:
        st.session_state["cohort_criteria"] = criteria
        _reset_cohort_session()

    criteria = criteria or st.session_state.get("cohort_criteria")
    if criteria is None:
        render_clinical_notice(
            "Configure trial criteria in the sidebar, then click Search Cohort.",
            "NEUTRAL",
        )
        return

    if "cohort_results" not in st.session_state:
        pipeline = load_pipeline()
        with st.spinner(f"Screening {loaded_count} patients (symbolic only)…"):
            results = run_cohort_screening(pipeline, provider, criteria)
        st.session_state["cohort_results"] = results
    else:
        results = st.session_state["cohort_results"]

    counts = cohort_result_counts(results)
    render_cohort_banner(
        counts["eligible"],
        counts["conditional"],
        counts["ineligible"],
        counts["total"],
    )
    _render_criteria_summary(criteria)

    render_section("Clinical Review — Master / Detail")
    st.caption("Select a patient to view pre-computed ValidationReport and XAI narrative.")
    _render_master_detail(results)
    _render_exports(criteria, results)
