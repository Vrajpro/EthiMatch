"""Patient matching batch summary widgets."""
from __future__ import annotations

import streamlit as st

from config import theme_colors

from ui.presentation.chart_style import CHART_PALETTE
from ui.presentation._utils import _esc
from ui.presentation.layout import render_status_metric

def render_matching_batch_summary(
    *,
    total: int,
    filter_label: str,
    path_counts: dict[str, int],
) -> None:
    """Post-batch summary: filter applied and extraction-path breakdown."""
    palette = theme_colors("PASS")
    st.markdown(
        f'<div class="clinical-notice" '
        f'style="background:{palette["background"]};color:{palette["text"]};'
        f'border:1px solid {CHART_PALETTE["border"]};border-left:4px solid {palette["color"]};'
        f'margin-bottom:.75rem;">'
        f'<strong>Batch screening complete</strong> — '
        f'{_esc(filter_label)}'
        f'</div>',
        unsafe_allow_html=True,
    )
    stats = [
        ("Patients screened", total, "PASS"),
        ("Silver cache", path_counts.get("silver", 0), "NEUTRAL"),
        ("Early exit (CSV)", path_counts.get("early_exit", 0), "NEUTRAL"),
        ("BioBERT runs", path_counts.get("neural", 0), "INCONCLUSIVE"),
    ]
    cols = st.columns(len(stats))
    for col, (label, value, token) in zip(cols, stats):
        with col:
            render_status_metric(label, str(value), token)
