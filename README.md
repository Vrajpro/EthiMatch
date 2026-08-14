# EthiMatch

Neuro-symbolic clinical trial matching prototype for oncology pre-screening.

The system combines biomedical named-entity recognition with a deterministic
symbolic rule engine and explainable audit reports. It is a research prototype
for academic evaluation, not a clinical product.

**Module:** 7005SCN Individual Research Project  
**Author:** Vraj Dipakkumar Parekh (16485659)  
**Course:** MSc Data Science, Coventry University

Repository: https://github.com/Vrajpro/EthiMatch

Examiner Q&A (my answers for PDF-only assessment):  
https://github.com/Vrajpro/EthiMatch/blob/main/docs/EXAMINER_FAQ.md

---

## Features

- Five-stage pipeline: cache lookup, structured early-exit, NER, symbolic validation, XAI narrative
- Streamlit UI: Dashboard, Patient Matching, Cohort Discovery, Evaluation
- Dual data pathway: Synthea CSVs and MIMIC-IV Demo
- JSON trial protocols under `ethimatch/trials/`
- Comparative benchmark vs a pure-neural baseline (precision, recall, F1, FPR, McNemar)

---

## Repository layout

```
EthiMatch/
├── ethimatch/                 Application package
│   ├── app.py                 Streamlit entry point
│   ├── ethimatch_pipeline.py  Pipeline orchestrator
│   ├── neural_extractor.py    Biomedical NER
│   ├── symbolic_validator.py  Rule engine
│   ├── evaluation.py          Benchmark harness
│   ├── ui/                    Streamlit pages and presentation
│   ├── services/              UI service layer
│   ├── data_access/           Data providers
│   ├── trials/                Trial protocol JSON
│   ├── scripts/               CLI utilities (QA, materialize, thesis runs)
│   ├── results/               Saved evaluation outputs
│   └── requirements.txt
├── data/
│   ├── synthea/               Synthea input CSVs
│   └── mimic/                 MIMIC-IV Demo tables
├── docs/
│   ├── figures/               Architecture and UI figures
│   └── reports/               Project report (Word)
├── tools/doc_builder/         Report/diagram build scripts
└── README.md
```

---

## Setup

```powershell
cd ethimatch
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run the app

```powershell
cd ethimatch
.\venv\Scripts\Activate.ps1
streamlit run app.py
```

## Re-run evaluation (optional)

```powershell
cd ethimatch
.\venv\Scripts\python.exe evaluation.py
```

Saved metrics live under `ethimatch/results/` (including `comparative_benchmark.json`).

---

## Disclaimer

EthiMatch is for research and assessment only. It must not be used for real patient
care, enrolment decisions, or regulatory clinical workflows.
