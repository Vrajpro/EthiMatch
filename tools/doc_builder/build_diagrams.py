"""Generates all diagrams used in EthiMatch_Design_Document.docx.

Each function saves a high-resolution PNG into design_doc_assets/.
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from matplotlib.lines import Line2D

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS = PROJECT_ROOT / "docs" / "figures"
ASSETS.mkdir(parents=True, exist_ok=True)

NAVY = "#0B2447"
TEAL = "#19A7CE"
GOLD = "#F0A04B"
GREEN = "#3A7D44"
RED = "#C53030"
GREY = "#4A5568"
LIGHT_GREY = "#F5F7FA"
LAVENDER = "#A084DC"
WHITE = "#FFFFFF"
BLUE_SOFT = "#E3F2FD"
GREEN_SOFT = "#E8F5E9"
ORANGE_SOFT = "#FFF3E0"
PURPLE_SOFT = "#F3E5F5"


def _save(fig, name: str) -> Path:
    path = ASSETS / name
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    print(f"  saved {path.name}")
    return path


def _bbox(ax, xy, w, h, text, *, fill=BLUE_SOFT, edge=NAVY, text_color=NAVY, fontsize=10, fontweight="bold"):
    box = FancyBboxPatch(
        xy, w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.6, edgecolor=edge, facecolor=fill,
    )
    ax.add_patch(box)
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text,
            ha="center", va="center", fontsize=fontsize,
            color=text_color, fontweight=fontweight, wrap=True)


def _arrow(ax, p0, p1, *, color=NAVY, lw=1.6, style="->"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style,
                                 mutation_scale=14, color=color, linewidth=lw))


def diagram_architecture():
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6.5)
    ax.axis("off")
    ax.text(5.5, 6.15, "EthiMatch 5-Stage Neuro-Symbolic Pipeline",
            ha="center", fontsize=15, fontweight="bold", color=NAVY)
    ax.text(5.5, 5.78, "Each stage has a single responsibility and a typed output contract.",
            ha="center", fontsize=10, color=GREY, style="italic")

    stages = [
        ("STAGE 1", "Silver Cache\nLookup",         BLUE_SOFT,   NAVY),
        ("STAGE 2", "Structured\nEarly-Exit",        ORANGE_SOFT, GOLD),
        ("STAGE 3", "Neural NER\n(BioBERT)",         GREEN_SOFT,  GREEN),
        ("STAGE 4", "Symbolic\nRule Engine",         PURPLE_SOFT, LAVENDER),
        ("STAGE 5", "XAI\nExplanation",              "#FDECEC",   RED),
    ]
    x_start = 0.4
    w = 1.95
    h = 1.7
    y = 2.6
    centers = []
    for i, (label, text, fill, edge) in enumerate(stages):
        x = x_start + i * (w + 0.15)
        _bbox(ax, (x, y), w, h, text, fill=fill, edge=edge, fontsize=11)
        ax.text(x + w / 2, y + h + 0.18, label,
                ha="center", fontsize=9, fontweight="bold", color=edge)
        centers.append((x + w / 2, y + h / 2))
        if i + 1 < len(stages):
            _arrow(ax, (x + w + 0.005, y + h / 2), (x + w + 0.12, y + h / 2),
                   color=NAVY, lw=2.2)

    _bbox(ax, (0.4, 0.55), 10.2, 1.2, "", fill=LIGHT_GREY, edge=GREY, fontsize=9)
    ax.text(5.5, 1.42, "Output: AuditReport",
            ha="center", fontsize=11, fontweight="bold", color=NAVY)
    ax.text(5.5, 1.05, "Entities  +  Validation Reports  +  Rule outcomes  +  Clinical narrative  +  PDF/JSON export",
            ha="center", fontsize=9.5, color=GREY)
    ax.text(5.5, 0.7, "Verdicts: ELIGIBLE  /  INELIGIBLE  /  INCONCLUSIVE",
            ha="center", fontsize=9.5, color=NAVY, fontweight="bold")

    for cx, _ in centers:
        ax.add_patch(FancyArrowPatch((cx, 2.55), (cx, 1.78),
                                     arrowstyle="->", mutation_scale=10,
                                     color=GREY, linewidth=0.9, linestyle=":"))
    return _save(fig, "01_architecture.png")


def diagram_dataflow():
    """Left-to-right data flow. No overlapping marks; every box has a clear path."""
    fig, ax = plt.subplots(figsize=(11.4, 7.0))
    ax.set_xlim(0, 11.4)
    ax.set_ylim(0, 7.0)
    ax.axis("off")
    ax.text(5.7, 6.65, "Data Flow Diagram", ha="center",
            fontsize=15, fontweight="bold", color=NAVY)
    ax.text(5.7, 6.32, "Where each piece of information comes from and where it goes.",
            ha="center", fontsize=10, color=GREY, style="italic")

    ax.text(0.45, 5.95, "Inputs", fontsize=10, fontweight="bold", color=TEAL)
    ax.text(3.35, 5.95, "Providers", fontsize=10, fontweight="bold", color=GREEN)
    ax.text(6.25, 5.95, "Core pipeline", fontsize=10, fontweight="bold", color=NAVY)
    ax.text(9.25, 5.95, "Output", fontsize=10, fontweight="bold", color=RED)

    # Inputs
    _bbox(ax, (0.35, 4.55), 2.35, 0.90, "Synthea CSVs\n(data/synthea/)", fill=BLUE_SOFT, edge=TEAL, fontsize=10)
    _bbox(ax, (0.35, 3.35), 2.35, 0.90, "MIMIC-IV Demo\n(data/mimic/)", fill=BLUE_SOFT, edge=TEAL, fontsize=10)
    _bbox(ax, (0.35, 2.15), 2.35, 0.90, "Trial protocols\n(trials/*.json)", fill=BLUE_SOFT, edge=TEAL, fontsize=10)

    # Provider
    _bbox(ax, (3.20, 3.15), 2.40, 1.50, "Data loader\nSyntheaDual /\nMIMICDual provider",
          fill=GREEN_SOFT, edge=GREEN, fontsize=10)

    # Core
    _bbox(ax, (6.15, 4.70), 2.40, 0.90, "Silver cache\n(data/silver/*.json)",
          fill=ORANGE_SOFT, edge=GOLD, fontsize=10)
    _bbox(ax, (6.15, 3.40), 2.40, 0.90, "Neural extractor",
          fill=GREEN_SOFT, edge=GREEN, fontsize=10)
    _bbox(ax, (6.15, 2.10), 2.40, 0.90, "Symbolic validator",
          fill=PURPLE_SOFT, edge=LAVENDER, fontsize=10)
    _bbox(ax, (6.15, 0.55), 2.40, 0.90, "XAI explainer",
          fill=LIGHT_GREY, edge=NAVY, fontsize=10)

    # Output
    _bbox(ax, (9.15, 2.70), 1.90, 1.70, "Audit report\n(UI / PDF)",
          fill="#FDECEC", edge=RED, fontsize=11)

    # Inputs -> loader
    _arrow(ax, (2.70, 5.00), (3.20, 4.30), lw=1.6)
    _arrow(ax, (2.70, 3.80), (3.20, 3.90), lw=1.6)
    _arrow(ax, (2.70, 2.60), (3.20, 3.40), lw=1.6)

    # Loader -> core
    _arrow(ax, (5.60, 4.20), (6.15, 5.00), lw=1.6)
    _arrow(ax, (5.60, 3.90), (6.15, 3.85), lw=1.6)
    _arrow(ax, (5.60, 3.50), (6.15, 2.55), lw=1.6)

    # Cache <-> extractor (one vertical link in the gap — not on the box edge)
    _arrow(ax, (7.35, 4.70), (7.35, 4.30), style="<->", color=GOLD, lw=1.8)

    # Validator -> XAI -> audit
    _arrow(ax, (7.35, 2.10), (7.35, 1.45), lw=1.6)
    _arrow(ax, (8.55, 3.85), (9.15, 3.85), lw=1.6)
    _arrow(ax, (8.55, 2.55), (9.15, 3.40), lw=1.6)
    _arrow(ax, (8.55, 1.00), (9.15, 2.90), lw=1.6)

    return _save(fig, "02_dataflow.png")


def diagram_use_case():
    """UML use-case diagram: grouped by actor, no crossing lines, text inside ovals."""
    fig, ax = plt.subplots(figsize=(11.5, 12.4))
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 12.4)
    ax.axis("off")

    ax.text(5.75, 12.05, "Use Case Diagram",
            ha="center", fontsize=15, fontweight="bold", color=NAVY)
    ax.text(5.75, 11.72, "Actors and the system functions they trigger.",
            ha="center", fontsize=10, color=GREY, style="italic")

    def stick(x, y, label):
        ax.add_patch(plt.Circle((x, y), 0.22, fill=False, edgecolor=NAVY, linewidth=1.6))
        ax.plot([x, x], [y - 0.22, y - 0.70], color=NAVY, linewidth=1.6)
        ax.plot([x - 0.30, x + 0.30], [y - 0.40, y - 0.40], color=NAVY, linewidth=1.6)
        ax.plot([x, x - 0.26], [y - 0.70, y - 1.02], color=NAVY, linewidth=1.6)
        ax.plot([x, x + 0.26], [y - 0.70, y - 1.02], color=NAVY, linewidth=1.6)
        ax.text(x, y - 1.32, label, ha="center", va="top",
                fontsize=8.8, color=NAVY, fontweight="bold", linespacing=1.15)
        return (x + 0.30, y - 0.40)

    def oval(cx, cy, text):
        w, h = 4.55, 0.72
        ax.add_patch(plt.matplotlib.patches.Ellipse(
            (cx, cy), w, h, facecolor=BLUE_SOFT, edgecolor=NAVY, linewidth=1.3,
        ))
        ax.text(cx, cy, text, ha="center", va="center",
                fontsize=9.2, color=NAVY, fontweight="bold")
        return (cx - w / 2, cy)

    def assoc(p0, p1):
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                color=NAVY, linewidth=1.15, alpha=0.8, zorder=0)

    ax.add_patch(Rectangle((3.30, 0.18), 7.90, 11.20,
                           fill=False, edgecolor=NAVY, linewidth=1.6))
    ax.text(7.25, 11.08, "EthiMatch System",
            ha="center", fontsize=12, fontweight="bold", color=NAVY)

    oval_x = 7.25

    groups = [
        ("Clinical matching", 1.35, 8.75, "Oncologist /\nResearch coordinator", [
            (10.35, "Quick note matching"),
            (9.55, "Screen patient cohort"),
            (8.75, "Search trial eligibility"),
            (7.95, "View XAI audit report"),
            (7.15, "Export audit PDF"),
        ]),
        ("System operations", 1.35, 5.30, "Hospital IT\nadministrator", [
            (6.10, "Configure data source"),
            (5.30, "Materialize silver cache"),
            (4.50, "Edit trial protocols"),
            (3.70, "Inspect cache status"),
        ]),
        ("Evaluation", 1.35, 1.85, "Researcher /\nDissertation evaluator", [
            (2.65, "Run comparative benchmark"),
            (1.85, "View McNemar's test"),
            (1.05, "Export figures (PNG)"),
        ]),
    ]

    headers = [10.70, 6.45, 3.00]
    for header_y, (header, ax_x, ax_y, actor, cases) in zip(headers, groups):
        ax.text(oval_x, header_y, header, ha="center",
                fontsize=9, color=GREY, style="italic")
        pts = [oval(oval_x, y, t) for y, t in cases]
        hand = stick(ax_x, ax_y, actor)
        for p in pts:
            assoc(hand, p)

    return _save(fig, "03_use_case.png")


def diagram_flowchart():
    fig, ax = plt.subplots(figsize=(9.6, 9.6))
    ax.set_xlim(0, 9.6)
    ax.set_ylim(0, 9.6)
    ax.axis("off")
    ax.text(4.80, 9.25, "System Flow Chart (Patient Matching)",
            ha="center", fontsize=15, fontweight="bold", color=NAVY)

    def oval(xy, w, h, text, fill=BLUE_SOFT, edge=NAVY):
        ell = plt.matplotlib.patches.Ellipse(xy, w, h, facecolor=fill,
                                             edgecolor=edge, linewidth=1.5)
        ax.add_patch(ell)
        ax.text(xy[0], xy[1], text, ha="center", va="center",
                fontsize=9.5, color=NAVY, fontweight="bold")

    def rect(xy, w, h, text, fill=BLUE_SOFT, edge=NAVY):
        _bbox(ax, (xy[0] - w/2, xy[1] - h/2), w, h, text, fill=fill, edge=edge, fontsize=9.5)

    def diamond(xy, w, h, text, fill=ORANGE_SOFT, edge=GOLD):
        cx, cy = xy
        pts = [(cx, cy + h/2), (cx + w/2, cy), (cx, cy - h/2), (cx - w/2, cy)]
        poly = plt.matplotlib.patches.Polygon(pts, closed=True,
                                              facecolor=fill, edgecolor=edge, linewidth=1.5)
        ax.add_patch(poly)
        ax.text(cx, cy, text, ha="center", va="center", fontsize=9, color=NAVY, fontweight="bold")

    cx = 4.80
    oval((cx, 8.65), 2.4, 0.5, "START")
    rect((cx, 7.85), 4.4, 0.55, "Load patient profile (provider.get_patient)")
    rect((cx, 7.05), 4.4, 0.55, "Synthesise EHR note (data_loader)")
    diamond((cx, 6.05), 2.3, 0.90, "Silver cache\nhit?")

    # Side branches sit clear of the diamond tips (tips at 4.80 ± 1.25 = 3.55 / 6.05)
    rect((1.45, 6.05), 2.35, 0.60, "Use cached\nentities", fill=BLUE_SOFT, edge=TEAL)
    rect((8.15, 6.05), 2.50, 0.60, "Structured early-\nexit possible?", fill=ORANGE_SOFT, edge=GOLD)
    rect((8.15, 5.10), 2.50, 0.55, "Run BioBERT NER\n(neural_extractor)", fill=GREEN_SOFT, edge=GREEN)
    rect((8.15, 4.30), 2.50, 0.55, "Save to silver\ncache (hashed)", fill=ORANGE_SOFT, edge=GOLD)

    rect((cx, 3.40), 5.2, 0.60, "Symbolic Validator: 10 rules x N trials", fill=PURPLE_SOFT, edge=LAVENDER)
    diamond((cx, 2.40), 2.6, 0.95, "Verdict?")
    rect((1.20, 1.35), 2.2, 0.55, "ELIGIBLE", fill=GREEN_SOFT, edge=GREEN)
    rect((cx, 1.35), 2.2, 0.55, "INCONCLUSIVE", fill=ORANGE_SOFT, edge=GOLD)
    rect((8.40, 1.35), 2.2, 0.55, "INELIGIBLE", fill="#FDECEC", edge=RED)
    rect((cx, 0.50), 5.6, 0.55, "Build AuditReport + XAI narrative", fill=LIGHT_GREY, edge=NAVY)

    _arrow(ax, (cx, 8.40), (cx, 8.13))
    _arrow(ax, (cx, 7.57), (cx, 7.33))
    _arrow(ax, (cx, 6.77), (cx, 6.53))

    # yes / no in the gaps, not on the diamond
    _arrow(ax, (3.65, 6.05), (2.63, 6.05))
    ax.text(3.05, 6.38, "yes", fontsize=9, color=GREEN, fontweight="bold",
            ha="center", va="bottom",
            bbox=dict(facecolor="white", edgecolor="none", pad=0.8))
    _arrow(ax, (5.95, 6.05), (6.90, 6.05))
    ax.text(6.72, 6.38, "no", fontsize=9, color=RED, fontweight="bold",
            ha="center", va="bottom",
            bbox=dict(facecolor="white", edgecolor="none", pad=0.8))

    _arrow(ax, (8.15, 5.75), (8.15, 5.38))
    _arrow(ax, (8.15, 4.82), (8.15, 4.58))
    _arrow(ax, (8.15, 4.02), (6.20, 3.70))
    _arrow(ax, (1.45, 5.75), (3.20, 3.70))
    _arrow(ax, (cx, 3.10), (cx, 2.88))
    _arrow(ax, (3.50, 2.40), (2.30, 1.63))
    _arrow(ax, (cx, 1.92), (cx, 1.63))
    _arrow(ax, (6.10, 2.40), (7.30, 1.63))
    _arrow(ax, (2.30, 1.07), (3.80, 0.78))
    _arrow(ax, (cx, 1.07), (cx, 0.78))
    _arrow(ax, (7.30, 1.07), (5.80, 0.78))
    return _save(fig, "04_flowchart.png")


def diagram_components():
    """Layered component diagram: readable names, no spaghetti arrows."""
    fig, ax = plt.subplots(figsize=(11.6, 8.4))
    ax.set_xlim(0, 11.6)
    ax.set_ylim(0, 8.4)
    ax.axis("off")

    ax.text(5.8, 8.10, "Module Dependency / Component Diagram",
            ha="center", fontsize=15, fontweight="bold", color=NAVY)
    ax.text(5.8, 7.75, "Arrows mean imports / depends on. Layers run top to bottom.",
            ha="center", fontsize=10, color=GREY, style="italic")

    def node(x, y, w, h, text, fill, edge, fs=9.5):
        _bbox(ax, (x, y), w, h, text, fill=fill, edge=edge, fontsize=fs)
        return (x + w / 2, y + h / 2, x, y, w, h)

    def down(a, b):
        # a, b are (cx, cy, x, y, w, h)
        _arrow(ax, (a[0], a[3]), (b[0], b[3] + b[5]), lw=1.5)

    def right(a, b):
        _arrow(ax, (a[2] + a[4], a[1]), (b[2], b[1]), lw=1.5)

    # Layer labels
    ax.text(0.25, 6.95, "UI", fontsize=9, fontweight="bold", color=TEAL, rotation=90, va="center")
    ax.text(0.25, 5.05, "Orchestration", fontsize=8.5, fontweight="bold", color=GREEN, rotation=90, va="center")
    ax.text(0.25, 3.15, "Core pipeline", fontsize=8.5, fontweight="bold", color=LAVENDER, rotation=90, va="center")
    ax.text(0.25, 1.20, "Data / config", fontsize=8.5, fontweight="bold", color=NAVY, rotation=90, va="center")

    # --- UI ---
    y_ui, h, w = 6.45, 0.90, 2.55
    app = node(1.15, y_ui, w, h, "app.py", BLUE_SOFT, TEAL)
    pages = node(4.50, y_ui, w, h, "ui / pages.py", BLUE_SOFT, TEAL)
    comps = node(7.85, y_ui, w, h, "ui / components.py", BLUE_SOFT, TEAL)
    right(app, pages)
    right(pages, comps)

    # --- Orchestration ---
    y_or = 4.60
    pipe = node(2.40, y_or, 3.10, h, "ethimatch pipeline", GREEN_SOFT, GREEN, fs=10)
    evl = node(6.20, y_or, 3.10, h, "evaluation", "#FDECEC", RED, fs=10)
    down(pages, pipe)
    down(pages, evl)

    # --- Core ---
    y_core = 2.70
    cw = 2.35
    neural = node(0.85, y_core, cw, h, "neural\nextractor", GREEN_SOFT, GREEN)
    symb = node(3.35, y_core, cw, h, "symbolic\nvalidator", PURPLE_SOFT, LAVENDER)
    xai = node(5.85, y_core, cw, h, "XAI\nexplainer", ORANGE_SOFT, GOLD)
    cache = node(8.35, y_core, cw, h, "silver\ncache", ORANGE_SOFT, GOLD)
    down(pipe, neural)
    down(pipe, symb)
    down(pipe, xai)
    down(pipe, cache)

    # --- Foundation ---
    y_f = 0.75
    loader = node(0.85, y_f, cw, h, "data\nloader", BLUE_SOFT, NAVY)
    trials = node(3.35, y_f, cw, h, "trial\nregistry", BLUE_SOFT, NAVY)
    cfg = node(5.85, y_f, cw, h, "config", LIGHT_GREY, GREY, fs=10)
    sch = node(8.35, y_f, cw, h, "schemas", LIGHT_GREY, GREY, fs=10)
    down(neural, loader)
    down(symb, trials)
    down(xai, cfg)
    down(cache, sch)

    ax.text(5.8, 0.28,
            "Evaluation also uses the extractor, validator and data loader for the paired benchmark.",
            ha="center", fontsize=8.5, color=GREY, style="italic")

    return _save(fig, "05_components.png")


def diagram_references_map():
    fig, ax = plt.subplots(figsize=(11.5, 7.2))
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 7.2)
    ax.axis("off")
    ax.text(5.75, 6.9, "Literature References Implementation Map",
            ha="center", fontsize=15, fontweight="bold", color=NAVY)
    ax.text(5.75, 6.55, "Each cited paper informs a specific module of EthiMatch.",
            ha="center", fontsize=10, color=GREY, style="italic")

    refs = [
        ("Carlisle et al. (2015)",          "Trial-accrual\nbottleneck",        0.3, 5.6),
        ("Lee et al. (2020) - BioBERT",     "Biomedical NER\nbackbone",         0.3, 4.6),
        ("Johnson et al. (2023) - MIMIC-IV","Real EHR\nbenchmark data",         0.3, 3.6),
        ("Loaiza-Bonilla et al. (2026)",    "Neuro-symbolic\nclinical safety",  0.3, 2.6),
        ("Lundberg & Lee (2017) - SHAP",    "Interpretable\nattribution",       0.3, 1.6),
        ("Zitianellis (2025)",              "Pre-screening &\nclinical adopt.", 0.3, 0.6),
    ]
    targets = [
        ("Problem motivation\n(README, proposal)",   8.4, 5.6, GREY),
        ("neural_extractor.py\n(d4data/biomedical-ner-all)", 8.4, 4.6, GREEN),
        ("data_loader.py\n(MIMICDualSourceProvider)",        8.4, 3.6, NAVY),
        ("symbolic_validator.py\n+ ethimatch_pipeline.py",   8.4, 2.6, LAVENDER),
        ("xai_explainer.py\n(criteria weighting)",           8.4, 1.6, GOLD),
        ("config.py + UI\n(INCONCLUSIVE verdict)",           8.4, 0.6, RED),
    ]

    for (ref_title, ref_text, x, y), (target_text, tx, ty, color) in zip(refs, targets):
        _bbox(ax, (x, y), 3.4, 0.85,
              f"{ref_title}\n{ref_text}",
              fill=BLUE_SOFT, edge=NAVY, fontsize=9.0)
        _bbox(ax, (tx, ty), 3.0, 0.85,
              target_text, fill=LIGHT_GREY, edge=color, fontsize=9.0)
        _arrow(ax, (x + 3.4, y + 0.42), (tx, ty + 0.42), color=color, lw=1.8)

    return _save(fig, "06_references_map.png")


def diagram_evaluation():
    """Evaluation methodology: top-down flow, short labels, no overflow."""
    fig, ax = plt.subplots(figsize=(11, 9.2))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 9.2)
    ax.axis("off")

    ax.text(5.5, 8.85, "Evaluation Methodology",
            ha="center", fontsize=15, fontweight="bold", color=NAVY)
    ax.text(5.5, 8.48, "Same patients, same neural extraction, two decision logics.",
            ha="center", fontsize=10, color=GREY, style="italic")

    def box(x, y, w, h, text, *, fill=BLUE_SOFT, edge=NAVY, fs=10):
        _bbox(ax, (x, y), w, h, text, fill=fill, edge=edge, fontsize=fs)

    def down(x, y0, y1):
        _arrow(ax, (x, y0), (x, y1), lw=2.0)

    # Centre column boxes
    cw, ch = 6.4, 0.95
    cx = (11 - cw) / 2  # 2.3

    # 1. Cohort
    y1 = 7.25
    box(cx, y1, cw, ch, "Patient cohort\nSynthetic  |  CSV  |  MIMIC-IV Demo",
        fill=BLUE_SOFT, edge=TEAL, fs=11)

    # 2. Extractor
    y2 = 5.95
    box(cx, y2, cw, ch, "Shared neural extractor (BioBERT)\nIdentical entities for both paths",
        fill=GREEN_SOFT, edge=GREEN, fs=11)
    down(5.5, y1, y2 + ch)

    # 3. Two paths
    pw, ph = 4.4, 1.05
    y3 = 4.45
    xa, xb = 0.7, 5.9
    box(xa, y3, pw, ph, "Path A  —  Neuro-symbolic\nValidator gates eligibility",
        fill=PURPLE_SOFT, edge=LAVENDER, fs=11)
    box(xb, y3, pw, ph, "Path B  —  Pure neural\nInclusion-only, no rules",
        fill="#FDECEC", edge=RED, fs=11)
    _arrow(ax, (5.5, y2), (xa + pw / 2, y3 + ph), lw=2.0)
    _arrow(ax, (5.5, y2), (xb + pw / 2, y3 + ph), lw=2.0)

    # 4. Compare (gold is stated inside this box — no side overlap)
    y4 = 2.95
    box(cx, y4, cw, 1.05,
        "Compare both paths against gold labels\nPrecision  ·  Recall  ·  F1  ·  FPR",
        fill=ORANGE_SOFT, edge=GOLD, fs=11)
    _arrow(ax, (xa + pw / 2, y3), (4.4, y4 + 1.05), lw=1.8)
    _arrow(ax, (xb + pw / 2, y3), (6.6, y4 + 1.05), lw=1.8)

    # 5. McNemar
    y5 = 1.55
    box(cx, y5, cw, 1.05,
        "McNemar's paired test (McNemar, 1947)\nSame patients: is Path A better than Path B?",
        fill=PURPLE_SOFT, edge=LAVENDER, fs=10.5)
    down(5.5, y4, y5 + 1.05)

    # 6. Outputs
    y6 = 0.25
    box(cx, y6, cw, 0.95,
        "Outputs for the report\ncomparative_benchmark.json  +  2D figures",
        fill=LIGHT_GREY, edge=NAVY, fs=10.5)
    down(5.5, y5, y6 + 0.95)

    return _save(fig, "07_evaluation.png")


def diagram_naming_cheatsheet():
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.6)
    ax.axis("off")
    ax.text(5, 5.3, "Naming Convention Cheat-Sheet  (PEP 8 compliant)",
            ha="center", fontsize=15, fontweight="bold", color=NAVY)

    rows = [
        ("Modules / files",  "lower_snake_case.py",     "silver_cache.py"),
        ("Classes",          "PascalCase",              "EthiMatchPipeline"),
        ("Functions",        "snake_case (verb-led)",   "compute_input_hash()"),
        ("Variables",        "snake_case",              "patient_id, note_hash"),
        ("Constants",        "UPPER_SNAKE_CASE",        "ALLOWED_DISEASES"),
        ("Booleans",         "is_/has_ prefix",         "is_conditionally_eligible"),
        ("Private helpers",  "_leading_underscore",     "_safe_filename()"),
        ("Type hints",       "PEP 484 throughout",      "def f(x: str) -> int"),
        ("Domain terms",     "use real clinical words", "ecog_ps, biomarker"),
    ]
    headers = ["Code element", "Rule", "Example"]
    col_x = [0.4, 3.4, 6.7]
    col_w = [3.0, 3.3, 3.4]
    header_y = 4.65
    for i, txt in enumerate(headers):
        _bbox(ax, (col_x[i], header_y), col_w[i], 0.45, txt,
              fill=NAVY, edge=NAVY, text_color=WHITE, fontsize=10.5)

    for j, (a, b, c) in enumerate(rows):
        y = 4.15 - j * 0.45
        fill = LIGHT_GREY if j % 2 == 0 else WHITE
        for i, txt in enumerate([a, b, c]):
            _bbox(ax, (col_x[i], y), col_w[i], 0.4, txt,
                  fill=fill, edge=GREY, text_color=NAVY,
                  fontsize=9.8, fontweight="normal")
    return _save(fig, "08_naming_cheatsheet.png")


def main() -> None:
    print("[diagrams] generating...")
    diagram_architecture()
    diagram_dataflow()
    diagram_use_case()
    diagram_flowchart()
    diagram_components()
    diagram_references_map()
    diagram_evaluation()
    diagram_naming_cheatsheet()
    print(f"[diagrams] done. Assets in {ASSETS}")


if __name__ == "__main__":
    main()
