"""
Build final thesis tables/figures from comparative_benchmark.json.

Outputs under results/thesis/:
  - final_benchmark_table.csv
  - final_benchmark_table.md
  - ablation_summary.md
  - figures/benchmark_overview.html
  - figures/benchmark_overview.png (optional if kaleido installed)
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import console  # noqa: F401
from console import json_dumps, safe_print

def _pct(v: Any) -> str:
    try:
        return f"{float(v) * 100:.1f}%"
    except (TypeError, ValueError):
        return "—"

def main() -> int:
    import json
    import plotly.graph_objects as go

    src = ROOT / "results" / "comparative_benchmark.json"
    if not src.is_file():
        raise FileNotFoundError(f"Missing benchmark file: {src}")
    payload = json.loads(src.read_text(encoding="utf-8"))
    comp = payload.get("comparative", {})

    out_dir = ROOT / "results" / "thesis"
    fig_dir = out_dir / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for source in ("csv", "synthetic", "mimic"):
        block = comp.get(source) or {}
        if not isinstance(block, dict) or block.get("error"):
            continue
        ns = block.get("neuro_symbolic") or {}
        pn = block.get("pure_neural") or {}
        rows.append(
            {
                "Source": source.upper(),
                "Neuro F1": _pct(ns.get("f1")),
                "Pure F1": _pct(pn.get("f1")),
                "F1 Delta": f"{(float(ns.get('f1', 0.0)) - float(pn.get('f1', 0.0))) * 100:+.1f}%",
                "Neuro FPR": _pct(ns.get("fpr")),
                "Pure FPR": _pct(pn.get("fpr")),
                "McNemar p": str((block.get("mcnemar") or {}).get("p_value_approx", "—")),
            },
        )

    csv_path = out_dir / "final_benchmark_table.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["Source"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    md_lines = [
        "# EthiMatch Final Benchmark Table",
        "",
        "| Source | Neuro F1 | Pure F1 | F1 Delta | Neuro FPR | Pure FPR | McNemar p |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        md_lines.append(
            f"| {r['Source']} | {r['Neuro F1']} | {r['Pure F1']} | {r['F1 Delta']} | "
            f"{r['Neuro FPR']} | {r['Pure FPR']} | {r['McNemar p']} |"
        )
    (out_dir / "final_benchmark_table.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    ablation = {
        r["Source"]: {
            "f1_delta": r["F1 Delta"],
            "neuro_fpr": r["Neuro FPR"],
            "pure_fpr": r["Pure FPR"],
        }
        for r in rows
    }
    (out_dir / "ablation_summary.md").write_text(
        "# Ablation Summary (With vs Without Symbolic Layer)\n\n"
        + json_dumps(ablation, indent=2)
        + "\n",
        encoding="utf-8",
    )

    labels = [r["Source"] for r in rows]
    neuro_f1 = [float((comp[s.lower()]["neuro_symbolic"] or {}).get("f1", 0.0)) for s in labels]
    pure_f1 = [float((comp[s.lower()]["pure_neural"] or {}).get("f1", 0.0)) for s in labels]
    neuro_fpr = [float((comp[s.lower()]["neuro_symbolic"] or {}).get("fpr", 0.0)) for s in labels]
    pure_fpr = [float((comp[s.lower()]["pure_neural"] or {}).get("fpr", 0.0)) for s in labels]

    fig = go.Figure()
    fig.add_bar(name="Neuro-Symbolic F1", x=labels, y=neuro_f1)
    fig.add_bar(name="Pure Neural F1", x=labels, y=pure_f1)
    fig.add_bar(name="Neuro-Symbolic FPR", x=labels, y=neuro_fpr)
    fig.add_bar(name="Pure Neural FPR", x=labels, y=pure_fpr)
    fig.update_layout(
        barmode="group",
        title="EthiMatch Final Benchmark (n=100)",
        yaxis_title="Score (0-1)",
        legend_title="Metric/Model",
    )

    html_path = fig_dir / "benchmark_overview.html"
    fig.write_html(str(html_path), include_plotlyjs="cdn")
    png_path = fig_dir / "benchmark_overview.png"
    try:
        fig.write_image(str(png_path), scale=2)
    except Exception:
        pass

    safe_print(f"Saved table CSV: {csv_path}")
    safe_print(f"Saved table MD : {out_dir / 'final_benchmark_table.md'}")
    safe_print(f"Saved figure   : {html_path}")
    if png_path.is_file():
        safe_print(f"Saved PNG      : {png_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
