# 7. Limitations and ethics

**Target: ~400 words. Honesty is a strength here, not a weakness.**

## 7.1 Limitations

- **Synthetic and public-demo data only.** Synthea and MIMIC-IV Demo were chosen for ethical and reproducibility reasons; neither substitutes for live hospital records.
- **Structured gold standard.** Gold labels were derived from structured patient fields passed through the same JSON rules used by the system. This is weaker than independent clinician review of free-text notes and risks under-counting free-text-only cases.
- **Directional, not significant.** Paired McNemar *p* ≈ 0.067 does not meet α = 0.05. We report a *directional* improvement and do not claim significance.
- **Narrow protocol set.** Six oncology trials. Generalisation to other disease areas is not demonstrated.
- **Single-site, single-annotator design.** No inter-annotator agreement, no multi-site external validation.
- **NER ceiling.** `d4data/biomedical-ner-all` is a general biomedical NER, not a domain-adapted fine-tune; recall is bounded by its extraction quality.

## 7.2 Ethics

- No identifiable patient data were used.
- No clinical notes were sent to external generative AI services for processing.
- The system is a **research prototype** for academic assessment; it must not be used for real patient care, trial enrolment, or regulatory workflows.
- AI drafting tools were used in preparing the manuscript; model outputs were reviewed and edited before inclusion. All numerical results come from the open-source evaluation harness, not from an LLM.

## 7.3 What this paper does **not** claim

- Readiness for clinical deployment or regulatory use.
- Replacement of clinician judgement on enrolment decisions.
- Statistical significance at α = 0.05 on the main paired comparison.
- Validation on large multi-site clinician-labelled free-text data.

---

<!-- Final prose below this line. -->
