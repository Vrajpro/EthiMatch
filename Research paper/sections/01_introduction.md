# 1. Introduction

**Target: ~600 words. Write after Methods and Results are drafted.**

## Paragraph plan

1. **Hook — scale of the problem.**
   Clinical trial recruitment is a known bottleneck; eligibility screening is manual and error-prone. Cite one epidemiology / recruitment stat.

2. **Why current ML approaches are insufficient.**
   Transformer-based biomedical NLP has advanced extraction, but end-to-end neural matchers (a) mis-handle negation and hedging and (b) produce a single soft score that hides *missing information*. In a trial-enrolment setting the cost of a false positive is clinically meaningful.

3. **Our position.**
   We argue that the *reading* step and the *rule-application* step should be structurally separated. The neural layer extracts; the symbolic layer decides. Missing-but-required evidence should surface as an explicit **INCONCLUSIVE** outcome instead of being imputed.

4. **What EthiMatch is.**
   A neuro-symbolic pre-screening pipeline comprising:
   - biomedical NER with negation handling (`d4data/biomedical-ner-all`);
   - a deterministic symbolic validator over JSON-encoded protocol rules;
   - an audit-first Streamlit UI exposing rule-level evidence.

5. **Contributions (verbatim bullets).**
   - A reproducible neuro-symbolic trial-matching pipeline with explicit INCONCLUSIVE semantics, where the symbolic layer can be isolated for paired evaluation on identical NER inputs.
   - A dual-source evaluation protocol (Synthea + MIMIC-IV Demo) over one shared patient-profile contract.
   - An audit-first UI designed for PDF-only academic review, exposing PASS / FAIL / INCONCLUSIVE evidence per criterion.

6. **Headline result + honest caveat (one sentence each).**
   > On a synthetic oncology cohort (*n* = 100, six trials), the pipeline lowers false-positive rate from 2.4% to 0.6% and raises F1 from 56.2% to 65.5% versus a pure-neural baseline on identical NER inputs.
   > The improvement is directional; McNemar *p* ≈ 0.067 does not reach α = 0.05, and all evaluation uses synthetic or public-demo data with a structured gold standard.

7. **Roadmap.** One sentence pointing to §3 Methods, §4 Results, §5 Discussion.

---

<!-- Final prose below this line. -->
