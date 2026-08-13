"""EthiMatch Streamlit entry point."""

from __future__ import annotations

import console  # noqa: F401 — UTF-8 stdout on Windows

import sys
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import config  # noqa: F401

CSV_REGISTRY_LIMIT_ALL: int = getattr(config, "CSV_REGISTRY_LIMIT_ALL", 0)
CSV_REGISTRY_LIMIT_OPTIONS: list[int] = getattr(
    config, "CSV_REGISTRY_LIMIT_OPTIONS", [50, 100, 200, 500, CSV_REGISTRY_LIMIT_ALL]
)
DEFAULT_CSV_UI_PATIENT_LIMIT: int = getattr(config, "DEFAULT_CSV_UI_PATIENT_LIMIT", 100)

def _csv_registry_limit_label(value: int) -> str:
    if value == CSV_REGISTRY_LIMIT_ALL:
        return "All patients (full registry)"
    return str(value)

from data_access.types import DATA_SOURCE_LABELS
from ui.components import inject_theme, render_footer, render_sidebar_brand
from ui.pages import (
    build_cohort_criteria,
    build_quick_note,
    page_cohort,
    page_dashboard,
    page_evaluation,
    page_matching,
)

PAGES = {
    "Dashboard": page_dashboard,
    "Patient Matching": page_matching,
    "Cohort Discovery": page_cohort,
    "Evaluation": page_evaluation,
}

st.set_page_config(
    page_title="EthiMatch | Clinical Trial Matching",
    page_icon="EM",
    layout="wide",
    initial_sidebar_state="expanded",
)

def init_session() -> None:
    """Seed the Streamlit session with the defaults used across pages."""
    defaults: dict[str, Any] = {
        "data_source": "Synthea",
        "csv_registry_limit": 100,
        "cohort_selected_patient_id": None,
        "cohort_master_filter": "All",
        "cohort_master_search": "",
        "matching_selected_patient_id": None,
        "matching_master_filter": "All",
        "matching_master_search": "",
        "matching_batch_filter": "oncology_any",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

def _check_runtime_deps() -> None:
    """Stop early when the app was launched outside the project environment."""
    try:
        import transformers  # noqa: F401
    except ImportError:
        st.error("Missing Python package: **transformers**")
        st.markdown(
            "The app is running with the **wrong Python environment**. "
            "`transformers` is installed in the project `venv`, but this session "
            "is using a different interpreter."
        )
        st.code(
            "cd C:\\Users\\91846\\Desktop\\EthiMatch\\ethimatch\n"
            ".\\run_app.bat",
            language="powershell",
        )
        st.markdown(
            "Or repair the venv once: `setup_venv.bat` then `run_app.bat`. "
            "Do **not** use `streamlit run app.py` from system Python or a mismatched `.venv`."
        )
        st.stop()

def _default_registry_limit_index() -> int:
    if DEFAULT_CSV_UI_PATIENT_LIMIT in CSV_REGISTRY_LIMIT_OPTIONS:
        return CSV_REGISTRY_LIMIT_OPTIONS.index(DEFAULT_CSV_UI_PATIENT_LIMIT)
    return 0

def _render_data_source_selector() -> None:
    st.markdown("---")
    st.markdown('<div class="nav-section">Data Source</div>', unsafe_allow_html=True)

    data_source_options = list(DATA_SOURCE_LABELS.keys())
    current_source = st.session_state.get("data_source", "Synthea")
    if current_source not in data_source_options:
        current_source = "Synthea"

    st.radio(
        "Active patient cohort",
        options=data_source_options,
        index=data_source_options.index(current_source),
        format_func=lambda key: DATA_SOURCE_LABELS.get(key, key),
        key="data_source",
        help=(
            "Switch between the de-identified MIMIC-IV Demo cohort (clinical "
            "benchmark) and the Synthea synthetic cohort (oncology prototyping). "
            "Cached screening results are cleared when the source changes."
        ),
    )

def _render_registry_limit_selector() -> None:
    st.markdown('<div class="nav-section">Performance</div>', unsafe_allow_html=True)
    st.selectbox(
        "Patients loaded from CSV",
        options=CSV_REGISTRY_LIMIT_OPTIONS,
        index=_default_registry_limit_index(),
        format_func=_csv_registry_limit_label,
        key="csv_registry_limit",
        help=(
            "Caps rows read from the active source. Choose **All patients** for "
            "full Cohort Discovery (symbolic-only, fast). Patient Matching still "
            "limits BioBERT runs separately."
        ),
    )

def _build_sidebar_content(page_name: str) -> tuple[str | None, dict[str, Any] | None]:
    """Render page-specific sidebar controls and return their payloads."""
    quick_note = None
    cohort_criteria = None

    if page_name == "Patient Matching":
        st.markdown('<div class="nav-section">Quick Entry</div>', unsafe_allow_html=True)
        quick_note = build_quick_note()
    elif page_name == "Cohort Discovery":
        st.markdown('<div class="nav-section">Criteria Builder</div>', unsafe_allow_html=True)
        cohort_criteria = build_cohort_criteria()

    return quick_note, cohort_criteria

def _render_sidebar() -> tuple[str, str | None, dict[str, Any] | None]:
    """Render the shared sidebar and return the active page inputs."""
    with st.sidebar:
        render_sidebar_brand()
        page_name = st.radio(
            "Main navigation",
            list(PAGES.keys()),
            label_visibility="collapsed",
        )

        _render_data_source_selector()
        _render_registry_limit_selector()
        quick_note, cohort_criteria = _build_sidebar_content(page_name)

        st.markdown("---")
        st.markdown(
            '<div class="disclaimer" style="margin-top:.5rem;">'
            'Research prototype. Local CSV data only. Not for clinical use.'
            '</div>',
            unsafe_allow_html=True,
        )

    return page_name, quick_note, cohort_criteria

def _render_active_page(
    page_name: str,
    quick_note: str | None,
    cohort_criteria: dict[str, Any] | None,
) -> None:
    """Dispatch the main content area for the selected page."""
    if page_name == "Patient Matching":
        page_matching(quick_note)
        return

    if page_name == "Cohort Discovery":
        page_cohort(cohort_criteria)
        return

    PAGES[page_name]()

def main() -> None:
    _check_runtime_deps()
    inject_theme()
    page_name, quick_note, cohort_criteria = _render_sidebar()
    _render_active_page(page_name, quick_note, cohort_criteria)

    render_footer()

if __name__ == "__main__":
    main()
