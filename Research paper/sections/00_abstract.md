# Abstract

**Target: 200 words. Draft once, rewrite after Results are final.**

Structure (one or two sentences each):

1. **Problem.** Clinical trial pre-screening with purely neural models can misread negation and produce confident but wrong matches, which is unsafe in a trial-enrolment setting.
2. **Gap.** Existing systems rarely separate reading the note from applying the protocol, and rarely expose an explicit *missing information* outcome.
3. **Approach.** We present EthiMatch, a neuro-symbolic pipeline: biomedical NER extracts clinical facts, then a deterministic JSON rule engine returns ELIGIBLE / INELIGIBLE / **INCONCLUSIVE**.
4. **Evaluation.** We compare the full pipeline against a pure-neural inclusion heuristic on identical NER outputs over a synthetic oncology cohort (*n* = 100, six trials), with a cross-source check on MIMIC-IV Demo.
5. **Headline numbers.** F1 65.5% vs. 56.2%; precision 64.5% vs. 48.7%; false-positive rate **0.6% vs. 2.4%**; McNemar *p* ≈ 0.067 (not significant at α = 0.05).
6. **Honest limitation.** Directional improvement only; synthetic + public-demo data; gold standard derived from structured fields.
7. **Contribution sentence.** A reproducible neuro-symbolic prototype with INCONCLUSIVE semantics, dual-source evaluation, and an audit-first UI.

---

<!-- Final abstract will go below this line. Keep the draft above for traceability. -->
