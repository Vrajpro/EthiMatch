"""Streamlit page package — thin UI wrappers over services/."""

from ui.pages.cohort import page_cohort
from ui.pages.dashboard import page_dashboard
from ui.pages.evaluation import page_evaluation
from ui.pages.matching import page_matching
from ui.pages.sidebar import build_cohort_criteria, build_quick_note

__all__ = [
    "build_cohort_criteria",
    "build_quick_note",
    "page_cohort",
    "page_dashboard",
    "page_evaluation",
    "page_matching",
]
