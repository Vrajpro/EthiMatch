# 5. Discussion

**Target: ~700 words.**

## 5.1 Why the FPR drop matters clinically (even without significance)

- A false-positive match in trial pre-screening wastes clinician time and risks approaching an ineligible patient.
- Reducing FPR 4× (2.4 → 0.6) on identical inputs is a meaningful operational signal even at *p* ≈ 0.067.
- Reframe: the paper's claim is about **where the symbolic layer moves errors to** (FP → INCONCLUSIVE), not about leaderboard F1.

## 5.2 Why pure-neural inclusion heuristics over-call positives

- No explicit missing-information outcome → anything resembling a match is a match.
- Negation and hedging in the free text leak through unless post-processed.
- The symbolic layer short-circuits both by requiring named evidence per criterion.

## 5.3 The role of INCONCLUSIVE

- INCONCLUSIVE converts an unsafe "yes" into an actionable "ask a clinician".
- In the audit UI, each INCONCLUSIVE criterion names the missing field, which is the handoff point to a human reviewer.
- This is the explicit design mechanism; discuss it as a *contribution*, not an afterthought.

## 5.4 Failure cases to be honest about

- Protocols with vague free-text criteria (e.g. "adequate organ function") cannot be fully encoded in the current JSON schema → symbolic layer returns INCONCLUSIVE often.
- Over-reliance on structured fields in the gold standard means we probably under-count free-text-only cases.
- NER model is DistilBERT-class, not a domain-adapted BioBERT fine-tune → ceiling on recall.

## 5.5 Positioning versus LLM-based matchers (e.g. TrialGPT)

- An LLM can be more flexible on free-text criteria but typically does not expose a per-criterion audit path.
- Complementary, not competing: an LLM could feasibly populate the structured evidence that the symbolic layer then validates. Flag as future work in §6.

---

<!-- Final prose below this line. -->
