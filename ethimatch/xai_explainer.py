
from __future__ import annotations

import re
from typing import Any

from symbolic_validator import RuleResult, RuleVerdict, SymbolicValidator, ValidationReport
from trial_registry import trial_protocol_relpath

ENTITY_LABELS: dict[str, str] = {
    "age": "Age",
    "gender": "Gender",
    "disease": "Primary Disease",
    "stage": "Cancer Stage",
    "biomarkers": "Biomarkers",
    "bmi": "BMI",
    "ecog_ps": "ECOG Performance Status",
    "comorbidities": "Comorbidities",
    "prior_therapies": "Prior Therapies",
}

# Clinician-friendly narrative templates keyed by rule_code
RULE_NARRATIVES: dict[str, str] = {
    "age_missing": (
        "Patient age was not found in the clinical note. "
        "Eligibility cannot be confirmed automatically — manual chart review is required."
    ),
    "age_below_min": (
        "Patient age {patient_val} is below the trial minimum of {criterion}. "
        "Enrollment would violate the protocol age requirement."
    ),
    "age_above_max": (
        "Patient age {patient_val} exceeds the trial maximum of {criterion}. "
        "Enrollment would violate the protocol age requirement."
    ),
    "age_pass": "Patient age satisfies the trial age requirement ({criterion}).",
    "gender_missing": (
        "Patient gender was not extracted from the note. "
        "Manual verification is required before enrollment."
    ),
    "gender_fail": (
        "Patient gender ({patient_val}) does not meet the trial restriction ({criterion})."
    ),
    "disease_missing": (
        "Primary disease could not be extracted. "
        "The symbolic layer cannot confirm disease eligibility."
    ),
    "disease_fail": (
        "Patient disease ({patient_val}) is not among eligible diseases: {criterion}."
    ),
    "stage_missing": (
        "Cancer stage was not found in the note. "
        "Stage eligibility requires manual confirmation."
    ),
    "stage_fail": (
        "Patient stage ({patient_val}) is not an eligible stage for this trial ({criterion})."
    ),
    "biomarker_missing": (
        "Required biomarkers were not extracted from the note. "
        "Laboratory confirmation may be needed."
    ),
    "biomarker_fail": (
        "Patient is missing required biomarkers: {criterion}. "
        "Detected biomarkers: {patient_val}."
    ),
    "ecog_missing": (
        "ECOG performance status was not extracted. "
        "This is a critical eligibility field — do not enroll without verification."
    ),
    "ecog_fail": (
        "Patient ECOG performance status ({patient_val}) exceeds the trial limit ({criterion}). "
        "Patient may be too unwell for this protocol."
    ),
    "bmi_max_missing": (
        "BMI was not found in the clinical note. "
        "Weight-based eligibility cannot be confirmed automatically."
    ),
    "bmi_max_fail": (
        "Patient BMI of {patient_val} exceeds the trial maximum of {criterion}. "
        "This patient would be excluded under current protocol criteria."
    ),
    "bmi_min_missing": "BMI missing — cannot verify minimum weight requirement.",
    "bmi_min_fail": (
        "Patient BMI of {patient_val} is below the trial minimum of {criterion}."
    ),
    "comorbidity_fail": (
        "Excluded comorbidity detected: {patient_val}. "
        "Protocol excludes: {criterion}."
    ),
    "therapy_fail": (
        "Excluded prior therapy detected: {patient_val}. "
        "Protocol excludes: {criterion}."
    ),
    "low_confidence_warning": (
        "Low-confidence extraction for {rule_name} ({patient_val}). "
        "Recommend manual verification before enrollment."
    ),
}

def _infer_rule_code(rule: RuleResult) -> str:
    if rule.rule_code:
        return rule.rule_code

    name = rule.rule_name.lower()
    if rule.verdict == RuleVerdict.INCONCLUSIVE:
        if "age" in name:
            return "age_missing"
        if "ecog" in name:
            return "ecog_missing"
        if "bmi" in name and "max" in name.lower():
            return "bmi_max_missing"
        if "biomarker" in name:
            return "biomarker_missing"
        if "stage" in name:
            return "stage_missing"
        if "disease" in name:
            return "disease_missing"
        if "gender" in name:
            return "gender_missing"
    if rule.verdict == RuleVerdict.FAIL:
        if "age" in name and "below" in rule.explanation.lower():
            return "age_below_min"
        if "age" in name:
            return "age_above_max"
        if "bmi" in name and "max" in name.lower():
            return "bmi_max_fail"
        if "bmi" in name:
            return "bmi_min_fail"
        if "ecog" in name:
            return "ecog_fail"
        if "biomarker" in name:
            return "biomarker_fail"
        if "stage" in name:
            return "stage_fail"
        if "disease" in name:
            return "disease_fail"
        if "gender" in name:
            return "gender_fail"
        if "comorbid" in name:
            return "comorbidity_fail"
        if "therap" in name:
            return "therapy_fail"
    if rule.verdict == RuleVerdict.PASS and "age" in name:
        return "age_pass"
    return "generic"

def explain_rule(rule: RuleResult) -> str:    #explains one failed/passed rule
    """Translate one symbolic rule result into clinician-friendly prose."""
    code = _infer_rule_code(rule)
    template = RULE_NARRATIVES.get(code)

    ctx = {
        "rule_name": rule.rule_name,
        "criterion": _fmt(rule.criterion),
        "patient_val": _fmt(rule.patient_val),
        "explanation": rule.explanation,
    }

    if template:
        try:
            return template.format(**ctx)
        except (KeyError, ValueError):
            pass

    return rule.explanation

def build_clinical_narrative(   # short explaination per trial 
    trial_report: ValidationReport,
    entities: dict[str, Any] | None = None,
) -> str:
    """Translate symbolic verdicts into clinician-readable prose."""
    lines: list[str] = []
    score = SymbolicValidator.match_score(trial_report)

    if not trial_report.eligible:
        fails = [r for r in trial_report.rule_results if r.verdict == RuleVerdict.FAIL]
        lines.append(
            f"**{trial_report.trial_name}** — Not recommended (Match Score: {score}%)."
        )
        lines.append("")
        lines.append("The symbolic safety layer blocked this match:")
        for rule in fails:
            lines.append(f"- **{rule.rule_name}:** {explain_rule(rule)}")
    elif trial_report.is_conditionally_eligible:
        pending = [
            r for r in trial_report.rule_results
            if r.verdict == RuleVerdict.INCONCLUSIVE
        ]
        lines.append(
            f"**{trial_report.trial_name}** — Conditionally eligible (Match Score: {score}%)."
        )
        lines.append("")
        lines.append("Manual review required:")
        for rule in pending:
            lines.append(f"- **{rule.rule_name}:** {explain_rule(rule)}")
    elif trial_report.has_warnings:
        soft = [
            r for r in trial_report.rule_results
            if r.verdict in (RuleVerdict.WARNING, RuleVerdict.INCONCLUSIVE)
        ]
        lines.append(
            f"**{trial_report.trial_name}** — Eligible with caution (Match Score: {score}%)."
        )
        lines.append("")
        for rule in soft:
            lines.append(f"- {explain_rule(rule)}")
    else:
        lines.append(
            f"**{trial_report.trial_name}** — Fully eligible (Match Score: {score}%)."
        )
        lines.append("")
        lines.append(
            f"All {trial_report.pass_count} inclusion/exclusion criteria "
            "passed deterministic validation."
        )

    if entities and entities.get("negated_fields"):
        lines.append("")
        lines.append(
            f"Negation-aware NLP removed potentially false entities: "
            f"{', '.join(entities['negated_fields'])}."
        )

    return "\n".join(lines)

def build_full_audit_narrative(   # full audit text
    raw_note: str,
    entities: dict[str, Any],
    trial_reports: list[ValidationReport],
) -> str:
    """Generate complete AuditReport text for clinicians and PDF export."""
    data_source = entities.get("data_source") if isinstance(entities, dict) else ""
    source_line = f"Data source: {data_source}" if data_source else "Data source: (unspecified)"
    sections: list[str] = [
        "ETHIMATCH CLINICAL TRIAL MATCHING — AUDIT REPORT",
        "=" * 60,
        source_line,
        "",
        "SECTION A: INPUT CLINICAL NOTE",
        "-" * 40,
        raw_note,
        "",
        "SECTION B: NEURAL EXTRACTION (BioBERT + Regex + Negation Filter)",
        "-" * 40,
    ]

    conf = entities.get("confidence_scores", {})
    for key, label in ENTITY_LABELS.items():
        val = entities.get(key)
        if val in (None, []):
            sections.append(f"  {label}: NOT EXTRACTED (requires manual review)")
        else:
            display = ", ".join(val) if isinstance(val, list) else str(val)
            score = conf.get(key)
            extra = f" [confidence: {score:.0%}]" if isinstance(score, (int, float)) else ""
            sections.append(f"  {label}: {display}{extra}")

    sections.extend(["", "SECTION C: SYMBOLIC VALIDATION & TRIAL RECOMMENDATIONS", "-" * 40])

    for report in trial_reports:
        sections.append("")
        sections.append(f"Trial: {report.trial_name} ({report.trial_id})")
        sections.append(f"Match Score: {SymbolicValidator.match_score(report)}%")
        sections.append(build_clinical_narrative(report, entities).replace("**", ""))
        sections.append("")
        sections.append("Rule-by-rule audit trace:")
        for rule in report.rule_results:
            tag = rule.verdict.value
            sections.append(f"  [{tag}] {rule.rule_name}: {explain_rule(rule)}")

    eligible = sum(1 for r in trial_reports if r.eligible and not r.is_conditionally_eligible)
    sections.extend([
        "",
        "SECTION D: SUMMARY",
        "-" * 40,
        f"Eligible for {eligible} of {len(trial_reports)} registered trial(s).",
        "This report requires clinician review before any enrollment decision.",
    ])

    return "\n".join(sections)

# Maps symbolic rule_code → JSON criterion path for clinician-facing chart tooltips
RULE_CRITERION_PATHS: dict[str, str] = {
    "age_missing": "inclusion.age_min / inclusion.age_max",
    "age_below_min": "inclusion.age_min",
    "age_above_max": "inclusion.age_max",
    "age_pass": "inclusion.age_min / inclusion.age_max",
    "gender_missing": "inclusion.gender",
    "gender_fail": "inclusion.gender",
    "disease_missing": "inclusion.diseases",
    "disease_fail": "inclusion.diseases",
    "disease_pass": "inclusion.diseases",
    "disease_unrecognised": "inclusion.diseases",
    "stage_missing": "inclusion.stages",
    "stage_fail": "inclusion.stages",
    "stage_unrecognised": "inclusion.stages",
    "biomarker_missing": "inclusion.required_biomarkers",
    "biomarker_fail": "inclusion.required_biomarkers",
    "ecog_missing": "inclusion.ecog_max",
    "ecog_fail": "inclusion.ecog_max",
    "ecog_unrecognised": "inclusion.ecog_max",
    "bmi_max_missing": "inclusion.bmi_max",
    "bmi_max_fail": "inclusion.bmi_max",
    "bmi_min_missing": "exclusion.bmi_min",
    "bmi_min_fail": "exclusion.bmi_min",
    "comorbidity_fail": "exclusion.excluded_comorbidities",
    "therapy_fail": "exclusion.excluded_prior_therapies",
    "low_confidence_warning": "extraction.confidence_scores",
}

def _rule_criterion_path(rule: RuleResult, trial_id: str) -> str:
    code = rule.rule_code or _infer_rule_code(rule)
    rel = trial_protocol_relpath(trial_id)
    path = RULE_CRITERION_PATHS.get(code, "inclusion / exclusion")
    return f"{rel} → {path}"

def _criteria_tooltip_html(
    *,
    rule_name: str,
    rule_code: str,
    trial_id: str,
    criterion_path: str,
    verdict_token: str,
    criterion: str,
    patient_value: str,
    explanation: str,
    weight: float,
) -> str:
    """Rich Plotly hover text for Weight of Advice bars."""
    verdict_labels = {
        "PASS": "PASS — Criterion satisfied",
        "FAIL": "FAIL — Blocks eligibility",
        "INCONCLUSIVE": "INCONCLUSIVE — Needs clinician review",
        "NEUTRAL": "NEUTRAL",
    }
    return (
        f"<b>{rule_name}</b><br>"
        f"<b>Verdict:</b> {verdict_labels.get(verdict_token, verdict_token)}<br>"
        f"<b>Rule ID:</b> {rule_code}<br>"
        f"<b>Trial:</b> {trial_id}<br>"
        f"<b>Protocol:</b> {criterion_path}<br>"
        f"<b>Impact:</b> {weight:+.0f}<br>"
        f"<b>Criterion:</b> {criterion}<br>"
        f"<b>Patient value:</b> {patient_value}<br>"
        f"<b>Detail:</b> {explanation}"
    )

def compute_criteria_advice_weights(     #chart data
    report: ValidationReport,
    trial: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Per-rule 'Weight of Advice' for inclusion/exclusion visualization.

    Signed magnitude reflects how strongly each criterion pushes the
    eligibility decision (PASS = supportive, FAIL = blocking, INCONCLUSIVE = uncertain).
    """
    trial_id = report.trial_id
    protocol = trial_protocol_relpath(trial_id)
    weights: list[dict[str, Any]] = []

    for rule in report.rule_results:
        code = rule.rule_code or _infer_rule_code(rule)
        criterion_path = _rule_criterion_path(rule, trial_id)
        rule_id = f"{trial_id}::{code}"

        if rule.verdict == RuleVerdict.PASS:
            magnitude = 72.0
            direction = "support"
            verdict_token = "PASS"
        elif rule.verdict == RuleVerdict.FAIL:
            magnitude = -88.0
            direction = "block"
            verdict_token = "FAIL"
        elif rule.verdict == RuleVerdict.INCONCLUSIVE:
            magnitude = -42.0
            direction = "uncertain"
            verdict_token = "INCONCLUSIVE"
        elif rule.verdict == RuleVerdict.WARNING:
            magnitude = -28.0
            direction = "caution"
            verdict_token = "INCONCLUSIVE"
        else:
            magnitude = 0.0
            direction = "neutral"
            verdict_token = "NEUTRAL"

        weights.append({
            "rule_id": rule_id,
            "rule_code": code,
            "rule_name": rule.rule_name,
            "verdict": verdict_token,
            "weight": magnitude,
            "direction": direction,
            "criterion_path": criterion_path,
            "protocol_file": protocol,
            "criterion": _fmt(rule.criterion),
            "patient_value": _fmt(rule.patient_val),
            "explanation": rule.explanation,
            "tooltip": _criteria_tooltip_html(
                rule_name=rule.rule_name,
                rule_code=code,
                trial_id=trial_id,
                criterion_path=criterion_path,
                verdict_token=verdict_token,
                criterion=_fmt(rule.criterion),
                patient_value=_fmt(rule.patient_val),
                explanation=rule.explanation,
                weight=magnitude,
            ),
        })

    weights.sort(key=lambda row: abs(row["weight"]), reverse=True)
    return weights

def compute_extraction_impact(entities: dict[str, Any]) -> list[dict[str, Any]]:   # which extracted fields drove the decision
    """SHAP-style contribution scores for neural extraction fields."""
    conf = entities.get("confidence_scores", {})
    sources = entities.get("extraction_sources", {})
    impacts: list[dict[str, Any]] = []

    for key, label in ENTITY_LABELS.items():
        val = entities.get(key)
        if val in (None, []):
            impacts.append({
                "field": key, "label": label, "value": "Missing",
                "impact": 0.0, "direction": "neutral", "source": sources.get(key),
            })
            continue

        base = float(conf.get(key, 1.0 if sources.get(key) == "regex" else 0.75))
        if key in set(entities.get("negated_fields", [])):
            base *= 0.35
            direction = "negated"
        elif sources.get(key) == "regex":
            direction = "deterministic"
        else:
            direction = "positive"

        display = ", ".join(val) if isinstance(val, list) else str(val)
        impacts.append({
            "field": key,
            "label": label,
            "value": display,
            "impact": round(base * 100, 1),
            "weight": round(base * 100, 1),
            "direction": direction,
            "source": sources.get(key),
            "verdict": "NEUTRAL" if direction == "neutral" else (
                "INCONCLUSIVE" if direction == "negated" else "PASS"
            ),
            "tooltip": (
                f"<b>{label}</b><br>"
                f"<b>Value:</b> {display}<br>"
                f"<b>Source:</b> {sources.get(key) or 'unknown'}<br>"
                f"<b>Confidence impact:</b> {round(base * 100, 1):.1f}%"
            ),
        })

    impacts.sort(key=lambda x: x["impact"], reverse=True)
    return impacts

def build_executive_summary(  #one-line summary
    trial_reports: list[ValidationReport],
    entities: dict[str, Any],
) -> dict[str, Any]:
    """High-level summary for dashboard and export."""
    eligible = [r for r in trial_reports if r.eligible and not r.is_conditionally_eligible]
    conditional = [r for r in trial_reports if r.is_conditionally_eligible]
    blocked = [r for r in trial_reports if not r.eligible]

    ranked = sorted(
        trial_reports,
        key=lambda r: SymbolicValidator.match_score(r),
        reverse=True,
    )

    conf_vals = [
        float(v) for v in entities.get("confidence_scores", {}).values()
        if isinstance(v, (int, float))
    ]
    avg_conf = round(sum(conf_vals) / len(conf_vals) * 100) if conf_vals else 0
    fields = list(ENTITY_LABELS.keys())
    found = sum(1 for k in fields if entities.get(k) not in (None, []))

    return {
        "eligible_count": len(eligible),
        "conditional_count": len(conditional),
        "blocked_count": len(blocked),
        "total_trials": len(trial_reports),
        "top_trial": ranked[0].trial_id if ranked else None,
        "top_score": SymbolicValidator.match_score(ranked[0]) if ranked else 0,
        "extraction_completeness": round(found / len(fields) * 100),
        "avg_confidence": avg_conf,
        "negation_applied": bool(entities.get("negated_fields")),
        "ranked_trials": [
            {
                "trial_id": r.trial_id,
                "trial_name": r.trial_name,
                "eligible": r.eligible,
                "score": SymbolicValidator.match_score(r),
                "verdict": _verdict_label(r),
            }
            for r in ranked
        ],
    }

def _verdict_label(report: ValidationReport) -> str:
    if not report.eligible:
        return "NOT ELIGIBLE"
    if report.is_conditionally_eligible:
        return "CONDITIONAL"
    if report.has_warnings:
        return "ELIGIBLE (WARN)"
    return "ELIGIBLE"

def _fmt(val: Any) -> str:
    if val is None:
        return "unknown"
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    return str(val)
