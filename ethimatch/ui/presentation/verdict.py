"""Verdict labels, pills, and registry scoring helpers."""
from __future__ import annotations

from config import theme_colors, theme_token
from ethimatch_pipeline import AuditReport
from symbolic_validator import SymbolicValidator, ValidationReport

from ui.presentation._utils import _esc

def matching_verdict_label(report: ValidationReport) -> str:
    """Clinician-facing verdict for Patient Matching summary."""
    if not report.eligible:
        return "Blocked"
    if report.is_conditionally_eligible:
        return "Conditional"
    return "Eligible"

def render_verdict_pill_html(verdict_label: str) -> str:
    """Return HTML for a themed verdict pill (light fill, dark label)."""
    token, css_cls = _registry_verdict_css(verdict_label)
    palette = theme_colors(token)
    return (
        f'<span class="verdict-pill {css_cls}" '
        f'style="background:{palette["background"]};color:{palette["text"]};'
        f'border:1px solid {palette["color"]};">'
        f'{_esc(verdict_label)}</span>'
    )

def _registry_verdict_css(verdict_label: str) -> tuple[str, str]:
    mapping = {
        "Eligible": ("PASS", "eligible"),
        "Inconclusive": ("INCONCLUSIVE", "conditional"),
        "Conditional": ("INCONCLUSIVE", "conditional"),
        "Ineligible": ("FAIL", "ineligible"),
        "Blocked": ("FAIL", "ineligible"),
    }
    token, css = mapping.get(verdict_label, ("NEUTRAL", "conditional"))
    return token, css

def primary_validation_report(audit: AuditReport) -> ValidationReport | None:
    return SymbolicValidator.best_trial_report(audit.trial_reports)

def _matching_verdict_sort_order(label: str) -> int:
    if label == "Eligible":
        return 0
    if label in ("Conditional", "Inconclusive"):
        return 1
    return 2

def matching_registry_verdict(audit: AuditReport) -> tuple[str, str, float]:
    """Return (label, css_class, match_score) for master registry table."""
    report = primary_validation_report(audit)
    if report is None:
        return "Blocked", "ineligible", 0.0
    score = SymbolicValidator.match_score(report)
    label = matching_verdict_label(report)
    _, css = _registry_verdict_css(label)
    return label, css, score

def cohort_verdict_label(result: CohortResult) -> tuple[str, str]:
    """Return (display label, CSS class) for a cohort screening result."""
    if result.is_eligible:
        return "Eligible", "eligible"
    if result.is_conditional:
        return "Inconclusive", "conditional"
    return "Ineligible", "ineligible"
