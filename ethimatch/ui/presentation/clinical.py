"""Clinical entity cards, trial panels, and matching summaries."""
from __future__ import annotations

from typing import Any

import streamlit as st

from config import theme_colors
from symbolic_validator import RuleVerdict, SymbolicValidator, ValidationReport
from trial_registry import get_trial_by_id
from xai_explainer import (
    ENTITY_LABELS,
    _infer_rule_code,
    build_clinical_narrative,
    compute_extraction_impact,
)

from ui.presentation._utils import _esc, _matching_fmt, _md_inline
from ui.presentation.charts import (
    render_criteria_weight_chart,
    render_extraction_impact_chart,
)
from ui.presentation.layout import (
    render_clinical_notice,
    render_section,
    render_themed_status_banner,
)
from ui.presentation.verdict import (
    matching_verdict_label,
    render_verdict_pill_html,
)

def _src_badge(source: str | None, negated: bool = False) -> str:
    if negated:
        return '<span class="sb sb-neg">Negated</span>'
    if source is None:
        return '<span class="sb sb-miss">Missing</span>'
    mapping = {
        "regex": ("sb-rx", "Rule"),
        "ner": ("sb-ner", "BioBERT"),
        "gold": ("sb-gold", "Gold Std"),
        "ner+regex": ("sb-both", "Hybrid"),
    }
    cls, label = mapping.get(source, ("sb-both", "Hybrid"))
    return f'<span class="sb {cls}">{label}</span>'

def _conf_bar(confidence: float, source: str | None) -> str:
    pct = int(min(confidence, 1.0) * 100)
    if source and "regex" in source and "ner" not in source:
        cls, pct = "cb-rule", 100
    elif confidence >= 0.9:
        cls = "cb-hi"
    elif confidence >= 0.7:
        cls = "cb-med"
    else:
        cls = "cb-low"
    return f'<div class="cb-bg"><div class="cb-fill {cls}" style="width:{pct}%;"></div></div>'

def render_entity_card(
    label: str,
    value: Any,
    confidence: float | None,
    source: str | None,
    negated: bool = False,
) -> None:
    if value is None or value == []:
        st.markdown(
            f'<div class="ec missing"><div class="ec-top">'
            f'<span class="ec-lbl">{_esc(label)}</span>{_src_badge(None)}</div>'
            f'<div class="ec-miss">Not extracted — requires manual review</div></div>',
            unsafe_allow_html=True,
        )
        return

    display = ", ".join(value) if isinstance(value, list) else str(value)
    conf_html = _conf_bar(confidence or 1.0, source) if confidence is not None else ""
    st.markdown(
        f'<div class="ec"><div class="ec-top">'
        f'<span class="ec-lbl">{_esc(label)}</span>{_src_badge(source, negated)}</div>'
        f'<div class="ec-val">{_esc(display)}</div>{conf_html}</div>',
        unsafe_allow_html=True,
    )

def render_extraction_impact(entities: dict[str, Any]) -> None:
    impacts = compute_extraction_impact(entities)
    max_imp = max((i["impact"] for i in impacts), default=1) or 1
    rows = []
    for item in impacts:
        width = int(item["impact"] / max_imp * 100)
        color = "var(--info)" if item["direction"] == "negated" else "var(--accent)"
        rows.append(
            f'<div class="impact-row">'
            f'<div class="impact-lbl">{_esc(item["label"])}</div>'
            f'<div class="impact-bar"><div class="impact-fill" style="width:{width}%;background:{color};"></div></div>'
            f'<div class="impact-val">{item["impact"]:.0f}</div></div>'
        )
    st.markdown("".join(rows), unsafe_allow_html=True)

def _rule_row(rule) -> str:
    mapping = {
        RuleVerdict.PASS: ("pass", "+", "PASS"),
        RuleVerdict.FAIL: ("fail", "x", "FAIL"),
        RuleVerdict.WARNING: ("warn", "!", "WARN"),
        RuleVerdict.INCONCLUSIVE: ("pending", "?", "PENDING"),
        RuleVerdict.SKIP: ("skip", "-", "SKIP"),
    }
    css, icon, tag = mapping.get(rule.verdict, ("skip", "-", "SKIP"))
    tag_token = {"pass": "PASS", "fail": "FAIL", "pending": "INCONCLUSIVE", "warn": "INCONCLUSIVE"}.get(css, "NEUTRAL")
    tp = theme_colors(tag_token)
    tag_style = f'background:{tp["background"]};color:{tp["text"]};border:1px solid {tp["color"]};'
    meta = ""
    if rule.criterion is not None or rule.patient_val is not None:
        meta = (
            f'<div class="rr-meta">Criterion: {_esc(rule.criterion)} '
            f'| Patient: {_esc(rule.patient_val)}</div>'
        )
    return (
        f'<div class="rr {css}">'
        f'<div class="rr-icon">{icon}</div>'
        f'<div style="flex:1;"><div class="rr-name">{_esc(rule.rule_name)}</div>'
        f'<div class="rr-expl">{_esc(rule.explanation)}</div>{meta}</div>'
        f'<span class="rr-tag {css}" style="{tag_style}">{tag}</span></div>'
    )

def render_trial_card(
    report: ValidationReport,
    entities: dict[str, Any] | None = None,
    expanded: bool = False,
) -> None:
    score = SymbolicValidator.match_score(report)
    if not report.eligible:
        card_cls, score_cls = "blocked", "lo"
    elif report.is_conditionally_eligible:
        card_cls, score_cls = "conditional", "med"
    else:
        card_cls, score_cls = "eligible", "hi"

    narrative_md = build_clinical_narrative(report, entities)
    narrative_html = _md_inline(narrative_md).replace("\n\n", "<br><br>").replace("\n", "<br>")

    st.markdown(
        f'<div class="trial-card {card_cls}">'
        f'<div class="trial-card-head">'
        f'<div><div class="trial-id">{_esc(report.trial_id)}</div>'
        f'<div class="trial-name">{_esc(report.trial_name)}</div></div>'
        f'<div class="score-badge {score_cls}">{score}%</div>'
        f'</div>'
        f'<div class="trial-card-body">'
        f'<div class="narrative-box">'
        f'<div class="narrative-label">Clinical Decision Narrative</div>'
        f'{narrative_html}'
        f'</div>'
        f'<div class="stat-row">'
        f'<div class="stat-cell"><div class="stat-num">{report.pass_count}</div><div class="stat-lbl">Passed</div></div>'
        f'<div class="stat-cell"><div class="stat-num">{report.fail_count}</div><div class="stat-lbl">Failed</div></div>'
        f'<div class="stat-cell"><div class="stat-num">{report.inconclusive_count}</div><div class="stat-lbl">Pending</div></div>'
        f'<div class="stat-cell"><div class="stat-num">{report.warning_count}</div><div class="stat-lbl">Warnings</div></div>'
        f'<div class="stat-cell"><div class="stat-num">{report.total_rules}</div><div class="stat-lbl">Total</div></div>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )

    with st.expander(f"Symbolic audit trace — {report.trial_id}", expanded=expanded):
        st.markdown("".join(_rule_row(r) for r in report.rule_results), unsafe_allow_html=True)

def render_matching_verdict_banner(report: ValidationReport, trial_name: str) -> None:
    """Themed verdict block (Eligible / Blocked / Conditional)."""
    verdict = matching_verdict_label(report)
    headline = f"**{verdict}** — {trial_name} (`{report.trial_id}`)"
    render_themed_status_banner(verdict, headline.replace("**", ""))

def render_matching_clinical_summary(
    report: ValidationReport,
    entities: dict[str, Any],
) -> None:
    """Compact Patient Matching summary: metrics, verdict, narrative, collapsed audit."""
    score = SymbolicValidator.match_score(report)

    score_col, _ = st.columns([1, 3])
    with score_col:
        st.metric("Match Score", f"{score}%")

    render_matching_verdict_banner(report, report.trial_name)

    st.subheader("Rule Highlights")
    passed, failed, pending = st.columns(3)
    passed.metric("Passed", report.pass_count)
    failed.metric("Failed", report.fail_count)
    pending.metric("Pending", report.inconclusive_count)

    with st.expander("Weight of Advice — Criteria Impact (chart)", expanded=True):
        trial_meta = get_trial_by_id(report.trial_id)
        render_criteria_weight_chart(
            report,
            trial_meta,
            chart_key=f"criteria_weight_{report.trial_id}",
        )

    st.subheader("Clinical Decision Narrative")
    st.markdown(build_clinical_narrative(report, entities))

    with st.expander("Full Validation Audit", expanded=False):
        st.markdown("".join(_rule_row(r) for r in report.rule_results), unsafe_allow_html=True)

def render_matching_extraction_panel(entities: dict[str, Any]) -> None:
    """Neural extraction entity grid + impact (Patient Matching tab)."""
    st.markdown('<div class="panel"><div class="entity-grid">', unsafe_allow_html=True)
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

    if entities.get("negated_fields"):
        render_clinical_notice(
            "Negation filter applied: " + ", ".join(entities["negated_fields"]),
            "INCONCLUSIVE",
        )

    with st.expander("Extraction Impact Analysis (chart)", expanded=False):
        render_extraction_impact_chart(entities, chart_key="matching_extraction_impact")
    st.markdown("</div>", unsafe_allow_html=True)

def render_matching_missing_data_analysis(
    report: ValidationReport,
    entities: dict[str, Any],
) -> None:
    """Analysis tab — fields driving inconclusive / missing-data verdicts."""
    findings = collect_missing_data_findings(report, entities)

    if report.inconclusive_count == 0 and not any(
        entities.get(k) in (None, []) for k in ENTITY_LABELS
    ):
        render_clinical_notice(
            "No missing-data inconclusive findings for this trial. "
            "All symbolic rules were resolved with complete patient data.",
            "PASS",
        )
        return

    if report.inconclusive_count > 0:
        render_clinical_notice(
            f"{report.inconclusive_count} pending rule(s) could not be confirmed because "
            "required clinical data is missing or incomplete. Review the fields below before enrollment.",
            "INCONCLUSIVE",
        )
    else:
        render_clinical_notice(
            "Some clinical fields were not extracted from the note. "
            "They may still affect eligibility if trial criteria require them.",
            "NEUTRAL",
        )

    if findings:
        import pandas as pd
        st.dataframe(
            pd.DataFrame(findings),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No specific missing-field rows to display.")

def render_symbolic_audit_panel(trial_reports: list[ValidationReport]) -> None:
    """Audit tab — primary trial rules plus optional other trials."""
    if not trial_reports:
        st.caption("No symbolic validation results.")
        return

    primary = SymbolicValidator.best_trial_report(trial_reports)
    if primary is None:
        st.caption("No symbolic validation results.")
        return

    label = matching_verdict_label(primary)
    score = SymbolicValidator.match_score(primary)
    st.markdown(
        f"<strong>Primary trial:</strong> <code>{_esc(primary.trial_id)}</code> — "
        f"{_esc(primary.trial_name)} "
        f"{render_verdict_pill_html(label)} · Match <strong>{score:.0f}%</strong> · "
        f"<strong>{primary.pass_count}</strong> pass · "
        f"<strong>{primary.fail_count}</strong> fail · "
        f"<strong>{primary.inconclusive_count}</strong> pending · "
        f"<strong>{primary.warning_count}</strong> warn",
        unsafe_allow_html=True,
    )
    st.markdown("".join(_rule_row(r) for r in primary.rule_results), unsafe_allow_html=True)

    others = [r for r in trial_reports if r.trial_id != primary.trial_id]
    if others:
        with st.expander(f"All other trials ({len(others)})", expanded=False):
            for tr in sorted(others, key=lambda r: r.trial_id):
                tr_label = matching_verdict_label(tr)
                st.markdown(
                    f"<strong>{_esc(tr.trial_id)}</strong> — {_esc(tr.trial_name)} "
                    f"{render_verdict_pill_html(tr_label)}",
                    unsafe_allow_html=True,
                )
                st.markdown("".join(_rule_row(r) for r in tr.rule_results), unsafe_allow_html=True)

def collect_missing_data_findings(
    report: ValidationReport,
    entities: dict[str, Any],
) -> list[dict[str, str]]:
    """Rows for Missing Data Analysis — inconclusive rules and absent extractions."""
    _RULE_CODE_FIELD: dict[str, str] = {
        "age_missing": "Age",
        "gender_missing": "Gender",
        "disease_missing": "Primary Disease",
        "stage_missing": "Cancer Stage",
        "biomarker_missing": "Biomarkers",
        "ecog_missing": "ECOG Performance Status",
        "bmi_max_missing": "BMI",
        "bmi_min_missing": "BMI",
    }

    findings: list[dict[str, str]] = []
    seen_fields: set[str] = set()

    for rule in report.rule_results:
        if rule.verdict != RuleVerdict.INCONCLUSIVE:
            continue
        code = _infer_rule_code(rule)
        field = _RULE_CODE_FIELD.get(code, rule.rule_name)
        seen_fields.add(field.lower())
        findings.append({
            "Clinical field": field,
            "Rule": rule.rule_name,
            "Status": "Pending (Inconclusive)",
            "Detail": rule.explanation,
            "Extracted value": _matching_fmt(rule.patient_val),
            "Trial criterion": _matching_fmt(rule.criterion),
        })

    for key, label in ENTITY_LABELS.items():
        val = entities.get(key)
        if val not in (None, []):
            continue
        if label.lower() in seen_fields:
            continue
        if report.inconclusive_count == 0:
            continue
        findings.append({
            "Clinical field": label,
            "Rule": "—",
            "Status": "Not extracted",
            "Detail": "Field absent from neural extraction output",
            "Extracted value": "Missing",
            "Trial criterion": "—",
        })

    return findings
