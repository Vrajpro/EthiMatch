# EthiMatch

**Student:** Vraj Dipakkumar Parekh (16485659)  
**Module:** 7005SCN Individual Research Project  
**Course:** MSc Data Science, Coventry University  
**Supervisor:** Someyah Bazin

This is the source code for my MSc project. I built **EthiMatch**, a research prototype that helps pre-screen patients against clinical-trial rules. It is **not** a hospital product and must not be used for real enrolment decisions.

**Project report (PDF submission):** the marked dissertation is submitted through Turnitin. This repository is so an examiner can inspect the implementation, data, and saved results.

**Examiner Q&A (open this file on the GitHub home page):** [Examiner-QA.md](Examiner-QA.md)

---

## What I built, in plain terms

Matching a patient to a trial usually means reading notes and checking inclusion/exclusion criteria. A purely neural system can read text, but it can also guess when information is missing, or treat “no history of diabetes” as if diabetes were present.

I split the job into two parts:

1. **Neural part** — a biomedical NER model reads the note and pulls out facts (age, disease, biomarkers, and so on).
2. **Symbolic part** — a rule engine checks those facts against JSON trial protocols. If a required field is missing, the system returns **INCONCLUSIVE** instead of guessing.

The Streamlit app has four pages: Dashboard, Patient Matching, Cohort Discovery, and Evaluation.

---

## What I evaluated

I compared EthiMatch with a **pure-neural baseline** on the **same patients** and the **same extracted entities**. Only the decision layer changes. That was deliberate: I wanted to test the symbolic rules, not swap to a different NLP model.

Main synthetic run (`n = 100`, six trials), saved in `ethimatch/results/comparative_benchmark.json`:

| Metric | EthiMatch | Pure-neural baseline |
|--------|-----------|----------------------|
| F1 | 65.5% | 56.2% |
| Precision | 64.5% | 48.7% |
| FPR | 0.6% | 2.4% |
| McNemar p | ≈ 0.067 (not significant at 0.05) | |

I treat the lower false-positive rate as the main safety-related result. I do **not** claim statistical significance at α = 0.05, and I do **not** claim the system is ready for clinical use.

---

## Data in this repository

I used two open datasets. Both are in the `data/` folder.

### Synthea (synthetic patients)

Folder: `data/synthea/`

The app mainly needs:

- `patients.csv`
- `conditions.csv`
- `medications.csv`
- `careplans.csv`
- `encounters.csv`

Those files are in this repository, together with the other moderate-sized Synthea tables I used locally.

Four Synthea exports are **too large for GitHub** (GitHub blocks files over 100 MB). I kept them on my machine only:

- `claims_transactions.csv` (~296 MB)
- `observations.csv` (~88 MB)
- `imaging_studies.csv` (~50 MB)
- `claims.csv` (~40 MB)

The prototype still runs with the core CSVs above. `observations.csv` is only used to fill cancer stage when that file is present.

### MIMIC-IV Demo (public structured subset)

Folder: `data/mimic/`

This is the public demo (100 patients). No PhysioNet credential is required. Tables included:

- `patients`
- `admissions`
- `diagnoses_icd`
- `d_icd_diagnoses`
- `d_icd_procedures`
- `prescriptions`

I did **not** use identifiable real patient notes, and I did not send patient text to external generative AI services.

More detail: [data/README.md](data/README.md)

---

## How to run the prototype

From a terminal, in the `ethimatch` folder:

```powershell
cd ethimatch
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The first run may download the Hugging Face NER model (`d4data/biomedical-ner-all`). That can take a few minutes on CPU.

To re-run the saved-style evaluation:

```powershell
cd ethimatch
.\venv\Scripts\python.exe evaluation.py
```

Saved numbers are under `ethimatch/results/`.

---

## Where to look in the code

| What | File |
|------|------|
| App entry | `ethimatch/app.py` |
| Pipeline | `ethimatch/ethimatch_pipeline.py` |
| NER | `ethimatch/neural_extractor.py` |
| Rules | `ethimatch/symbolic_validator.py` |
| Evaluation | `ethimatch/evaluation.py` |
| Trial protocols | `ethimatch/trials/` |
| Synthea / MIMIC loaders | `ethimatch/data_access/` |

---

## Folder layout

```
EthiMatch/
├── ethimatch/          Python application
├── data/synthea/       Synthea CSVs I used (core files)
├── data/mimic/         MIMIC-IV Demo tables
├── docs/               Figures, examiner Q&A
├── tools/doc_builder/  Scripts used while writing the report
└── README.md
```

---

## Disclaimer

EthiMatch is for this MSc assessment only. Please do not use it for real patient care or trial enrolment.
