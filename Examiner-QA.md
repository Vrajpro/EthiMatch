# EthiMatch — Examiner Q&A

**Student:** Vraj Dipakkumar Parekh (16485659)  
**Module:** 7005SCN Individual Research Project  
**Repository:** https://github.com/Vrajpro/EthiMatch  

Because this module is assessed by report only, I prepared this note so an examiner can find direct answers after reading the PDF and opening the repository. EthiMatch is a **research prototype** — it is not intended for real patient care or enrolment decisions.

---

## 1. What did I build?

I built EthiMatch, an end-to-end neuro-symbolic clinical-trial matching system with four main parts:

1. A **neural extraction layer** (biomedical NER, regex, and negation handling) that reads clinical notes  
2. A **symbolic validation layer** with deterministic JSON protocol rules that return ELIGIBLE, INELIGIBLE, or INCONCLUSIVE  
3. An **explainability layer** that produces audit narratives and rule-level outcomes for review  
4. A **Streamlit interface** with Dashboard, Patient Matching, Cohort Discovery, and Evaluation pages  

In the report, Chapter 4 and the architecture figures and screenshots show how this fits together. In the repository, the main entry points are `ethimatch/app.py`, `ethimatch_pipeline.py`, `neural_extractor.py`, and `symbolic_validator.py`.

---

## 2. What do I mean by “neuro-symbolic” here?

I deliberately separated **reading the note** from **applying the protocol**:

- The neural part extracts entities from text; those entities can be incomplete or uncertain  
- The symbolic part applies trial rules in a deterministic, inspectable way  
- When required information is missing, the system returns **INCONCLUSIVE** rather than guessing  

My research question was whether this separation improves safety and transparency compared with a purely neural approach — not whether I invented a new deep-learning architecture.

---

## 3. How did I design the baseline comparison, and is it fair?

I compared two decision paths on the **same patients** and the **same extracted entities**:

- **EthiMatch (full pipeline):** entities pass through my symbolic validator with exclusions and missing-data handling  
- **Pure-neural baseline:** an inclusion-oriented heuristic on the same entities, without the full symbolic safety layer  

Both paths use the same NER output, so the evaluation isolates the effect of the symbolic decision layer. I describe this in Chapter 3 and implement it in `ethimatch/evaluation.py`.

---

## 4. How did I create the gold standard? Could this be circular?

I derived gold labels from **structured patient fields** in the CSV/Synthea profiles (for example active conditions and demographics), validated against the same protocol rules, rather than from free-text NER output alone.

This makes the benchmark reproducible, but I accept it is weaker than independent clinician review of full clinical notes. I state that limitation clearly in Chapters 6 and 8. The gold standard reflects the protocol definition I implemented; that is why I was careful about what I claim in the results tables.

---

## 5. Why did I use Synthea and MIMIC-IV Demo?

For this MSc project I needed data I could use ethically and reproducibly:

- **Synthea** gave me a scalable synthetic cohort for controlled testing without privacy restrictions  
- **MIMIC-IV Demo** gave me a public structured dataset as an external check  

Together they support a dual-source evaluation within the time and ethics constraints of the module. I do **not** present this as equivalent to validation on live hospital records.

---

## 6. Which model did I use — BioBERT or something else?

In the running system I use **`d4data/biomedical-ner-all`** (a DistilBERT-style biomedical NER model via Hugging Face). I chose it because it runs on CPU hardware available to me during development.

In the literature review I discuss BioBERT (Lee et al., 2020) as the research background for biomedical language models. I was careful in the report not to imply that BioBERT itself is the deployed checkpoint.

---

## 7. What are the main results an examiner should look at?

My primary synthetic benchmark (`n = 100`, six trials) is saved in `ethimatch/results/comparative_benchmark.json` and reported in the Abstract and Chapter 6:

| Metric | EthiMatch | Pure-neural baseline |
|--------|-----------|----------------------|
| F1 | 65.5% | 56.2% |
| Precision | 64.5% | 48.7% |
| FPR | 0.6% | 2.4% |
| McNemar p | ≈ 0.067 (not significant at α = 0.05) | |

The result I trust most is the **reduction in false positive rate**, together with improved F1 and precision on the main synthetic run. I treat FPR as the main safety-related signal in this project.

---

## 8. McNemar was not significant — what am I allowed to claim?

I report this honestly:

- Discordant pairs favoured EthiMatch (14 vs 5)  
- The p-value (≈ 0.067) did **not** reach α = 0.05  
- I therefore describe a **directional improvement**, not statistical proof at conventional significance  

I do not claim that McNemar confirms superiority at the 5% level. That position is reflected in the Abstract, Chapter 6, and Tables 5 and 7 in the report.

---

## 9. MIMIC results look weak — does that weaken the whole project?

I do not think it invalidates the work, but it **limits generalisation**.

MIMIC-IV Demo is small and not rich in oncology eligibility cases for my trial set, so absolute F1 stays modest. I still use it as a stress test: even there, the pattern of lower false positives relative to the baseline is visible. In the report I treat MIMIC as supporting evidence, not as the primary claim.

---

## 10. What is my contribution at MSc level?

I am not claiming to have built the first trial-matching system in the literature. My contribution is a **complete, reproducible prototype** that brings together:

- one patient-profile contract for Synthea and MIMIC-IV Demo  
- JSON-defined trial protocols with explicit INCONCLUSIVE handling  
- paired comparison against a pure-neural baseline on identical inputs  
- a clinician-facing audit UI, evidenced in the report by screenshots for PDF-only assessment  

The GitHub repository is part of that contribution so an examiner can inspect the implementation without a live demo.

---

## 11. How can an examiner verify my numbers without running the app?

An examiner can:

1. Open `ethimatch/results/comparative_benchmark.json` in the repository  
2. Compare those values with the Abstract, Table 1, and Chapter 6  
3. Check cross-source summaries in Table 3 and the files under `ethimatch/results/thesis/`  
4. Cross-check the UI screenshots in Chapter 4 (Figures 6–9) against the described workflows  

I designed the evaluation outputs to be inspectable so the report stands on its own.

---

## 12. How can someone run my system from GitHub?

From the repository root:

```powershell
cd ethimatch
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Further setup notes are in the main `README.md`. A few very large Synthea CSV files are not on GitHub because of file-size limits; the core CSVs needed for the demo path are included. I explain this in `data/README.md`.

---

## 13. Where is explainability in my design?

I implemented explainability at two levels:

- **Rule level:** each protocol criterion returns PASS, FAIL, or INCONCLUSIVE in the Audit view  
- **Narrative level:** XAI text summarises why a match was suggested  

The Patient Matching page exposes Narrative, Entities, and Audit tabs (Figure 7 in the report). I also added PDF export for audit handoff. The clinician or coordinator remains the final decision-maker; the system supports review, it does not replace it.

---

## 14. What did I do for ethics and data protection?

Throughout the project I worked only with:

- Synthea synthetic data  
- the public MIMIC-IV Demo subset  
- no identifiable real patient records  

I did not send patient note content to external generative AI services for processing. The amber AI usage declaration in the report describes how I used AI tools for drafting support only. Clinical deployment and regulatory approval were outside the scope I set for this dissertation.

---

## 15. What I explicitly do **not** claim

I want to be clear that I am **not** claiming:

- readiness for real clinical deployment or regulatory use  
- that EthiMatch should replace clinician judgement on enrolment  
- statistical significance for McNemar at α = 0.05 on the main synthetic paired comparison  
- validation on a large multi-site clinician-labelled free-text gold standard  

These boundaries are summarised in Tables 5 and 7 of the report.

---

## 16. If the app does not run first time — what I would check

These are the checks I used during development:

1. Python 3.11 and a virtual environment with `ethimatch/requirements.txt`  
2. Running commands from the `ethimatch/` folder so imports resolve  
3. Allowing time for the first Hugging Face model download on CPU  
4. Using the Evaluation page with cached synthetic results to confirm the reported benchmark numbers quickly  

---

## Quick reference (how I would answer in a viva)

| Question | How I would answer |
|----------|-------------------|
| What is novel? | A reproducible neuro-symbolic prototype with INCONCLUSIVE semantics, JSON protocols, paired evaluation, and an audit UI — all documented in the report and repo. |
| Why a symbolic layer? | To reduce unsafe false positives and make protocol logic explicit and reviewable. |
| Why not clinically ready? | Synthetic/demo data, limited protocols, structured gold labels, and McNemar not significant at 0.05. |
| Main finding? | Lower FPR and better F1/precision on my main synthetic benchmark versus the pure-neural baseline. |
| Where is the evidence? | Report Chapters 4–6, `results/comparative_benchmark.json`, and the UI screenshots. |

---

If anything in the report is unclear, I hope this file and the repository together give enough context for PDF-only examination. I am happy to clarify further through the normal module channels if required.
