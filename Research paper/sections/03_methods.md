# 3. Methods

**Target: ~1,200 words. Reproducible from this section alone — cite repo paths.**

## 3.1 System overview

Pipeline diagram → `docs/figures/01_architecture.png` (reproduced here as Fig. 1).

Stages:
1. **Input normalisation** — one patient-profile contract shared by Synthea and MIMIC-IV Demo (`ethimatch/data/` loaders).
2. **Neural extraction** — biomedical NER + regex + negation handling (`ethimatch/neural_extractor.py`).
3. **Protocol loading** — JSON trial rules from `ethimatch/trials/`.
4. **Symbolic validation** — deterministic rule engine returning per-criterion PASS / FAIL / INCONCLUSIVE (`ethimatch/symbolic_validator.py`).
5. **Audit & narrative** — explainability layer rendered by the Streamlit UI (`ethimatch/app.py`).

Orchestration lives in `ethimatch/ethimatch_pipeline.py`.

## 3.2 Neural extraction layer

- Model: `d4data/biomedical-ner-all` (Hugging Face), DistilBERT-style biomedical NER, chosen for CPU-only reproducibility.
- Post-processing: regex fallbacks for lab values + ages; a negation pass to prevent "no history of X" being extracted as positive X.
- Output: list of typed entities per patient (condition, medication, demographic, lab).

## 3.3 Symbolic validation layer

- Protocols are **JSON documents** in `ethimatch/trials/`; each criterion carries an operator (`has`, `absent`, `age_between`, …), required evidence fields, and a severity.
- The validator maps NER entities → criteria → outcome:
  - **PASS** — evidence present and satisfied.
  - **FAIL** — evidence present and violated.
  - **INCONCLUSIVE** — required evidence absent in both NER output and structured fields.
- Patient-level outcome: ELIGIBLE iff all inclusion criteria PASS **and** no exclusion criterion FAILs; INELIGIBLE if any exclusion FAILs or any inclusion FAILs; otherwise INCONCLUSIVE.

> Design choice: INCONCLUSIVE is never auto-converted to ELIGIBLE. This is the mechanism that drives the FPR reduction reported in §4.

## 3.4 Pure-neural baseline

To isolate the effect of the symbolic layer, the baseline consumes the **same NER output** and applies an inclusion-oriented heuristic (match on presence of inclusion-criterion keywords, no explicit missing-information handling). Implementation: baseline branch in `ethimatch/evaluation.py`.

Fairness: identical patients, identical entities, identical trials. The only variable is the decision layer.

## 3.5 Datasets

| Dataset | Role | Access | Size used |
|---------|------|--------|-----------|
| Synthea | Main benchmark | Open synthetic | 100 patients, 6 oncology trials |
| MIMIC-IV Demo | Cross-source stress test | Public (no credential) | 100-patient structured subset |

Rationale: ethically usable and reproducible for an MSc project; explicitly not a substitute for validation on live records (see §6).

## 3.6 Gold standard construction

Gold labels are derived from **structured patient fields** (active conditions, demographics, medications) passed through the same JSON protocol rules.

Trade-off: this makes the benchmark reproducible and inspectable, at the cost of being weaker than independent clinician review of free-text notes. This is stated explicitly in §6.

## 3.7 Metrics

Primary: F1, Precision, Recall, False-Positive Rate (FPR).
Significance: McNemar's test on paired discordant decisions (EthiMatch vs. baseline on the same patient / trial pair).
Reported with 95% bootstrap CIs where space allows.

## 3.8 Reproducibility

- Code: `https://github.com/Vrajpro/EthiMatch`
- Entry: `ethimatch/evaluation.py`
- Saved outputs: `ethimatch/results/comparative_benchmark.json`, `ethimatch/results/thesis/final_benchmark_table.md`.
- Hardware: CPU-only; first run downloads the HF model.

---

<!-- Final prose below this line. -->
