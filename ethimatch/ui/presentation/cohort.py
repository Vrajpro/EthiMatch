"""Cohort screening banners, filters, and detail panels."""
from __future__ import annotations

from typing import Any

import streamlit as st

from data_access.interfaces import PatientDataProvider
from ethimatch_pipeline import CohortResult
from symbolic_validator import SymbolicValidator
from xai_explainer import ENTITY_LABELS

from ui.presentation._utils import _esc, resolve_patient_profile
from ui.presentation.clinical import render_entity_card, render_trial_card
from ui.presentation.layout import clinical_panel, render_clinical_notice, render_status_metric
from ui.presentation.verdict import cohort_verdict_label, render_verdict_pill_html

def render_cohort_banner(eligible: int, conditional: int, ineligible: int, total: int) -> None:
    """Screening summary metrics with semantic status colors (dark text on soft fills)."""
    stats = [
        ("Eligible", eligible, "PASS"),
        ("Inconclusive", conditional, "INCONCLUSIVE"),
        ("Ineligible", ineligible, "FAIL"),
        ("Screened", total, "NEUTRAL"),
    ]
    cols = st.columns(len(stats))
    for col, (label, value, token) in zip(cols, stats):
        with col:
            render_status_metric(label, str(value), token)

def filter_cohort_results(
    results: list[CohortResult],
    *,
    verdict_filter: str,
    search_query: str,
) -> list[CohortResult]:
    filtered = results
    if verdict_filter == "Eligible":
        filtered = [r for r in filtered if r.is_eligible]
    elif verdict_filter == "Inconclusive":
        filtered = [r for r in filtered if r.is_conditional]
    elif verdict_filter == "Ineligible":
        filtered = [r for r in filtered if not r.is_eligible and not r.is_conditional]

    query = search_query.strip().lower()
    if not query:
        return filtered

    def _matches(r: CohortResult) -> bool:
        p = r.patient_profile
        haystack = " ".join(
            str(x)
            for x in (
                r.patient_id,
                p.disease if p else "",
                p.stage if p else "",
                p.gender if p else "",
            )
        ).lower()
        return query in haystack or query in r.patient_id.lower()

    return [r for r in filtered if _matches(r)]

def build_cohort_master_table(results: list[CohortResult]) -> "Any":
    """Build a patient registry table for the master list panel."""
    import pandas as pd

    rows: list[dict[str, Any]] = []
    for r in results:
        p = resolve_patient_profile(r.patient_id, r.patient_profile)
        verdict, _ = cohort_verdict_label(r)
        report = r.trial_reports[0] if r.trial_reports else None
        score = SymbolicValidator.match_score(report) if report else 0.0
        rows.append({
            "Patient ID": r.patient_id,
            "Verdict": verdict,
            "Disease": p.disease if p and p.disease else "—",
            "Stage": p.stage if p and p.stage else "—",
            "Age": p.age if p and p.age is not None else "—",
            "Match %": score,
        })
    return pd.DataFrame(rows)

def render_cohort_detail_panel(
    result: CohortResult,
    provider: PatientDataProvider | None = None,
) -> None:
    """Detail view — ValidationReport + XAI narrative from session-stored results."""
    p = resolve_patient_profile(result.patient_id, result.patient_profile, provider)
    verdict, verdict_cls = cohort_verdict_label(result)
    report = result.trial_reports[0] if result.trial_reports else None

    if p is None or report is None:
        render_clinical_notice("No validation data available for this patient.", "FAIL")
        return

    entities = dict(result.extracted_entities or {})
    from ethimatch_pipeline import reconcile_entities_with_profile
    entities = reconcile_entities_with_profile(entities, p)

    score = SymbolicValidator.match_score(report)
    with clinical_panel("Patient Record"):
        head_l, head_r = st.columns([3, 1])
        with head_l:
            st.markdown(f"**`{result.patient_id}`**")
        with head_r:
            st.markdown(render_verdict_pill_html(verdict), unsafe_allow_html=True)
            st.metric("Match Score", f"{score:.0f}%")
        d1, d2, d3, d4, d5, d6 = st.columns(6)
        d1.metric("Age", p.age if p.age is not None else "—")
        d2.metric("Gender", (p.gender or "—").title())
        d3.metric("Disease", p.disease or "—")
        d4.metric("Stage", p.stage or "—")
        d5.metric("BMI", p.bmi if p.bmi is not None else "—")
        d6.metric("ECOG", p.ecog_ps if p.ecog_ps is not None else "—")

    if result.fail_reasons:
        render_clinical_notice(
            "Blocking criteria: " + "; ".join(result.fail_reasons[:3]),
            "FAIL",
        )

    with clinical_panel("Symbolic Validation Report"):
        render_trial_card(report, entities, expanded=False)

    if entities:
        with clinical_panel("Extracted Clinical Entities"):
            st.markdown('<div class="entity-grid">', unsafe_allow_html=True)
            conf = entities.get("confidence_scores", {})
            sources = entities.get("extraction_sources", {})
            negated_keys = {n.split(":")[0] for n in entities.get("negated_fields", [])}
            for key, label in ENTITY_LABELS.items():
                render_entity_card(
                    label,
                    entities.get(key),
                    conf.get(key),
                    sources.get(key),
                    negated=key.rstrip("s") in negated_keys or key in negated_keys,
                )
            st.markdown("</div>", unsafe_allow_html=True)

def render_patient_row(
    patient_id: str,
    verdict: str,
    verdict_cls: str,
    meta_parts: list[str],
    fail_reasons: list[str],
) -> str:
    meta = "".join(f"<span>{_esc(p)}</span>" for p in meta_parts)
    reasons = "".join(f'<div class="fail-reason">{_esc(r)}</div>' for r in fail_reasons)
    return (
        f'<div class="patient-row"><div class="patient-row-head">'
        f'<span class="patient-id">{_esc(patient_id)}</span>'
        f'<span class="verdict-pill {verdict_cls}">{_esc(verdict)}</span></div>'
        f'<div class="patient-meta">{meta}</div>{reasons}</div>'
    )
