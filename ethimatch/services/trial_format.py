"""HTML formatters for trial registry rows."""

from __future__ import annotations

import html
from typing import Any

def _esc(text: Any) -> str:
    return html.escape(str(text) if text is not None else "")

def format_trial_exclusions_html(excl: dict) -> str:
    excluded_comorb = excl.get("excluded_comorbidities") or []
    excluded_rx = excl.get("excluded_prior_therapies") or []
    lines: list[str] = ['<div class="trial-excl-title">Exclusions</div>']
    if excluded_comorb:
        lines.append(
            '<div class="trial-excl-line">'
            f'<span class="trial-excl-key">Comorbidities</span>'
            f'<span class="trial-excl-val">{_esc(", ".join(excluded_comorb))}</span>'
            "</div>"
        )
    if excluded_rx:
        lines.append(
            '<div class="trial-excl-line">'
            f'<span class="trial-excl-key">Prior therapies</span>'
            f'<span class="trial-excl-val">{_esc(", ".join(excluded_rx))}</span>'
            "</div>"
        )
    if not excluded_comorb and not excluded_rx:
        lines.append('<div class="trial-excl-line trial-excl-none">None specified</div>')
    return "".join(lines)

def format_trial_age_html(inclusion: dict[str, Any]) -> str:
    age_min = inclusion.get("age_min")
    age_max = inclusion.get("age_max")
    if age_min is not None and age_max is not None:
        return f"Ages {age_min}–{age_max}"
    if age_min is not None:
        return f"Ages &ge; {age_min}"
    if age_max is not None:
        return f"Ages &le; {age_max}"
    return "Any age"

def format_trial_inclusion_html(inclusion: dict[str, Any]) -> str:
    summary_parts = [format_trial_age_html(inclusion)]
    diseases = inclusion.get("diseases") or []
    summary_parts.append(_esc(", ".join(diseases) if diseases else "Any disease"))
    stages = inclusion.get("stages") or []
    if stages:
        summary_parts.append(_esc(f"Stages {', '.join(stages)}"))
    ecog_max = inclusion.get("ecog_max")
    if ecog_max is not None:
        summary_parts.append(f"ECOG &le; {ecog_max}")
    return " · ".join(summary_parts)
