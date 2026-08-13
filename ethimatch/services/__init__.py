"""Backend services — business logic without Streamlit widgets."""

from services.cohort_service import (
    build_cohort_export_data,
    build_user_trial_from_criteria,
    cohort_export_csv,
    cohort_result_counts,
    parse_criteria_for_display,
    run_cohort_screening,
)
from services.evaluation_service import (
    SOURCE_KEYS,
    available_evaluation_sources,
    evaluation_patient_limits,
    load_saved_evaluation,
    run_comparative_evaluation,
    run_evaluation_request,
)
from services.matching_service import (
    build_matching_export_data,
    build_quick_entry_profile,
    compose_quick_entry_note,
    extraction_path_label,
    finalize_audit_with_profile,
    resolve_batch_filter,
    run_csv_batch_screening,
    run_quick_entry_screening,
    sort_matching_results,
)
from services.patient_service import (
    data_source_label,
    load_dashboard_registry,
    registry_limit_for_provider,
    registry_limit_label,
)
from services.runtime import get_registered_trials, load_patient_registry, load_pipeline
from services.session_service import clear_screening_cache_if_changed
from services.trial_format import (
    format_trial_age_html,
    format_trial_exclusions_html,
    format_trial_inclusion_html,
)

__all__ = [
    "build_cohort_export_data",
    "build_matching_export_data",
    "build_user_trial_from_criteria",
    "available_evaluation_sources",
    "cohort_export_csv",
    "cohort_result_counts",
    "evaluation_patient_limits",
    "parse_criteria_for_display",
    "load_saved_evaluation",
    "run_comparative_evaluation",
    "run_cohort_screening",
    "run_evaluation_request",
    "SOURCE_KEYS",
    "build_quick_entry_profile",
    "clear_screening_cache_if_changed",
    "compose_quick_entry_note",
    "data_source_label",
    "extraction_path_label",
    "finalize_audit_with_profile",
    "format_trial_age_html",
    "format_trial_exclusions_html",
    "format_trial_inclusion_html",
    "get_registered_trials",
    "load_dashboard_registry",
    "load_patient_registry",
    "load_pipeline",
    "registry_limit_for_provider",
    "registry_limit_label",
    "resolve_batch_filter",
    "run_csv_batch_screening",
    "run_quick_entry_screening",
    "sort_matching_results",
]
