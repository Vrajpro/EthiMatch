"""Cached pipeline and registry loaders."""

from __future__ import annotations

from typing import Any

import streamlit as st

from data_access.loader import load_provider
from ethimatch_pipeline import EthiMatchPipeline
from trial_registry import load_all_trials, trials_for_export

@st.cache_resource(show_spinner="Initializing BioBERT model…")
def load_pipeline() -> EthiMatchPipeline:
    return EthiMatchPipeline(verbose=False)

@st.cache_resource(show_spinner="Loading patient registry…")
def load_patient_registry(source: str, max_patients: int | None):
    return load_provider(source=source, limit=max_patients)

@st.cache_data(show_spinner=False)
def get_registered_trials() -> list[dict[str, Any]]:
    return trials_for_export(load_all_trials())
