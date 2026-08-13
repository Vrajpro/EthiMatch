"""Shared Streamlit accessors for page modules."""

from __future__ import annotations

from typing import Any

import streamlit as st

from data_access.loader import normalise_source
from services.patient_service import data_source_label as _data_source_label_svc
from services.patient_service import registry_limit_for_provider as _limit_for_provider
from services.patient_service import registry_limit_label as _limit_label
from services.runtime import load_patient_registry
from services.session_service import clear_screening_cache_if_changed
import config as _cfg

DEFAULT_CSV_UI_PATIENT_LIMIT: int = getattr(_cfg, "DEFAULT_CSV_UI_PATIENT_LIMIT", 100)
CSV_REGISTRY_LIMIT_ALL: int = getattr(_cfg, "CSV_REGISTRY_LIMIT_ALL", 0)
MATCHING_BIOBERT_BATCH_DEFAULT: int = getattr(_cfg, "MATCHING_BIOBERT_BATCH_DEFAULT", 25)
MATCHING_BIOBERT_BATCH_MAX: int = getattr(_cfg, "MATCHING_BIOBERT_BATCH_MAX", 100)

def registry_limit() -> int:
    return int(st.session_state.get("csv_registry_limit", DEFAULT_CSV_UI_PATIENT_LIMIT))

def active_data_source() -> str:
    return normalise_source(st.session_state.get("data_source", "Synthea"))

def data_source_label() -> str:
    return _data_source_label_svc(active_data_source())

def get_patient_provider():
    return load_patient_registry(
        active_data_source(),
        _limit_for_provider(registry_limit(), CSV_REGISTRY_LIMIT_ALL),
    )

def registry_limit_label() -> str:
    return _limit_label(registry_limit(), CSV_REGISTRY_LIMIT_ALL)

def clear_cache_if_needed() -> None:
    clear_screening_cache_if_changed(st.session_state, active_data_source(), registry_limit())

def quick_entry_fields() -> dict[str, Any]:
    return {
        "qe_age": st.session_state.get("qe_age", 55),
        "qe_gender": st.session_state.get("qe_gender", "male"),
        "qe_disease": st.session_state.get("qe_disease", ""),
        "qe_stage": st.session_state.get("qe_stage", "IIIA"),
        "qe_bio": st.session_state.get("qe_bio", []),
        "qe_bmi": st.session_state.get("qe_bmi", 25.0),
        "qe_ecog": st.session_state.get("qe_ecog", 1),
        "qe_comorb": st.session_state.get("qe_comorb", []),
        "qe_rx": st.session_state.get("qe_rx", []),
        "qe_neg": st.session_state.get("qe_neg"),
    }
