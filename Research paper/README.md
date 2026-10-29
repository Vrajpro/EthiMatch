# Research paper — EthiMatch

This folder is a dedicated workspace for turning the EthiMatch MSc dissertation into a short, publishable **research paper** (6–10 pages, IMRaD).

It is intentionally separate from `docs/reports/` (which holds the full MSc report and design document) so the paper can be drafted, versioned, and submitted on its own timeline.

---

## How this folder is organised

```
Research paper/
├── README.md            This guide — read first
├── outline.md           Target structure + per-section word budget
├── venue-notes.md       Candidate venues and formatting notes
├── sections/            One Markdown file per paper section
│   ├── 00_abstract.md
│   ├── 01_introduction.md
│   ├── 02_related_work.md
│   ├── 03_methods.md
│   ├── 04_results.md
│   ├── 05_discussion.md
│   ├── 06_conclusion.md
│   └── 07_limitations_ethics.md
├── figures/             Figures prepared for the paper (reuse from docs/figures/)
│   └── README.md
├── tables/              Camera-ready tables (CSV + rendered Markdown)
│   └── README.md
└── references/          BibTeX and reading notes
    └── references.bib
```

---

## The writing workflow I recommend

Work section-by-section in **this order** — it minimises rewrites because each step constrains the next.

1. **Lock the claim** (`sections/00_abstract.md`)
   - One sentence: *"We show that a neuro-symbolic layer reduces false-positive trial matches from X% to Y% on identical NER inputs."*
   - If you cannot write that sentence crisply, do not start the paper yet.

2. **Fix the results table** (`tables/`)
   - Pull numbers verbatim from `ethimatch/results/comparative_benchmark.json` and `ethimatch/results/thesis/final_benchmark_table.md`.
   - Decide **now** which numbers are headline, which are supporting, which are appendix.

3. **Draft Methods** (`sections/03_methods.md`)
   - Methods must be reproducible from this section alone. Cite exact file paths in the repo.

4. **Draft Results** (`sections/04_results.md`)
   - Each paragraph answers one research question with one table or figure.

5. **Draft Introduction + Related Work** (`sections/01_*`, `02_*`)
   - These are easiest to write last because now you know exactly what you are motivating.

6. **Draft Discussion, Limitations, Conclusion** (`sections/05_*`, `07_*`, `06_*`)
   - Keep limitations honest — especially McNemar p ≈ 0.067 and the structured gold standard.

7. **Rewrite the Abstract**
   - The first draft from step 1 will almost always need tightening after Results are final.

---

## Non-negotiable honesty guardrails

These come straight from `Examiner-QA.md` and must survive into the paper:

- Do **not** claim statistical significance at α = 0.05 (McNemar p ≈ 0.067).
- Do **not** claim clinical deployment readiness.
- Describe FPR reduction as the **primary** safety-relevant finding.
- State clearly that the gold standard is derived from **structured fields**, not clinician review of free text.
- Name the running NER model as `d4data/biomedical-ner-all`, not BioBERT.

---

## What the LLM guide (me) will do next

When you ask for help on a section I will:

1. Open the corresponding stub in `sections/`.
2. Pull real numbers / file paths from the repo rather than inventing them.
3. Draft in neutral academic voice, flagging any claim that is not supported by `ethimatch/results/`.
4. Keep the overall word budget in `outline.md` in sight so sections don't drift.

Tell me which section to start with, or say *"start with methods"* and I'll begin there.
