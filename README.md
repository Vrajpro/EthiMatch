# EthiMatch

**Neuro-symbolic clinical trial matching** — MSc Data Science research prototype (Coventry University, 7005SCN).

| | |
|---|---|
| **Student** | Vraj Dipakkumar Parekh (16485659) |
| **Course** | MSc Data Science |
| **Supervisor** | Someyah Bazin |
| **Repository** | https://github.com/Vrajpro/EthiMatch |
| **Examiner Q&A** | [Examiner-QA.md](Examiner-QA.md) |

EthiMatch helps **pre-screen** patients against oncology trial criteria. It is a **research prototype for academic assessment**, not a clinical product, and must not be used for real enrolment decisions.

---

## What this system does

Clinical trial matching usually means reading notes and checking inclusion/exclusion rules. A purely neural model can misread negation (for example treating “no history of diabetes” as a positive finding) or guess when data are missing.

EthiMatch separates the two jobs:

1. **Neural layer** — biomedical NER extracts clinical facts from notes  
2. **Symbolic layer** — a deterministic JSON rule engine returns **ELIGIBLE**, **INELIGIBLE**, or **INCONCLUSIVE** (never guesses missing fields)

The Streamlit interface has four pages: **Dashboard**, **Patient Matching**, **Cohort Discovery**, and **Evaluation**.

---

## Main evaluation result

Compared with a pure-neural baseline on the **same patients** and **same extracted entities** (symbolic decision layer isolated):

| Metric | EthiMatch | Pure-neural baseline |
|--------|-----------|----------------------|
| F1 | **65.5%** | 56.2% |
| Precision | **64.5%** | 48.7% |
| False positive rate | **0.6%** | 2.4% |
| McNemar *p* | ≈ 0.067 (**not** significant at α = 0.05) | |

Source: `ethimatch/results/comparative_benchmark.json` (synthetic *n* = 100, six trials).

The strongest supported claim is a **lower false-positive rate** under synthetic/demo conditions. This project does **not** claim clinical deployment readiness or statistical significance at 0.05.

---

## Repository structure

```
EthiMatch/
├── ethimatch/                 Application (pipeline, UI, evaluation)
│   ├── app.py                 Streamlit entry point
│   ├── ethimatch_pipeline.py  Five-stage orchestrator
│   ├── neural_extractor.py    Biomedical NER
│   ├── symbolic_validator.py  Rule engine
│   ├── evaluation.py          Benchmark harness
│   ├── trials/                JSON trial protocols
│   ├── results/               Saved benchmark outputs
│   └── requirements.txt
├── data/
│   ├── synthea/               Synthea synthetic CSVs (core files)
│   └── mimic/                 MIMIC-IV Demo tables
├── docs/
│   ├── figures/               Architecture diagrams and UI screenshots
│   └── reports/               Project report (Word)
├── Examiner-QA.md             Common examiner questions and answers
└── README.md
```

---

## Data included

| Source | Location | Notes |
|--------|----------|--------|
| **Synthea** | `data/synthea/` | Core CSVs: patients, conditions, medications, careplans, encounters |
| **MIMIC-IV Demo** | `data/mimic/` | Public 100-patient structured subset (no credential required) |

Four Synthea exports are **not** on GitHub (over GitHub’s file-size limits): `claims_transactions.csv`, `observations.csv`, `imaging_studies.csv`, `claims.csv`. The app runs with the core CSVs. Details: [data/README.md](data/README.md).

---

## Quick start

```powershell
cd ethimatch
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

First run downloads the Hugging Face model `d4data/biomedical-ner-all` (may take a few minutes on CPU).

Optional — re-run evaluation:

```powershell
cd ethimatch
.\venv\Scripts\python.exe evaluation.py
```

---

## Key files for examiners

| Topic | Path |
|-------|------|
| How to run / what I built | This README |
| Short Q&A | [Examiner-QA.md](Examiner-QA.md) |
| Main benchmark numbers | `ethimatch/results/comparative_benchmark.json` |
| Cross-source table | `ethimatch/results/thesis/final_benchmark_table.md` |
| Trial rules | `ethimatch/trials/` |
| UI screenshots | `docs/figures/screenshots/` |

---

## Disclaimer

EthiMatch is for this MSc assessment only. Do not use it for real patient care, trial enrolment, or regulatory clinical workflows.
