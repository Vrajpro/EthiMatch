# 4. Results

**Target: ~900 words. One table/figure per paragraph.**

## 4.1 Main benchmark (synthetic cohort)

Reference: `ethimatch/results/comparative_benchmark.json` → paper Table 1.

| Metric | EthiMatch | Pure-neural baseline |
|--------|-----------|----------------------|
| F1 | **65.5%** | 56.2% |
| Precision | **64.5%** | 48.7% |
| Recall | *fill from JSON* | *fill from JSON* |
| False-positive rate | **0.6%** | 2.4% |

Prose points to make:
- Headline is the **4× reduction** in FPR (2.4 → 0.6).
- Precision gain is larger than recall gain → consistent with a symbolic layer that *refuses to decide* on missing evidence rather than guessing positive.
- Note which patients moved category (FP → INCONCLUSIVE is the main shift to describe).

## 4.2 Paired significance

McNemar on discordant pairs:
- Discordant favouring EthiMatch: **14**
- Discordant favouring baseline: **5**
- McNemar *p* ≈ **0.067**

Write exactly one sentence of interpretation:
> The direction of effect favours EthiMatch but does not reach α = 0.05; we therefore report a directional improvement rather than a confirmed one.

Do **not** write "trend toward significance" — that phrase is correctly disliked by reviewers.

## 4.3 Cross-source check (MIMIC-IV Demo)

Reference: `ethimatch/results/thesis/final_benchmark_table.md` → paper Table 2.

- Absolute F1 drops on MIMIC-IV Demo for both systems (small, structured-only, few oncology-relevant cases).
- The **relative** FPR reduction pattern persists.
- Framing: supporting evidence, not a primary claim.

## 4.4 Qualitative error taxonomy

Build Table 3 during drafting by sampling ~20 patients:
- FP → INCONCLUSIVE conversions (expected majority).
- Remaining FPs (symbolic layer mis-mapped evidence).
- New FNs introduced by the symbolic layer (should be few; if more than ~5, discuss).

## 4.5 What this section must **not** claim

- No "statistically significant improvement" at α = 0.05.
- No clinical validation.
- No cross-site generalisation.

---

<!-- Final prose below this line. -->
