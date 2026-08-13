# EthiMatch — Examiner Q&A

**Project:** EthiMatch (7005SCN Individual Research Project)  
**Student:** Vraj Dipakkumar Parekh (16485659)  
**Repository:** https://github.com/Vrajpro/EthiMatch  
**Purpose of this file:** Because assessment is PDF-only, this note answers the questions an examiner is most likely to ask after reading the project report and opening the repository.

EthiMatch is a **research prototype**, not a clinical product. It must not be used for real patient care or enrolment decisions.

---

## 1. What did you actually build?

EthiMatch is an end-to-end neuro-symbolic clinical-trial matching prototype:

1. **Neural layer** — biomedical NER (+ regex / negation handling) extracts eligibility features from notes  
2. **Symbolic layer** — deterministic JSON protocol rules return ELIGIBLE / INELIGIBLE / INCONCLUSIVE  
3. **Explainability** — audit narratives and rule-level outcomes for human review  
4. **UI** — Streamlit pages: Dashboard, Patient Matching, Cohort Discovery, Evaluation  

Evidence in the report: Chapter 4 figures (architecture + screenshots).  
Evidence in the repo: `ethimatch/app.py`, `ethimatch_pipeline.py`, `neural_extractor.py`, `symbolic_validator.py`, `ui/pages/`.

---

## 2. What is “neuro-symbolic” here (is this just NER + if-else)?

Yes, it is deliberately a hybrid:

- Neural module **perceives** text (entities may be incomplete or uncertain)  
- Symbolic module **decides** protocol fitness with explicit, inspectable rules  
- Missing mandatory evidence becomes **INCONCLUSIVE**, not a forced binary guess  

The research point is separation of concerns for safety and auditability, not claiming a new foundational ML algorithm.

---

## 3. What is the pure-neural baseline, and is the comparison fair?

Both systems use the **same extracted entities** for a patient.  
The baseline applies an inclusion-oriented heuristic **without** full symbolic exclusion / missing-data discipline.  
EthiMatch runs the full symbolic validator.

So the comparison isolates the decision layer, not a different NER model.

See report Chapter 3 (comparative design) and `ethimatch/evaluation.py`.

---

## 4. How is the gold standard created? Is it circular?

Gold labels are derived from **structured profile/CSV fields** validated by protocol rules (active conditions, demographics, etc.), independent of free-text NER success.

That is reproducible and useful for engineering evaluation, but weaker than independent clinician chart review of free text. The report states this limitation explicitly (Ch6/Ch8).

It is not “the neural model labelled by itself,” but it **is** aligned with the symbolic protocol definition — that is why claim discipline matters.

---

## 5. Why Synthea and MIMIC-IV Demo?

- **Synthea:** scalable synthetic cohort, no privacy barrier, controlled testing  
- **MIMIC-IV Demo:** public de-identified structured demo data for an external stress test  

This supports dual-source evaluation under MSc/ethics constraints. It does **not** equal multi-site hospital validation.

---

## 6. Which model do you use — BioBERT or DistilBERT?

The deployed extractor is **`d4data/biomedical-ner-all`** (DistilBERT-style biomedical NER via Hugging Face), chosen for CPU feasibility.

BioBERT is cited as the research paradigm, not as the exact checkpoint identity. The report is written to avoid overselling the model name.

---

## 7. What are the main results I should trust?

Primary synthetic comparative run (`n = 100`, 6 trials), from `ethimatch/results/comparative_benchmark.json`:

| Metric | EthiMatch | Pure neural |
|--------|-----------|-------------|
| F1 | 65.5% | 56.2% |
| Precision | 64.5% | 48.7% |
| FPR | 0.6% | 2.4% |
| McNemar p | ≈ 0.067 (not significant at α = 0.05) | |

Strongest supported finding: **lower false-positive rate** (safety-oriented signal), with improved F1/precision on the main synthetic benchmark.

---

## 8. McNemar is not significant — what can you claim?

Claim carefully:

- Direction of discordant pairs favours EthiMatch (14 vs 5)  
- Effect is **not** statistically conclusive at α = 0.05 on this paired sample  
- Therefore the project claims a **supported safety trend / engineering result**, not statistical certainty  

This is stated in Abstract, Chapter 6, and claim-discipline tables.

---

## 9. MIMIC performance looks weak. Does that invalidate the project?

No — it bounds external validity.

MIMIC-IV Demo is small and not oncology-dense for these protocols, so absolute F1 can be modest while the safety pattern (lower FPR vs baseline) can still appear. The report treats MIMIC as a stress test, not the primary success claim.

---

## 10. What is novel for an MSc contribution?

Not “first neural trial matcher in literature.” Contribution is an open, reproducible prototype that integrates:

- dual-source intake under one patient-profile contract  
- JSON-governed protocols  
- explicit INCONCLUSIVE semantics  
- paired comparative evaluation vs pure-neural baseline  
- clinician-facing audit UI for PDF-only assessment  

---

## 11. Can the examiner verify numbers without running the app?

Yes:

1. Open `ethimatch/results/comparative_benchmark.json`  
2. Compare with Abstract / Table 1 / Chapter 6  
3. Cross-source summary also appears in report Table 3 and thesis tables under `ethimatch/results/thesis/`  

Screenshots in the report show the UI pathways used for matching, cohort discovery, and evaluation.

---

## 12. How do I run the system from GitHub?

```powershell
cd ethimatch
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Full instructions: repository `README.md`.

Note: a few very large Synthea CSVs were excluded from GitHub due to file-size limits; core CSVs needed for the demo pathway are included. Details are in `data/README.md`.

---

## 13. Where is explainability?

Not only SHAP-style feature attribution language:

- rule-level PASS/FAIL/INCONCLUSIVE outcomes  
- Narrative / Entities / Audit panels in Patient Matching  
- PDF export path for audit handoff  

Human remains the decision owner.

---

## 14. Ethics and data protection — what was done?

- No identifiable real patient data processed  
- Synthea synthetic + MIMIC-IV Demo boundaries respected  
- No patient notes uploaded to external generative AI services  
- Amber AI declaration included in the report  

Production clinical deployment was out of scope.

---

## 15. What does EthiMatch explicitly NOT claim?

- Not ready for real patient care / regulatory deployment  
- Not a substitute for clinician enrolment judgement  
- Not statistically conclusive McNemar significance at 0.05 on the main synthetic pair  
- Not validated on large multi-site clinician-labelled free-text gold standards  

See report Tables 5 and 7 (claim discipline).

---

## 16. If something fails when I run it, what should I check first?

1. Python 3.11 + venv from `ethimatch/requirements.txt`  
2. Run from `ethimatch/` so local imports resolve  
3. First NER download can be slow on CPU  
4. Use Evaluation page cached synthetic results for quick verification of reported metrics  

---

## Short viva-style answers (one line each)

| Question | One-line answer |
|----------|-----------------|
| What is novel? | Reproducible neuro-symbolic matching with INCONCLUSIVE semantics, JSON protocols, paired eval, and audit UI. |
| Why symbolic layer? | To reduce unsafe false positives and make protocol criteria explicit/auditable. |
| Why not clinically ready? | Synthetic/demo data, limited protocols, structured gold, McNemar not significant at 0.05. |
| Main empirical finding? | Lower FPR and better F1/precision on the main synthetic benchmark vs pure neural. |
| Where is proof? | Report Ch4–Ch6 + `results/comparative_benchmark.json` + UI screenshots. |

---

If further clarification is needed, the project report and this repository are intended to be self-contained for PDF-only examination.
