"""Page chrome, panels, and shared layout primitives."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import streamlit as st

from config import theme_colors, theme_token

from ui.presentation.chart_style import CHART_PALETTE
from ui.presentation._utils import _esc, _md_inline

def inject_theme() -> None:
    """Inject light-mode clinical CSS (Streamlit theme locked via .streamlit/config.toml)."""
    from ui.theme import get_theme_css
    st.markdown(get_theme_css(), unsafe_allow_html=True)

def render_sidebar_brand() -> None:
    st.markdown(
        '<div class="brand-block">'
        '<div class="brand-mark">'
        '<div class="brand-icon">EM</div>'
        '<div><div class="brand-name">EthiMatch</div>'
        '<div class="brand-tag">Clinical Trial Intelligence</div></div>'
        '</div></div>'
        '<div class="nav-section">Navigation</div>',
        unsafe_allow_html=True,
    )

def render_page_header(
    eyebrow: str,
    title: str,
    description: str,
    chips: list[tuple[str, bool]] | None = None,
) -> None:
    chip_html = ""
    if chips:
        chip_html = '<div class="page-header-right">'
        for label, live in chips:
            cls = "status-chip live" if live else "status-chip"
            chip_html += f'<span class="{cls}">{_esc(label)}</span>'
        chip_html += "</div>"

    desc_html = (
        f'<p class="page-desc">{_esc(description)}</p>' if description.strip() else ""
    )
    st.markdown(
        f'<div class="page-header">'
        f'<div class="page-header-left">'
        f'<div class="page-eyebrow">{_esc(eyebrow)}</div>'
        f'<h1 class="page-title">{_esc(title)}</h1>'
        f'{desc_html}'
        f'</div>{chip_html}</div>',
        unsafe_allow_html=True,
    )

def render_pipeline_stepper(active: int = 0) -> None:
    steps = [
        ("01", "EHR Input", "Clinical note ingestion"),
        ("02", "Neural Extract", "BioBERT + negation"),
        ("03", "Symbolic Validate", "Deterministic rules"),
        ("04", "XAI Report", "Clinical narrative"),
    ]
    parts = ['<div class="pipeline-wrap"><div class="pipeline">']
    for i, (num, label, _) in enumerate(steps):
        cls = "done" if i < active else ("active" if i == active else "")
        line = '<div class="ps-line"></div>' if i < len(steps) - 1 else ""
        parts.append(
            f'<div class="ps {cls}"><div class="ps-dot">{num}</div>'
            f'<div class="ps-lbl">{label}</div>{line}</div>'
        )
    parts.append("</div></div>")
    st.markdown("".join(parts), unsafe_allow_html=True)

def render_kpi_row(summary: dict[str, Any]) -> None:
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_status_metric("Eligible Trials", str(summary["eligible_count"]), "PASS")
    with c2:
        render_status_metric("Conditional", str(summary["conditional_count"]), "INCONCLUSIVE")
    with c3:
        render_status_metric("Safety Blocked", str(summary["blocked_count"]), "FAIL")
    with c4:
        render_status_metric("Extraction", f'{summary["extraction_completeness"]}%', "NEUTRAL")
    with c5:
        render_status_metric("Top Match Score", f'{summary["top_score"]}%', "NEUTRAL")

def render_section(title: str) -> None:
    st.markdown(
        f'<div class="sec clinical-sec">{_esc(title)}<span class="sec-line"></span></div>',
        unsafe_allow_html=True,
    )

@contextmanager
def clinical_panel(title: str | None = None) -> Iterator[None]:
    """Bordered clinical content block with optional section title."""
    with st.container(border=True):
        if title:
            st.markdown(f"**{title}**")
        yield

def render_clinical_notice(message: str, token: str = "NEUTRAL") -> None:
    """Themed notice — dark text on soft semantic background (light mode)."""
    palette = theme_colors(token)
    st.markdown(
        f'<div class="clinical-notice" '
        f'style="background:{palette["background"]};color:{palette["text"]};'
        f'border:1px solid {CHART_PALETTE["border"]};border-left:4px solid {palette["color"]};">'
        f'{_md_inline(message)}</div>',
        unsafe_allow_html=True,
    )

def render_hint_text(message: str) -> None:
    """Muted helper text — supports ``**bold**`` markers."""
    st.markdown(
        f'<p class="clinical-hint">{_md_inline(message)}</p>',
        unsafe_allow_html=True,
    )

def render_status_metric(label: str, value: str, token: str = "NEUTRAL") -> None:
    """KPI tile with colored header and dark value text."""
    palette = theme_colors(token)
    st.markdown(
        f'<div class="clinical-metric">'
        f'<div class="clinical-metric-head" style="background:{palette["background"]};'
        f'color:{palette["text"]};">{_esc(label)}</div>'
        f'<div class="clinical-metric-value">{_esc(value)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

def render_panel_start(title: str, subtitle: str = "") -> None:
    sub = f'<div class="panel-sub">{_esc(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f'<div class="panel"><div class="panel-header">'
        f'<div><div class="panel-title">{_esc(title)}</div>{sub}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

def render_panel_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)

def render_architecture_flow() -> None:
    steps = [
        ("1", "EHR Ingestion", "Unstructured clinical notes"),
        ("2", "Neural Extraction", "BioBERT NER + negation filter"),
        ("3", "Symbolic Validation", "Deterministic eligibility rules"),
        ("4", "Explainability", "Impact scores + rule traces"),
        ("5", "Clinician Review", "Human-in-the-loop decision"),
    ]
    parts = ['<div class="arch-flow">']
    for i, (num, title, desc) in enumerate(steps):
        if i > 0:
            parts.append('<div class="arch-arrow">&#8594;</div>')
        parts.append(
            f'<div class="arch-step"><div class="arch-step-num">{num}</div>'
            f'<div class="arch-step-title">{_esc(title)}</div>'
            f'<div class="arch-step-desc">{_esc(desc)}</div></div>'
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)

def render_themed_status_banner(verdict_label: str, message: str) -> None:
    """Accessible status banner mapped from a clinician verdict label."""
    render_clinical_notice(message, theme_token(verdict_label))

def render_feature_grid() -> None:
    features = [
        ("Neuro-Symbolic Engine", "BioBERT extracts entities; symbolic rules enforce safety with zero false-positive tolerance on exclusions."),
        ("Dual-Layer XAI", "Neural impact scores plus deterministic rule traces translated into clinical narratives."),
        ("Negation Awareness", "Detects negated clinical statements to prevent dangerous mis-extractions."),
        ("Cohort Discovery", "Screen patient registries against trial criteria with full audit trails per record."),
    ]
    cards = "".join(
        f'<div class="feature-card"><h4>{_esc(t)}</h4><p>{_esc(d)}</p></div>'
        for t, d in features
    )
    st.markdown(f'<div class="feature-grid">{cards}</div>', unsafe_allow_html=True)

def render_footer() -> None:
    st.markdown(
        '<div class="app-footer">'
        '<span>EthiMatch v1.0 &middot; Neuro-Symbolic Clinical Trial Matching &middot; Module 7005SCN</span>'
        '<span>Research prototype &mdash; local CSV data only, not for clinical use</span>'
        '</div>',
        unsafe_allow_html=True,
    )
