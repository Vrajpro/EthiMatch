"""Patient registries, inline detail panels, and master tables."""
from __future__ import annotations

from typing import Any

import streamlit as st

from data_access.interfaces import PatientDataProvider
from ethimatch_pipeline import AuditReport, CohortResult, MatchingPatientResult
from symbolic_validator import SymbolicValidator, ValidationReport
from trial_registry import get_trial_by_id
from xai_explainer import ENTITY_LABELS, build_clinical_narrative, build_executive_summary

from ui.presentation._utils import (
    _esc,
    _records_to_dataframe,
    _short_patient_id,
    resolve_patient_profile,
)
from ui.presentation.clinical import (
    render_entity_card,
    render_matching_extraction_panel,
    render_symbolic_audit_panel,
    render_trial_card,
)
from ui.presentation.layout import (
    clinical_panel,
    render_clinical_notice,
    render_hint_text,
    render_section,
)
from ui.presentation.cohort import filter_cohort_results
from ui.presentation.verdict import (
    _registry_verdict_css,
    cohort_verdict_label,
    matching_registry_verdict,
    matching_verdict_label,
    render_verdict_pill_html,
)

REGISTRY_PAGE_SIZE = 15

def filter_matching_results(
    results: list[MatchingPatientResult],
    *,
    verdict_filter: str,
    search_query: str,
) -> list[MatchingPatientResult]:
    filtered = results
    if verdict_filter == "Eligible":
        filtered = [
            r for r in filtered
            if matching_registry_verdict(r.audit_report)[0] == "Eligible"
        ]
    elif verdict_filter in ("Inconclusive", "Conditional"):
        filtered = [
            r for r in filtered
            if matching_registry_verdict(r.audit_report)[0] in ("Inconclusive", "Conditional")
        ]
    elif verdict_filter == "Blocked":
        filtered = [
            r for r in filtered
            if matching_registry_verdict(r.audit_report)[0] == "Blocked"
        ]

    query = search_query.strip().lower()
    if not query:
        return filtered

    def _matches(r: MatchingPatientResult) -> bool:
        p = r.patient_profile
        entities, _ = resolve_audit_display(r.audit_report, p)
        disease_disp, _ = format_registry_disease_cell(p, entities)
        haystack = " ".join(
            str(x)
            for x in (
                r.patient_id,
                disease_disp,
                p.stage if p else entities.get("stage", ""),
                p.gender if p else entities.get("gender", ""),
            )
        ).lower()
        return query in haystack or query in r.patient_id.lower()

    return [r for r in filtered if _matches(r)]

def display_registry_disease(
    profile: Any | None,
    entities: dict[str, Any] | None = None,
) -> str:
    """Best available disease label for registry rows (trial code or raw condition)."""
    if profile is not None and profile.disease:
        return profile.disease
    if entities:
        ent_disease = entities.get("disease")
        if ent_disease not in (None, "", "—"):
            return str(ent_disease)
    if profile is not None:
        from config import normalize_disease

        active = getattr(profile, "active_conditions", None) or []
        for cond in active:
            mapped = normalize_disease(cond)
            if mapped:
                return mapped
            if cond and str(cond).strip():
                text = str(cond).strip()
                return text[:34] + ("…" if len(text) > 34 else "")
        for cond in profile.comorbidities or []:
            mapped = normalize_disease(cond)
            if mapped:
                return mapped
    return "—"

def format_registry_disease_cell(
    profile: Any | None,
    entities: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Return (compact display, full tooltip) for the registry Disease column."""
    disease = display_registry_disease(profile, entities)
    if disease == "—":
        return "—", "No mapped disease or active condition"

    stage = None
    if profile is not None and profile.stage:
        stage = profile.stage
    elif entities and entities.get("stage"):
        stage = entities.get("stage")

    tooltip_parts = [disease]
    if stage:
        tooltip_parts.append(f"Stage {stage}")
    if profile is not None:
        active = getattr(profile, "active_conditions", None) or []
        if active:
            tooltip_parts.append("Conditions: " + "; ".join(active[:4]))
            if len(active) > 4:
                tooltip_parts[-1] += f" (+{len(active) - 4} more)"

    display = disease if not stage else f"{disease} · {stage}"
    if len(display) > 38:
        display = display[:35] + "…"
    return display, " · ".join(tooltip_parts)

def resolve_audit_display(
    audit: AuditReport,
    profile: Any | None = None,
    provider: PatientDataProvider | None = None,
) -> tuple[dict[str, Any], list[ValidationReport]]:
    """Reconcile entities with profile and refresh rule audits so UI tabs agree."""
    from ethimatch_pipeline import reconcile_entities_with_profile

    patient_id = audit.patient_id or (profile.patient_id if profile else "")
    resolved = resolve_patient_profile(patient_id, profile, provider)
    entities = dict(audit.extracted_entities or {})
    if resolved is not None:
        entities = reconcile_entities_with_profile(entities, resolved)

    validator = SymbolicValidator()
    refreshed: list[ValidationReport] = []
    for report in audit.trial_reports:
        trial = get_trial_by_id(report.trial_id)
        if trial:
            refreshed.append(validator.validate(entities, trial))
        else:
            refreshed.append(report)
    return entities, refreshed

def _matching_row_fields(r: MatchingPatientResult) -> dict[str, Any]:
    verdict, _, score = matching_registry_verdict(r.audit_report)
    p = resolve_patient_profile(r.patient_id, r.patient_profile)
    entities, trial_reports = resolve_audit_display(
        r.audit_report, r.patient_profile, provider=None,
    )
    disease_display, disease_tooltip = format_registry_disease_cell(p, entities)
    # Registry status from reconciled primary trial (matches Audit tab).
    primary = SymbolicValidator.best_trial_report(trial_reports)
    if primary is not None:
        verdict = matching_verdict_label(primary)
        score = SymbolicValidator.match_score(primary)
    return {
        "patient_id": r.patient_id,
        "age": p.age if p and p.age is not None else entities.get("age", "—"),
        "gender": (p.gender or entities.get("gender") or "—").title() if p or entities.get("gender") else "—",
        "disease": disease_display,
        "disease_tooltip": disease_tooltip,
        "stage": (p.stage if p and p.stage else entities.get("stage")) or "—",
        "status": verdict,
        "primary_trial": primary.trial_id if primary is not None else "—",
        "match_pct": f"{score:.0f}%",
    }

def _cohort_row_fields(r: CohortResult) -> dict[str, Any]:
    p = resolve_patient_profile(r.patient_id, r.patient_profile)
    entities = dict(r.extracted_entities or {})
    if p is not None:
        from ethimatch_pipeline import reconcile_entities_with_profile
        entities = reconcile_entities_with_profile(entities, p)
    disease_display, disease_tooltip = format_registry_disease_cell(p, entities)
    report = r.trial_reports[0] if r.trial_reports else None
    score = SymbolicValidator.match_score(report) if report else 0.0
    verdict, _ = cohort_verdict_label(r)
    if report is not None:
        if report.eligible and not report.is_conditionally_eligible:
            verdict = "Eligible"
        elif report.is_conditionally_eligible:
            verdict = "Inconclusive"
        else:
            verdict = "Ineligible"
        score = SymbolicValidator.match_score(report)
    return {
        "patient_id": r.patient_id,
        "age": p.age if p and p.age is not None else entities.get("age", "—"),
        "gender": (p.gender or entities.get("gender") or "—").title() if p or entities.get("gender") else "—",
        "disease": disease_display,
        "disease_tooltip": disease_tooltip,
        "stage": (p.stage if p and p.stage else entities.get("stage")) or "—",
        "verdict": verdict,
        "match_pct": f"{score:.0f}%",
    }

def _registry_page_slice(
    items: list[Any],
    page_key: str,
) -> tuple[list[Any], int, int]:
    total_pages = max(1, (len(items) + REGISTRY_PAGE_SIZE - 1) // REGISTRY_PAGE_SIZE)
    page = int(st.session_state.get(page_key, 1))
    page = max(1, min(page, total_pages))
    st.session_state[page_key] = page
    start = (page - 1) * REGISTRY_PAGE_SIZE
    return items[start : start + REGISTRY_PAGE_SIZE], page, total_pages

def _render_registry_pagination(
    page: int,
    total_pages: int,
    total_items: int,
    *,
    prev_key: str,
    next_key: str,
    page_key: str,
) -> None:
    c_prev, c_mid, c_next = st.columns([1, 2.2, 1])
    with c_prev:
        if st.button("◀ Previous", disabled=page <= 1, key=prev_key, use_container_width=True):
            st.session_state[page_key] = page - 1
            st.rerun()
    with c_mid:
        render_hint_text(
            f"Page **{page}** of **{total_pages}** · **{total_items}** patients · "
            "click **☐** to expand details below the row"
        )
    with c_next:
        if st.button("Next ▶", disabled=page >= total_pages, key=next_key, use_container_width=True):
            st.session_state[page_key] = page + 1
            st.rerun()

def _registry_toggle_box(
    patient_id: str,
    expanded_id: str | None,
    session_key: str,
    widget_key: str,
) -> None:
    is_open = expanded_id == patient_id
    st.markdown('<div class="registry-select-btn">', unsafe_allow_html=True)
    if st.button(
        "☑" if is_open else "☐",
        key=widget_key,
        help="Expand or collapse patient details",
    ):
        st.session_state[session_key] = None if is_open else patient_id
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def _render_registry_header(labels: list[str], weights: list[float]) -> None:
    cols = st.columns(weights)
    for col, label in zip(cols, labels):
        with col:
            st.markdown(f"**{label}**" if label else "")

def _render_registry_data_row(
    fields: dict[str, Any],
    *,
    expanded_id: str | None,
    session_key: str,
    widget_key: str,
    column_keys: list[str],
    weights: list[float],
) -> None:
    pid = fields["patient_id"]
    is_open = expanded_id == pid
    cols = st.columns(weights)
    with cols[0]:
        _registry_toggle_box(pid, expanded_id, session_key, widget_key)
    for col, key in zip(cols[1:], column_keys):
        with col:
            value = fields.get(key, "—")
            if key == "patient_id":
                st.markdown(
                    f'<span class="patient-id" title="{_esc(pid)}">{_esc(_short_patient_id(pid))}</span>',
                    unsafe_allow_html=True,
                )
            elif key in ("status", "verdict"):
                _, css = _registry_verdict_css(str(value))
                st.markdown(
                    f'<span class="verdict-pill {css}">{_esc(str(value))}</span>',
                    unsafe_allow_html=True,
                )
            elif key == "disease":
                tooltip = fields.get("disease_tooltip", str(value))
                st.markdown(
                    f'<span style="font-size:.84rem;" title="{_esc(tooltip)}">'
                    f'{_esc(str(value))}</span>',
                    unsafe_allow_html=True,
                )
            elif key == "primary_trial":
                st.markdown(
                    f'<span class="patient-id" title="Primary trial driving this row">'
                    f'{_esc(str(value))}</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<span style="font-size:.84rem;">{_esc(str(value))}</span>',
                    unsafe_allow_html=True,
                )
    if is_open:
        st.markdown(
            '<div style="height:2px;background:var(--brand,#0b6e99);margin:.15rem 0 .35rem;border-radius:2px;"></div>',
            unsafe_allow_html=True,
        )

def render_matching_detail_inline(
    result: MatchingPatientResult,
    provider: PatientDataProvider | None = None,
) -> None:
    """Compact inline detail — shown below the selected registry row."""
    p = resolve_patient_profile(result.patient_id, result.patient_profile, provider)
    audit = result.audit_report
    entities, trial_reports = resolve_audit_display(audit, p, provider)
    primary = SymbolicValidator.best_trial_report(trial_reports)

    st.markdown('<div class="registry-detail-inline" style="border:none;box-shadow:none;background:transparent;padding:.25rem 0 0;margin:0;">', unsafe_allow_html=True)

    if p is None and result.patient_id != "QUICK-ENTRY":
        render_clinical_notice("Patient profile not available.", "FAIL")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if primary is not None:
        verdict = matching_verdict_label(primary)
        score = SymbolicValidator.match_score(primary)
    else:
        verdict, _, score = matching_registry_verdict(audit)

    trial_label = primary.trial_id if primary is not None else "—"
    st.markdown(
        f'<div class="registry-detail-header">'
        f'<span class="patient-id">{_esc(result.patient_id)}</span>'
        f'{render_verdict_pill_html(verdict)}'
        f'<span class="registry-match-score">'
        f'Match {score:.0f}% · Primary trial <code>{_esc(trial_label)}</code>'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    d1, d2, d3, d4, d5, d6 = st.columns(6)
    d1.metric("Age", entities.get("age") if entities.get("age") is not None else (p.age if p else "—"))
    d2.metric("Gender", (entities.get("gender") or (p.gender if p else None) or "—").title())
    d3.metric("Disease", display_registry_disease(p, entities))
    d4.metric("Stage", entities.get("stage") or (p.stage if p else None) or "—")
    d5.metric("BMI", entities.get("bmi") if entities.get("bmi") is not None else (p.bmi if p else "—"))
    d6.metric("ECOG", entities.get("ecog_ps") if entities.get("ecog_ps") is not None else (p.ecog_ps if p else "—"))

    if result.patient_id == "QUICK-ENTRY":
        st.text_area("Clinical note", audit.raw_note, height=120, disabled=True)

    tab_narr, tab_ent, tab_audit = st.tabs(["Narrative", "Entities", "Audit"])
    with tab_narr:
        if primary is not None:
            st.markdown(build_clinical_narrative(primary, entities))
        elif audit.xai_narrative:
            st.markdown(audit.xai_narrative)
        else:
            st.caption("No narrative available.")
    with tab_ent:
        if entities:
            render_matching_extraction_panel(entities)
        else:
            st.caption("No extracted entities.")
    with tab_audit:
        render_symbolic_audit_panel(trial_reports)

    st.markdown("</div>", unsafe_allow_html=True)

def render_cohort_detail_inline(
    result: CohortResult,
    provider: PatientDataProvider | None = None,
) -> None:
    """Compact inline detail for cohort registry rows."""
    p = resolve_patient_profile(result.patient_id, result.patient_profile, provider)
    report = result.trial_reports[0] if result.trial_reports else None

    st.markdown('<div class="registry-detail-inline" style="border:none;box-shadow:none;background:transparent;padding:.25rem 0 0;margin:0;">', unsafe_allow_html=True)

    if p is None or report is None:
        render_clinical_notice("No validation data available for this patient.", "FAIL")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    from ethimatch_pipeline import reconcile_entities_with_profile
    entities = reconcile_entities_with_profile(dict(result.extracted_entities or {}), p)
    validator = SymbolicValidator()
    trial = get_trial_by_id(report.trial_id)
    trial_reports = (
        [validator.validate(entities, trial)]
        if trial
        else list(result.trial_reports)
    )
    report = trial_reports[0]
    if report.eligible and not report.is_conditionally_eligible:
        verdict = "Eligible"
    elif report.is_conditionally_eligible:
        verdict = "Inconclusive"
    else:
        verdict = "Ineligible"
    score = SymbolicValidator.match_score(report)

    st.markdown(
        f'<div class="registry-detail-header">'
        f'<span class="patient-id">{_esc(result.patient_id)}</span>'
        f'{render_verdict_pill_html(verdict)}'
        f'<span class="registry-match-score">Match {score:.0f}%</span></div>',
        unsafe_allow_html=True,
    )

    d1, d2, d3, d4, d5, d6 = st.columns(6)
    d1.metric("Age", entities.get("age") if entities.get("age") is not None else "—")
    d2.metric("Gender", (entities.get("gender") or "—").title())
    d3.metric("Disease", display_registry_disease(p, entities))
    d4.metric("Stage", entities.get("stage") or "—")
    d5.metric("BMI", entities.get("bmi") if entities.get("bmi") is not None else "—")
    d6.metric("ECOG", entities.get("ecog_ps") if entities.get("ecog_ps") is not None else "—")

    if result.fail_reasons:
        render_clinical_notice(
            "Blocking: " + "; ".join(result.fail_reasons[:2]),
            "FAIL",
        )

    tab_val, tab_ent, tab_audit = st.tabs(["Summary", "Entities", "Audit"])
    with tab_val:
        render_trial_card(report, entities, expanded=False)
    with tab_ent:
        if entities:
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
    with tab_audit:
        render_symbolic_audit_panel(trial_reports)

    st.markdown("</div>", unsafe_allow_html=True)

_MATCHING_REGISTRY_WEIGHTS = [0.05, 0.16, 0.06, 0.07, 0.12, 0.07, 0.10, 0.10, 0.09]

_MATCHING_REGISTRY_COLS = [
    "patient_id", "age", "gender", "disease", "stage", "status", "primary_trial", "match_pct",
]

_COHORT_REGISTRY_WEIGHTS = [0.05, 0.22, 0.07, 0.08, 0.14, 0.08, 0.14, 0.09]

_COHORT_REGISTRY_COLS = ["patient_id", "age", "gender", "disease", "stage", "verdict", "match_pct"]

def render_matching_expandable_registry(
    results: list[MatchingPatientResult],
    provider: PatientDataProvider | None = None,
) -> None:
    """Single-column registry: row list + inline expand below selected patient."""
    filter_col, search_col = st.columns([1, 1.4])
    with filter_col:
        st.selectbox(
            "Status filter",
            ["All", "Eligible", "Inconclusive", "Blocked"],
            key="matching_master_filter",
            label_visibility="collapsed",
        )
    with search_col:
        st.text_input(
            "Search patients",
            key="matching_master_search",
            placeholder="Search ID, disease, stage…",
            label_visibility="collapsed",
        )

    filtered = filter_matching_results(
        results,
        verdict_filter=st.session_state.get("matching_master_filter", "All"),
        search_query=st.session_state.get("matching_master_search", ""),
    )
    st.caption(f"{len(filtered)} of {len(results)} patients")

    if not filtered:
        render_clinical_notice("No patients match the current filter.", "INCONCLUSIVE")
        return

    page_items, page, total_pages = _registry_page_slice(filtered, "matching_registry_page")
    expanded_id = st.session_state.get("matching_selected_patient_id")
    visible_ids = {r.patient_id for r in page_items}
    if expanded_id and expanded_id not in visible_ids:
        expanded_id = None

    _render_registry_pagination(
        page, total_pages, len(filtered),
        prev_key="matching_registry_prev",
        next_key="matching_registry_next",
        page_key="matching_registry_page",
    )

    _render_registry_header(
        ["", "Patient ID", "Age", "Gender", "Disease", "Stage", "Status", "Trial", "Match %"],
        _MATCHING_REGISTRY_WEIGHTS,
    )

    by_id = {r.patient_id: r for r in filtered}
    for r in page_items:
        fields = _matching_row_fields(r)
        pid = r.patient_id
        is_open = st.session_state.get("matching_selected_patient_id") == pid
        with st.container(border=True):
            _render_registry_data_row(
                fields,
                expanded_id=expanded_id,
                session_key="matching_selected_patient_id",
                widget_key=f"matching_reg_toggle_{pid}_{page}",
                column_keys=_MATCHING_REGISTRY_COLS,
                weights=_MATCHING_REGISTRY_WEIGHTS,
            )
            if is_open:
                render_matching_detail_inline(by_id[pid], provider=provider)

def render_cohort_expandable_registry(
    results: list[CohortResult],
    provider: PatientDataProvider | None = None,
) -> None:
    """Single-column cohort registry with inline expand below selected patient."""
    filter_col, search_col = st.columns([1, 1.4])
    with filter_col:
        st.selectbox(
            "Verdict filter",
            ["All", "Eligible", "Inconclusive", "Ineligible"],
            key="cohort_master_filter",
            label_visibility="collapsed",
        )
    with search_col:
        st.text_input(
            "Search patients",
            key="cohort_master_search",
            placeholder="Search ID, disease, stage…",
            label_visibility="collapsed",
        )

    filtered = filter_cohort_results(
        results,
        verdict_filter=st.session_state.get("cohort_master_filter", "All"),
        search_query=st.session_state.get("cohort_master_search", ""),
    )
    st.caption(f"{len(filtered)} of {len(results)} patients shown")

    if not filtered:
        render_clinical_notice("No patients match the current filter.", "INCONCLUSIVE")
        st.session_state["cohort_selected_patient_id"] = None
        return

    page_items, page, total_pages = _registry_page_slice(filtered, "cohort_registry_page")
    expanded_id = st.session_state.get("cohort_selected_patient_id")
    visible_ids = {r.patient_id for r in page_items}
    if expanded_id and expanded_id not in visible_ids:
        expanded_id = None

    _render_registry_pagination(
        page, total_pages, len(filtered),
        prev_key="cohort_registry_prev",
        next_key="cohort_registry_next",
        page_key="cohort_registry_page",
    )

    _render_registry_header(
        ["", "Patient ID", "Age", "Gender", "Disease", "Stage", "Verdict", "Match %"],
        _COHORT_REGISTRY_WEIGHTS,
    )

    by_id = {r.patient_id: r for r in filtered}
    for r in page_items:
        fields = _cohort_row_fields(r)
        pid = r.patient_id
        is_open = st.session_state.get("cohort_selected_patient_id") == pid
        with st.container(border=True):
            _render_registry_data_row(
                fields,
                expanded_id=expanded_id,
                session_key="cohort_selected_patient_id",
                widget_key=f"cohort_reg_toggle_{pid}_{page}",
                column_keys=_COHORT_REGISTRY_COLS,
                weights=_COHORT_REGISTRY_WEIGHTS,
            )
            if is_open:
                render_cohort_detail_inline(by_id[pid], provider=provider)

def build_matching_master_table(results: list[MatchingPatientResult]) -> "Any":
    """Compact master list: Patient ID, age, and eligibility status."""
    import pandas as pd

    rows: list[dict[str, Any]] = []
    for r in results:
        verdict, _, _ = matching_registry_verdict(r.audit_report)
        p = resolve_patient_profile(r.patient_id, r.patient_profile)
        rows.append({
            "Patient ID": r.patient_id,
            "Age": p.age if p and p.age is not None else "—",
            "Status": verdict,
        })
    return pd.DataFrame(rows)

def render_matching_detail_panel(
    result: MatchingPatientResult,
    provider: PatientDataProvider | None = None,
) -> None:
    """Detail panel — demographics, XAI narrative, collapsed audit (from session cache)."""
    p = resolve_patient_profile(result.patient_id, result.patient_profile, provider)
    audit = result.audit_report
    entities, trial_reports = resolve_audit_display(audit, p, provider)
    primary = SymbolicValidator.best_trial_report(trial_reports)

    if p is None and result.patient_id != "QUICK-ENTRY":
        render_clinical_notice("Patient profile not available.", "FAIL")
        return

    if primary is not None:
        verdict = matching_verdict_label(primary)
        score = SymbolicValidator.match_score(primary)
    else:
        verdict, _, score = matching_registry_verdict(audit)

    if result.patient_id == "QUICK-ENTRY":
        with clinical_panel("Quick Entry Note"):
            head_l, head_r = st.columns([3, 1])
            with head_l:
                st.markdown("**Quick Entry (sidebar)**")
            with head_r:
                st.markdown(render_verdict_pill_html(verdict), unsafe_allow_html=True)
                st.metric("Match Score", f"{score:.0f}%")
            st.text_area("Clinical note", audit.raw_note, height=160, disabled=True)
    else:
        with clinical_panel("Patient 360"):
            head_l, head_r = st.columns([3, 1])
            with head_l:
                st.markdown(f"**`{result.patient_id}`**")
            with head_r:
                st.markdown(render_verdict_pill_html(verdict), unsafe_allow_html=True)
                st.metric("Match Score", f"{score:.0f}%")

        with clinical_panel("Demographics"):
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Age", entities.get("age") if entities.get("age") is not None else "—")
            d2.metric("Gender", (entities.get("gender") or "—").title())
            d3.metric("Primary Disease", display_registry_disease(p, entities))
            d4.metric("Stage", entities.get("stage") or "—")
            d5, d6, d7 = st.columns(3)
            d5.metric("BMI", entities.get("bmi") if entities.get("bmi") is not None else "—")
            d6.metric("ECOG", entities.get("ecog_ps") if entities.get("ecog_ps") is not None else "—")
            biomarkers = ", ".join(entities.get("biomarkers") or []) or "—"
            d7.metric("Biomarkers", biomarkers if len(biomarkers) <= 20 else biomarkers[:17] + "…")

    with clinical_panel("Clinical Decision Narrative"):
        if primary is not None:
            st.markdown(build_clinical_narrative(primary, entities))
        elif audit.xai_narrative:
            st.markdown(audit.xai_narrative)
        else:
            st.caption("No narrative available for this patient.")

    with st.expander("Full Validation Audit", expanded=False):
        render_symbolic_audit_panel(trial_reports)

def render_patient_360_panel(
    result: MatchingPatientResult,
    provider: PatientDataProvider,
) -> None:
    """Patient 360 detail — demographics, conditions, care plans + trial matching."""
    p = resolve_patient_profile(result.patient_id, result.patient_profile, provider)
    audit = result.audit_report
    verdict, verdict_cls, score = matching_registry_verdict(audit)

    if p is None:
        render_clinical_notice("Patient profile not available.", "FAIL")
        return

    with st.container(border=True):
        head_l, head_r = st.columns([3, 1])
        with head_l:
            st.markdown("##### Patient 360")
            st.markdown(f"`{result.patient_id}`")
        with head_r:
            st.markdown(render_verdict_pill_html(verdict), unsafe_allow_html=True)
            st.metric("Match Score", f"{score:.0f}%")

    tab_360, tab_match = st.tabs(["Patient 360", "Trial Matching"])

    with tab_360:
        with st.container(border=True):
            st.markdown("**Demographics** *(patients.csv)*")
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Age", p.age if p.age is not None else "—")
            d2.metric("Gender", (p.gender or "—").title())
            d3.metric("Primary Disease", p.disease or "—")
            d4.metric("Stage", p.stage or "—")
            d5, d6, d7 = st.columns(3)
            d5.metric("BMI", p.bmi if p.bmi is not None else "—")
            d6.metric("ECOG", p.ecog_ps if p.ecog_ps is not None else "—")
            biomarkers = ", ".join(p.biomarkers) if p.biomarkers else "—"
            d7.metric("Biomarkers", biomarkers if len(biomarkers) <= 24 else biomarkers[:21] + "…")

        conditions = provider.get_conditions(result.patient_id)
        with st.container(border=True):
            st.markdown(f"**Active Conditions** *(conditions.csv)* — {len(conditions)} record(s)")
            st.dataframe(
                _records_to_dataframe(conditions, {
                    "description": "Description",
                    "code": "Code",
                    "start_date": "Start",
                }),
                use_container_width=True,
                hide_index=True,
            )

        careplans = provider.get_careplans(result.patient_id)
        with st.container(border=True):
            st.markdown(f"**Care Plans** *(careplans.csv)* — {len(careplans)} active plan(s)")
            st.dataframe(
                _records_to_dataframe(careplans, {
                    "description": "Description",
                    "reason": "Reason",
                    "start_date": "Start",
                }),
                use_container_width=True,
                hide_index=True,
            )

        note = p.ehr_note or provider.get_patient_note(result.patient_id)
        if note:
            with st.container(border=True):
                st.markdown("**Clinical Note**")
                st.text_area(
                    "EHR note",
                    value=note,
                    height=140,
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"p360_note_{result.patient_id}",
                )

    with tab_match:
        render_matching_patient_detail(audit)

def render_matching_patient_detail(report: AuditReport) -> None:
    """Trial matching tabs for one cached AuditReport (no pipeline re-run)."""
    entities = report.extracted_entities
    trials = sorted(report.trial_reports, key=SymbolicValidator.match_score, reverse=True)
    if not trials:
        render_clinical_notice("No trial validation results for this patient.", "INCONCLUSIVE")
        return

    exec_summary = build_executive_summary(trials, entities)
    render_hint_text(
        f"Screened against **{len(trials)}** trial(s): "
        f"{exec_summary['eligible_count']} eligible · "
        f"{exec_summary['conditional_count']} conditional · "
        f"{exec_summary['blocked_count']} blocked"
    )

    trial_labels = [f"{t.trial_id} — {t.trial_name}" for t in trials]
    trial_by_label = dict(zip(trial_labels, trials))
    focus_key = f"matching_focus_{report.patient_id or 'anon'}"
    default_idx = 0
    if st.session_state.get(focus_key) in trial_labels:
        default_idx = trial_labels.index(st.session_state[focus_key])

    selected_label = st.selectbox(
        "Focus trial",
        trial_labels,
        index=default_idx,
        key=focus_key,
    )
    trial_report = trial_by_label[selected_label]

    tab_summary, tab_extraction, tab_analysis = st.tabs(
        ["Clinical Summary", "Neural Extraction", "Missing Data Analysis"]
    )
    with tab_summary:
        render_matching_clinical_summary(trial_report, entities)
    with tab_extraction:
        render_section("Neural Extraction Results")
        render_matching_extraction_panel(entities)
    with tab_analysis:
        render_section("Missing Data Analysis")
        render_matching_missing_data_analysis(trial_report, entities)
