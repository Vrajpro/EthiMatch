"""Evaluation and XAI chart builders and Streamlit renderers."""
from __future__ import annotations

import re
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from symbolic_validator import RuleVerdict
from xai_explainer import compute_criteria_advice_weights, compute_extraction_impact

from ui.presentation.chart_style import (
    CHART_PALETTE,
    CHART_TEXT,
    PLOTLY_CHART_CONFIG,
    _academic_bar_marker,
    _apply_publication_layout,
    _chart_font,
    _criteria_legend_traces,
    _verdict_bar_outline,
    _verdict_chart_color,
)
from ui.presentation.layout import (
    render_clinical_notice,
    render_hint_text,
    render_status_metric,
    render_themed_status_banner,
)

def build_weight_of_advice_figure(
    rows: list[dict[str, Any]],
    *,
    title: str = "Weight of Advice — Inclusion / Exclusion Criteria",
    x_axis_title: str = "Advisory Impact on Eligibility (signed scale)",
    criteria_mode: bool = True,
) -> go.Figure:
    """Horizontal bar chart for per-criterion clinical advice weights."""
    if not rows:
        fig = go.Figure()
        fig.add_annotation(
            text="No criteria data available.",
            showarrow=False,
            font=_chart_font(14),
        )
        _apply_publication_layout(fig, title=title, height=280, show_legend=False)
        return fig

    labels = [r.get("rule_name") or r.get("label", "Criterion") for r in rows]
    weights = [float(r.get("weight", r.get("impact", 0))) for r in rows]
    verdicts = [str(r.get("verdict", "NEUTRAL")).upper() for r in rows]
    colors = [_verdict_chart_color(v) for v in verdicts]
    outlines = [_verdict_bar_outline(v) for v in verdicts]
    hover = [r.get("tooltip") or r.get("rule_name", "") for r in rows]

    fig = go.Figure(
        go.Bar(
            y=labels,
            x=weights,
            orientation="h",
            marker={
                "color": colors,
                "line": {"color": CHART_PALETTE["bar_border"], "width": 1},
                "opacity": 1.0,
            },
            text=[f"{w:+.0f}" for w in weights],
            textposition="outside",
            textfont={
                "family": "Segoe UI, Arial, sans-serif",
                "size": 14 if criteria_mode else 12,
                "color": CHART_TEXT,
            },
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover,
            showlegend=False,
        )
    )

    bar_height = 56 if criteria_mode else 48
    left_margin = 220 if criteria_mode else 56
    _apply_publication_layout(
        fig,
        title=title,
        height=max(360 if criteria_mode else 320, bar_height * len(rows) + 120),
        show_legend=criteria_mode,
        x_title=x_axis_title,
        y_title="Clinical Criterion",
    )
    fig.update_layout(
        margin={"l": left_margin, "r": 48, "t": 100, "b": 56},
        bargap=0.28,
    )
    fig.update_yaxes(
        categoryorder="total ascending",
        automargin=True,
        tickfont=_chart_font(15 if criteria_mode else 12, bold=criteria_mode),
        ticklabelposition="outside",
    )
    fig.update_xaxes(
        tickfont=_chart_font(12),
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor=CHART_PALETTE["axis"],
    )
    if criteria_mode:
        _criteria_legend_traces(fig, rows)
        fig.update_layout(
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5,
                "bgcolor": "rgba(255,255,255,0.98)",
                "bordercolor": CHART_PALETTE["border"],
                "borderwidth": 1.5,
                "font": _chart_font(12, bold=True),
            },
        )

    fig.update_traces(cliponaxis=False)
    return fig

def build_criteria_weight_figure(
    report: ValidationReport,
    trial: dict[str, Any] | None = None,
) -> go.Figure:
    """Patient Matching — inclusion/exclusion Weight of Advice (clinical palette)."""
    rows = compute_criteria_advice_weights(report, trial)
    trial_id = report.trial_id
    return build_weight_of_advice_figure(
        rows,
        title=f"Weight of Advice — {report.trial_name} ({trial_id})",
        x_axis_title="Advisory Impact on Eligibility (positive = supports match)",
        criteria_mode=True,
    )

def build_extraction_impact_figure(
    entities: dict[str, Any],
    *,
    title: str = "Neural Extraction Confidence Impact",
) -> go.Figure:
    """Horizontal bar chart for BioBERT / regex field confidence weights."""
    rows = compute_extraction_impact(entities)
    for row in rows:
        row.setdefault("rule_name", row.get("label"))
        row.setdefault("weight", row["impact"])
        v = str(row.get("verdict", "NEUTRAL")).upper()
        if row.get("direction") == "negated":
            row["verdict"] = "INCONCLUSIVE"
        elif v not in ("PASS", "FAIL", "INCONCLUSIVE"):
            row["verdict"] = "NEUTRAL"
    return build_weight_of_advice_figure(
        rows,
        title=title,
        x_axis_title="Extraction Confidence Impact (%)",
        criteria_mode=False,
    )

def build_evaluation_comparison_figure(
    neuro_symbolic: dict[str, float],
    pure_neural: dict[str, float],
    *,
    title: str = "Neuro-Symbolic vs Pure Neural Baseline",
) -> go.Figure:
    """Grouped 2D bar chart: Precision, Recall, False Positive Rate (academic style)."""
    metrics = [
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("False Positive Rate", "fpr"),
    ]
    categories = [m[0] for m in metrics]
    neuro_vals = [float(neuro_symbolic.get(m[1], 0)) * 100 for m in metrics]
    pure_vals = [float(pure_neural.get(m[1], 0)) * 100 for m in metrics]
    pure_fill = "#94A3B8"

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Neuro-Symbolic (BioBERT + Rules)",
            x=categories,
            y=neuro_vals,
            marker=_academic_bar_marker(CHART_PALETTE["neuro_symbolic"]),
            text=[f"{v:.1f}%" for v in neuro_vals],
            textposition="outside",
            textfont={"size": 13, "color": CHART_TEXT, "family": "Segoe UI, Arial, sans-serif"},
            hovertemplate="<b>Neuro-Symbolic</b><br>%{x}<br>%{y:.1f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Pure Neural (BioBERT + Heuristic)",
            x=categories,
            y=pure_vals,
            marker=_academic_bar_marker(pure_fill),
            text=[f"{v:.1f}%" for v in pure_vals],
            textposition="outside",
            textfont={"size": 13, "color": CHART_TEXT, "family": "Segoe UI, Arial, sans-serif"},
            hovertemplate="<b>Pure Neural</b><br>%{x}<br>%{y:.1f}%<extra></extra>",
        )
    )
    _apply_publication_layout(
        fig,
        title=title,
        height=500,
        x_title="Evaluation Metric",
        y_title="Score (%)",
    )
    fig.update_layout(barmode="group", bargap=0.2, bargroupgap=0.1)
    y_top = max(max(neuro_vals + pure_vals, default=0) * 1.3, 35)
    fig.update_yaxes(range=[0, min(110, y_top)])
    return fig

def render_benchmark_interpretation(benchmark: dict[str, Any]) -> None:
    """Plain-language explanation of evaluation metrics for clinicians/reviewers."""
    neuro = benchmark.get("neuro_symbolic") or {}
    pure = benchmark.get("pure_neural") or {}
    n = benchmark.get("n_patients", "?")
    source = str(benchmark.get("data_source", "dataset")).replace("_", " ").title()

    ns_p, ns_r, ns_fpr = neuro.get("precision", 0), neuro.get("recall", 0), neuro.get("fpr", 0)
    pn_p, pn_r, pn_fpr = pure.get("precision", 0), pure.get("recall", 0), pure.get("fpr", 0)
    ns_f1, pn_f1 = neuro.get("f1", 0), pure.get("f1", 0)

    better = "Neuro-Symbolic" if ns_f1 >= pn_f1 else "Pure Neural"
    st.markdown(
        f'<div class="clinical-notice" style="background:#F0FDF4;border-left:4px solid #047857;'
        f'color:#0F172A;padding:1rem 1.1rem;margin-bottom:1rem;">'
        f"<strong>What this chart means ({source}, n={n} patients)</strong><br><br>"
        f"<strong>Precision</strong> — When the system says a patient is eligible, how often is that correct? "
        f"Neuro-Symbolic <strong>{ns_p:.1%}</strong> vs Pure Neural <strong>{pn_p:.1%}</strong>. "
        f"Higher is safer for avoiding false trial offers.<br><br>"
        f"<strong>Recall</strong> — Of all truly eligible patients, how many did we find? "
        f"Neuro-Symbolic <strong>{ns_r:.1%}</strong> vs Pure Neural <strong>{pn_r:.1%}</strong>. "
        f"Higher means fewer missed candidates.<br><br>"
        f"<strong>False Positive Rate</strong> — How often ineligible patients are wrongly flagged. "
        f"Neuro-Symbolic <strong>{ns_fpr:.1%}</strong> vs Pure Neural <strong>{pn_fpr:.1%}</strong>. "
        f"Lower is better for clinical safety.<br><br>"
        f"<strong>F1 score</strong> balances precision and recall: "
        f"Neuro-Symbolic <strong>{ns_f1:.1%}</strong> vs Pure Neural <strong>{pn_f1:.1%}</strong>. "
        f"The <strong>{better}</strong> pipeline performs better overall on this run."
        f"</div>",
        unsafe_allow_html=True,
    )

def render_plotly_chart(
    fig: go.Figure,
    *,
    key: str | None = None,
    use_container_width: bool = True,
) -> None:
    """Streamlit wrapper for branded Plotly figures."""
    st.plotly_chart(
        fig,
        use_container_width=use_container_width,
        key=key,
        config=PLOTLY_CHART_CONFIG,
    )

def render_criteria_weight_chart(
    report: ValidationReport,
    trial: dict[str, Any] | None = None,
    *,
    chart_key: str | None = None,
) -> None:
    """Patient-facing XAI: inclusion/exclusion weight of advice."""
    fig = build_criteria_weight_figure(report, trial)
    render_plotly_chart(fig, key=chart_key)
    n_pass = sum(1 for r in report.rule_results if r.verdict == RuleVerdict.PASS)
    n_fail = sum(1 for r in report.rule_results if r.verdict == RuleVerdict.FAIL)
    n_pending = sum(
        1 for r in report.rule_results
        if r.verdict in (RuleVerdict.INCONCLUSIVE, RuleVerdict.WARNING)
    )
    st.markdown(
        f'<div style="display:flex;gap:1rem;flex-wrap:wrap;margin:.35rem 0 0;font-size:0.9rem;">'
        f'<span><span style="display:inline-block;width:12px;height:12px;background:#047857;'
        f'border-radius:2px;margin-right:6px;"></span><strong>PASS</strong> ({n_pass})</span>'
        f'<span><span style="display:inline-block;width:12px;height:12px;background:#B91C1C;'
        f'border-radius:2px;margin-right:6px;"></span><strong>FAIL</strong> ({n_fail})</span>'
        f'<span><span style="display:inline-block;width:12px;height:12px;background:#B45309;'
        f'border-radius:2px;margin-right:6px;"></span><strong>INCONCLUSIVE</strong> ({n_pending})</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    render_hint_text(
        "Hover any bar for **Rule ID**, trial protocol path (`trials/*.json`), criterion vs patient "
        "value, and clinical explanation. Bar length shows how strongly each rule pushes the decision."
    )

def render_extraction_impact_chart(
    entities: dict[str, Any],
    *,
    chart_key: str | None = None,
) -> None:
    """Neural layer confidence impact (complements symbolic criteria chart)."""
    fig = build_extraction_impact_figure(entities)
    render_plotly_chart(fig, key=chart_key)

def render_evaluation_benchmark_chart(
    benchmark: dict[str, Any],
    *,
    chart_key: str | None = None,
) -> None:
    """Publication-style grouped comparison from evaluation benchmark payload."""
    if benchmark.get("error"):
        render_clinical_notice(f"Benchmark unavailable: {benchmark['error']}", "FAIL")
        return
    neuro = benchmark.get("neuro_symbolic") or {}
    pure = benchmark.get("pure_neural") or {}
    source = str(benchmark.get("data_source", "dataset")).replace("_", " ").title()
    title = f"System Evaluation — Neuro-Symbolic vs Pure Neural ({source})"

    render_benchmark_interpretation(benchmark)

    fig_2d = build_evaluation_comparison_figure(neuro, pure, title=title)
    render_plotly_chart(fig_2d, key=f"{chart_key}_2d" if chart_key else None)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_status_metric("Neuro-Symbolic F1", f"{float(neuro.get('f1', 0)) * 100:.1f}%", "PASS")
    with c2:
        render_status_metric("Pure Neural F1", f"{float(pure.get('f1', 0)) * 100:.1f}%", "NEUTRAL")
    with c3:
        delta = float(neuro.get("f1", 0)) - float(pure.get("f1", 0))
        render_status_metric("F1 Δ (Neuro − Neural)", f"{delta * 100:+.1f}%", "PASS" if delta >= 0 else "FAIL")
    with c4:
        render_status_metric(
            "Neuro Precision",
            f"{float(neuro.get('precision', 0)) * 100:.1f}%",
            "NEUTRAL",
        )

    mcnemar = benchmark.get("mcnemar")
    if isinstance(mcnemar, dict):
        p_val = mcnemar.get("p_value_approx")
        chi2 = mcnemar.get("chi2")
        b_count = mcnemar.get("ethimatch_correct_baseline_wrong")
        c_count = mcnemar.get("ethimatch_wrong_baseline_correct")
        significant = bool(mcnemar.get("significant_at_0.05"))
        verdict_label = "Statistically significant (p < 0.05)" if significant else "Not statistically significant (p ≥ 0.05)"
        verdict_status = "PASS" if significant else "NEUTRAL"
        st.markdown(
            f"**McNemar's paired significance test (Neuro-Symbolic vs Pure Neural)** — "
            f"χ² = {chi2}, p ≈ {p_val}. "
            f"Discordant pairs: Neuro-correct & Neural-wrong = {b_count}, "
            f"Neuro-wrong & Neural-correct = {c_count}."
        )
        render_themed_status_banner(verdict_status, verdict_label)

    _render_benchmark_png_export(
        fig_2d=fig_2d,
        data_source=str(benchmark.get("data_source", "dataset")),
        chart_key=chart_key,
    )

def _render_benchmark_png_export(
    *,
    fig_2d: go.Figure,
    data_source: str,
    chart_key: str | None,
) -> None:
    """Offer PNG download + auto-save to results/figures/.

    Requires the optional ``kaleido`` engine for ``fig.to_image()``. If unavailable,
    show a friendly hint rather than failing the page.
    """
    safe_source = re.sub(r"[^A-Za-z0-9_-]+", "_", data_source).strip("_") or "dataset"
    with st.expander("Export figures (PNG)", expanded=False):
        try:
            png_2d = fig_2d.to_image(format="png", scale=2)
        except Exception as exc:
            st.caption(
                "PNG export needs the optional `kaleido` engine. "
                "Install with `pip install kaleido` and rerun. "
                f"(detail: {type(exc).__name__})"
            )
            return

        st.download_button(
            "Download 2D bars (PNG)",
            data=png_2d,
            file_name=f"ethimatch_eval_{safe_source}_2d.png",
            mime="image/png",
            key=f"{chart_key or 'eval'}_dl2d",
        )

        try:
            from config import ETHIMATCH_ROOT

            out_dir = ETHIMATCH_ROOT / "results" / "figures"
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"ethimatch_eval_{safe_source}_2d.png").write_bytes(png_2d)
            st.caption(f"Also auto-saved to `{out_dir}` for the dissertation.")
        except Exception as exc:
            st.caption(f"Could not auto-save to disk: {exc}")
