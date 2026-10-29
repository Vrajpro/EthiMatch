# Figures for the paper

Keep this folder small — **3 to 4 figures max** in an 8-page submission.

## Reuse from the dissertation

Copy or symlink the ready assets from `docs/figures/`:

| Paper Fig | Source |
|-----------|--------|
| Fig. 1 Architecture | `docs/figures/01_architecture.png` |
| Fig. 2 Data flow | `docs/figures/02_dataflow.png` |

## New figures to generate

| Paper Fig | What | How |
|-----------|------|-----|
| Fig. 3 Example symbolic rule with INCONCLUSIVE branch | Diagram showing a JSON criterion → PASS/FAIL/INCONCLUSIVE | Draw from one real JSON file in `ethimatch/trials/` |
| Fig. 4 Headline bar chart (F1 / Precision / FPR, EthiMatch vs. baseline) | 3-group bar chart | Script against `ethimatch/results/comparative_benchmark.json` |

## File format rules

- Vector when possible (PDF / SVG) for anything with text.
- PNG only for screenshots.
- All axis labels large enough to read at 50% page width.
- Captions written in the section Markdown, not embedded in the image.
