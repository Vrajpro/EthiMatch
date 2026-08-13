"""Plotly chart palette and layout helpers."""
from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

CHART_PALETTE: dict[str, str] = {
    "PASS": "#047857",            # emerald-700
    "FAIL": "#B91C1C",            # red-700
    "INCONCLUSIVE": "#B45309",    # amber-700
    "NEUTRAL": "#1D4ED8",         # blue-700
    "neuro_symbolic": "#047857",
    "neuro_symbolic_light": "#6EE7B7",
    "pure_neural": "#1D4ED8",
    "pure_neural_light": "#93C5FD",
    "grid": "#CBD5E1",
    "axis": "#334155",
    "text": "#0F172A",
    "text_muted": "#475569",
    "paper": "#FFFFFF",
    "plot": "rgba(0,0,0,0)",
    "border": "#94A3B8",
    "bar_border": "#000000",
}

CHART_TEXT = "#0F172A"

PLOTLY_CHART_CONFIG: dict[str, Any] = {
    "displayModeBar": False,
    "displaylogo": False,
    "responsive": True,
    "staticPlot": False,
}

def _chart_font(size: int = 13, *, bold: bool = False) -> dict[str, Any]:
    return {
        "family": "Segoe UI, Inter, Helvetica Neue, Arial, sans-serif",
        "size": size,
        "color": CHART_TEXT,
    }

def _apply_publication_layout(
    fig: go.Figure,
    *,
    title: str,
    height: int = 460,
    show_legend: bool = True,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """Light-mode layout: white/transparent chart area, dark slate text throughout."""
    axis_title_font = {"size": 14, "color": CHART_TEXT, "family": "Segoe UI, Arial, sans-serif"}
    tick_font = {"size": 12, "color": CHART_TEXT, "family": "Segoe UI, Arial, sans-serif"}

    layout_kw: dict[str, Any] = {
        "title": {
            "text": title,
            "x": 0.02,
            "xanchor": "left",
            "font": {"size": 17, "color": CHART_TEXT, "family": "Segoe UI, Arial, sans-serif"},
        },
        "font": {"size": 13, "color": CHART_TEXT, "family": "Segoe UI, Arial, sans-serif"},
        "paper_bgcolor": CHART_PALETTE["paper"],
        "plot_bgcolor": CHART_PALETTE["plot"],
        "margin": {"l": 56, "r": 28, "t": 88, "b": 56},
        "height": height,
        "hoverlabel": {
            "bgcolor": "#FFFFFF",
            "bordercolor": CHART_PALETTE["border"],
            "font": {"size": 13, "color": CHART_TEXT, "family": "Segoe UI, Arial, sans-serif"},
        },
    }
    if show_legend:
        layout_kw["legend"] = {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.01,
            "xanchor": "center",
            "x": 0.5,
            "bgcolor": "#FFFFFF",
            "bordercolor": CHART_PALETTE["border"],
            "borderwidth": 1,
            "font": {"size": 12, "color": CHART_TEXT, "family": "Segoe UI, Arial, sans-serif"},
        }
    if x_title:
        layout_kw["xaxis_title"] = {"text": x_title, "font": axis_title_font}
    if y_title:
        layout_kw["yaxis_title"] = {"text": y_title, "font": axis_title_font}
    fig.update_layout(**layout_kw)
    fig.update_xaxes(
        tickfont=tick_font,
        title_font=axis_title_font,
        linecolor=CHART_PALETTE["axis"],
        linewidth=1.5,
        gridcolor=CHART_PALETTE["grid"],
        zerolinecolor=CHART_PALETTE["axis"],
        color=CHART_TEXT,
    )
    fig.update_yaxes(
        tickfont=tick_font,
        title_font=axis_title_font,
        linecolor=CHART_PALETTE["axis"],
        linewidth=1.5,
        gridcolor=CHART_PALETTE["grid"],
        zerolinecolor=CHART_PALETTE["axis"],
        color=CHART_TEXT,
    )
    return fig

def _verdict_chart_color(verdict: str) -> str:
    return CHART_PALETTE.get(verdict.upper(), CHART_PALETTE["NEUTRAL"])

def _verdict_bar_outline(verdict: str) -> str:
    """Darker edge on bars for contrast (color-blind friendly)."""
    outlines = {
        "PASS": "#065F46",
        "FAIL": "#991B1B",
        "INCONCLUSIVE": "#92400E",
        "NEUTRAL": "#1E40AF",
    }
    return outlines.get(verdict.upper(), CHART_PALETTE["axis"])

def _criteria_legend_traces(fig: go.Figure, rows: list[dict[str, Any]]) -> None:
    """PASS / FAIL / INCONCLUSIVE swatches when those verdicts appear in data."""
    present = {str(r.get("verdict", "")).upper() for r in rows}
    legend_items = [
        ("PASS", CHART_PALETTE["PASS"], "PASS — Criterion satisfied"),
        ("FAIL", CHART_PALETTE["FAIL"], "FAIL — Blocks eligibility"),
        ("INCONCLUSIVE", CHART_PALETTE["INCONCLUSIVE"], "INCONCLUSIVE — Review required"),
    ]
    for key, color, label in legend_items:
        if key not in present:
            continue
        fig.add_trace(
            go.Bar(
                x=[None],
                y=[None],
                orientation="h",
                marker=_academic_bar_marker(color),
                name=label,
                showlegend=True,
                hoverinfo="skip",
            )
        )

def _academic_bar_marker(fill: str) -> dict[str, Any]:
    """Publication-style bars: filled color with black outline."""
    return {
        "color": fill,
        "line": {"color": CHART_PALETTE["bar_border"], "width": 1},
        "opacity": 1.0,
    }
