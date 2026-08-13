"""Sidebar builders for Quick Entry and Cohort criteria."""

from __future__ import annotations

from typing import Any

import streamlit as st

from config import (
    AGE_MAX,
    AGE_MIN,
    ALLOWED_STAGES,
    BIOMARKERS,
    BMI_COHORT_MAX_DEFAULT,
    BMI_MAX,
    BMI_MIN,
    COHORT_DISEASE_DEFAULTS,
    COHORT_EXCLUDED_COMORBIDITY_DEFAULTS,
    COHORT_EXCLUDED_THERAPY_DEFAULTS,
    COHORT_REQUIRED_BIOMARKER_OPTIONS,
    COHORT_STAGE_DEFAULTS,
    COMORBIDITIES,
    ECOG_LEVELS,
    ECOG_MAX_LEVELS,
    GENDERS,
    PRIOR_THERAPIES,
    disease_code_from_display,
    disease_display_options,
    disease_label_for_code,
)
from services.matching_service import compose_quick_entry_note
from services.runtime import get_registered_trials
from trial_registry import trial_select_label
from ui.components import _esc, render_clinical_notice, render_hint_text
from ui.pages._common import quick_entry_fields

def build_quick_note() -> str | None:
    st.markdown('<div class="sidebar-section-title">Quick Entry Builder</div>', unsafe_allow_html=True)
    render_hint_text(
        "Builds **one test note** for the instant screen button. "
        "For CSV batch, only **disease** can be reused as a filter — not age, stage, or ECOG."
    )

    st.slider("Age", AGE_MIN, AGE_MAX, 55, key="qe_age")
    st.selectbox("Gender", GENDERS, key="qe_gender")
    st.selectbox("Primary Disease", disease_display_options(), key="qe_disease")
    st.selectbox("Stage", ALLOWED_STAGES, index=ALLOWED_STAGES.index("IIIA"), key="qe_stage")
    st.multiselect("Biomarkers", BIOMARKERS, key="qe_bio")
    st.number_input("BMI", BMI_MIN, BMI_MAX, 25.0, 0.5, key="qe_bmi")
    st.selectbox("ECOG PS", ECOG_LEVELS, index=1, key="qe_ecog")
    st.multiselect("Comorbidities", COMORBIDITIES, key="qe_comorb")
    st.multiselect("Prior Therapies", PRIOR_THERAPIES, key="qe_rx")
    st.checkbox("Test negation handling: include 'patient denies diabetes'", key="qe_neg")

    if st.button("Generate Clinical Note", use_container_width=True, key="qe_btn"):
        note = compose_quick_entry_note(quick_entry_fields())
        st.session_state["quick_entry_note"] = note
        return note

    stored = st.session_state.get("quick_entry_note")
    if stored:
        st.markdown(
            '<div class="sidebar-note-panel">'
            '<div class="sidebar-note-title">Generated note (ready to screen)</div>'
            f'<div class="sidebar-note-body">{_esc(stored)}</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    return stored

def build_cohort_criteria() -> dict[str, Any] | None:
    st.markdown("**Trial Criteria Builder**")

    trials = get_registered_trials()
    if not trials:
        render_clinical_notice("No trial protocols found in the trials/ folder.", "FAIL")
        return None

    trial_labels = [trial_select_label(t) for t in trials]
    trial_by_label = dict(zip(trial_labels, trials))
    selected_label = st.selectbox(
        "Registered trial protocol",
        trial_labels,
        key="cd_registered_trial",
        help="Protocols are loaded from JSON/YAML files in trials/",
    )
    selected_trial = trial_by_label[selected_label]
    if selected_trial.get("description"):
        st.caption(selected_trial["description"])

    criteria_mode = st.radio(
        "Screening criteria",
        ["Use registered protocol", "Custom criteria builder"],
        horizontal=True,
        key="cd_criteria_mode",
    )

    if criteria_mode == "Use registered protocol":
        inc = selected_trial["inclusion"]
        excl = selected_trial.get("exclusion", {})
        with st.expander("Protocol summary", expanded=False):
            st.markdown(f"**Trial:** {selected_trial['trial_name']}")
            st.markdown(f"- Age: {inc.get('age_min')}–{inc.get('age_max')}")
            st.markdown(f"- Diseases: {', '.join(inc.get('diseases', []))}")
            st.markdown(f"- Stages: {', '.join(inc.get('stages', []))}")
            st.markdown(f"- ECOG ≤ {inc.get('ecog_max')}")
            st.markdown(f"- BMI ≤ {inc.get('bmi_max')}")
            comorb = excl.get("excluded_comorbidities") or ["None"]
            st.markdown(f"- Excluded comorbidities: {', '.join(comorb)}")
        if st.button("Search Cohort", type="primary", use_container_width=True):
            return {"registered_trial": selected_trial}
        return None

    st.caption("Define custom inclusion and exclusion criteria for cohort screening.")
    st.markdown("**Inclusion**")
    age_range = st.slider("Age Range", AGE_MIN, AGE_MAX, (40, 75), key="cd_age")
    genders = st.multiselect("Eligible Genders", GENDERS, default=GENDERS, key="cd_gender")
    diseases = st.multiselect(
        "Target Diseases",
        disease_display_options(),
        default=[disease_label_for_code(d) for d in COHORT_DISEASE_DEFAULTS],
        key="cd_dis",
    )
    diseases = [disease_code_from_display(d) or d for d in diseases]
    stages = st.multiselect("Eligible Stages", ALLOWED_STAGES, default=COHORT_STAGE_DEFAULTS, key="cd_stg")
    ecog_max = st.selectbox("Maximum ECOG PS", ECOG_MAX_LEVELS, index=2, key="cd_ecog")
    bmi_max = st.number_input("Maximum BMI", BMI_MIN, BMI_MAX, BMI_COHORT_MAX_DEFAULT, key="cd_bmi")
    req_bio = st.multiselect("Required Biomarkers", COHORT_REQUIRED_BIOMARKER_OPTIONS, key="cd_bio")

    st.markdown("**Exclusion**")
    excl_comorb = st.multiselect(
        "Excluded Comorbidities", COMORBIDITIES, default=COHORT_EXCLUDED_COMORBIDITY_DEFAULTS, key="cd_exc",
    )
    excl_rx = st.multiselect(
        "Excluded Prior Therapies", PRIOR_THERAPIES, default=COHORT_EXCLUDED_THERAPY_DEFAULTS, key="cd_rx",
    )

    if st.button("Search Cohort", type="primary", use_container_width=True):
        return {
            "age_min": age_range[0],
            "age_max": age_range[1],
            "gender": genders,
            "diseases": diseases,
            "stages": stages,
            "ecog_max": ecog_max,
            "bmi_max": bmi_max,
            "required_biomarkers": req_bio,
            "excluded_comorbidities": excl_comorb,
            "excluded_prior_therapies": excl_rx,
        }
    return None
