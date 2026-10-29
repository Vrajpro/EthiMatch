# Paper outline — EthiMatch

**Working title:** *EthiMatch: A Neuro-Symbolic Pipeline for Safer Clinical Trial Pre-Screening with Explicit INCONCLUSIVE Semantics*

**Target length:** 8 pages, two-column (≈ 6,000 words incl. references).
**Target audience:** Applied-ML / health-informatics venue (see `venue-notes.md`).

---

## Headline claim (one sentence)

> On identical biomedical-NER inputs over a synthetic oncology cohort (*n* = 100, six trials), inserting a deterministic symbolic validator with explicit INCONCLUSIVE semantics lowers the false-positive rate from 2.4% to 0.6% while improving F1 from 56.2% to 65.5%, at the cost of statistical significance only directional (McNemar *p* ≈ 0.067).

Everything in the paper must defend or qualify this sentence.

---

## Section budget

| # | Section | Words | Pages | Must contain |
|---|---------|-------|-------|--------------|
| 0 | Abstract | 200 | 0.25 | Problem, approach, headline numbers, limitation |
| 1 | Introduction | 600 | 0.75 | Why trial matching, why pure-neural is unsafe, our contribution (3 bullets) |
| 2 | Related work | 700 | 1.0  | Clinical NLP, trial-matching systems (TrialGPT, Criteria2Query), neuro-symbolic AI |
| 3 | Methods | 1,200 | 1.5 | Pipeline diagram, NER layer, symbolic validator, INCONCLUSIVE rule, datasets, baseline design |
| 4 | Results | 900 | 1.25 | Main table (synthetic), cross-source table (MIMIC-IV Demo), McNemar, ablation if space |
| 5 | Discussion | 700 | 1.0 | Why FPR drop matters clinically, interpretation of non-significance, failure cases |
| 6 | Limitations & ethics | 400 | 0.5 | Synthetic data, structured gold standard, single annotator, no clinician review |
| 7 | Conclusion | 200 | 0.25 | Restate contribution, one line of future work |
| — | References | — | 1.0 | ~25 refs, see `references/references.bib` |

Total ≈ 4,900 words of body + references → fits an 8-page two-column template.

---

## Three contributions (must appear verbatim in Introduction)

1. A reproducible neuro-symbolic trial-matching pipeline that returns **ELIGIBLE / INELIGIBLE / INCONCLUSIVE** rather than a single soft score, with the symbolic layer isolated for paired evaluation.
2. A **dual-source** evaluation protocol — Synthea (synthetic) and MIMIC-IV Demo (public structured) — using one shared patient-profile contract.
3. An **audit-first UI** (Streamlit, four pages) that exposes rule-level PASS/FAIL/INCONCLUSIVE evidence for every match, designed for PDF-only academic review.

---

## Figure plan

| Fig | Content | Source |
|-----|---------|--------|
| 1 | System architecture (neural → symbolic → audit) | `docs/figures/01_architecture.png` |
| 2 | Data flow across layers | `docs/figures/02_dataflow.png` |
| 3 | Example symbolic rule with INCONCLUSIVE branch | New — build from a JSON protocol in `ethimatch/trials/` |
| 4 | Results plot (F1 / Precision / FPR, EthiMatch vs. baseline) | New — generate from `ethimatch/results/comparative_benchmark.json` |

Keep to 3–4 figures. Everything else goes in tables.

---

## Table plan

| Tbl | Content | Source |
|-----|---------|--------|
| 1 | Main synthetic benchmark | `ethimatch/results/comparative_benchmark.json` |
| 2 | Cross-source summary (Synthea vs. MIMIC-IV Demo) | `ethimatch/results/thesis/final_benchmark_table.md` |
| 3 | Error taxonomy (FP, FN, INCONCLUSIVE counts) | Derived during Results drafting |

---

## Writing order (same as `README.md`)

1. Abstract (draft) → 2. Tables → 3. Methods → 4. Results → 5. Intro + Related Work → 6. Discussion + Limitations + Conclusion → 7. Abstract (rewrite).
