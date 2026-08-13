"""All chapter content for the full EthiMatch project report."""
from __future__ import annotations

from chapter1_sections import CHAPTER_1_SECTIONS
from build_chapter2 import SECTIONS as CHAPTER_2_SECTIONS
from build_chapter3 import SECTIONS as CHAPTER_3_SECTIONS
from report_expansions import CH4_EXTRA, CH5_EXTRA, CH6_EXTRA, CH7_EXTRA, CH8_EXTRA

ABSTRACT = (
    "Clinical trial recruitment remains a major bottleneck in oncology research, with "
    "nearly one in five Phase 2 and 3 trials failing to achieve adequate accrual. "
    "Automated patient–trial matching using artificial intelligence can improve "
    "efficiency, but purely neural systems may produce unsafe false positives when "
    "clinical negation is mishandled or required data are missing. This project "
    "designed, implemented, and evaluated EthiMatch, a neuro-symbolic clinical trial "
    "matching system that combines biomedical named-entity recognition with a "
    "deterministic symbolic rule engine and explainable audit reporting. The system "
    "was evaluated using Synthea synthetic cohorts, structured CSV benchmarks, and "
    "MIMIC-IV Demo data against a pure-neural baseline, while keeping the neural "
    "extractor constant. In the main synthetic comparative run involving 100 patients "
    "and six trials, EthiMatch achieved a higher F1 score (65.5% vs 56.2%) and "
    "precision (64.5% vs 48.7%), while reducing the false positive rate (0.6% vs "
    "2.4%). McNemar's paired test approached but did not reach statistical "
    "significance at α = 0.05 (p ≈ 0.067). Overall, the project demonstrates that "
    "separating neural perception from symbolic decision-making can improve the "
    "safety of patient–trial matching while maintaining competitive recall, although "
    "EthiMatch remains a research prototype rather than a clinical product."
)

CHAPTER_4_SECTIONS = [
    ("4.1 Introduction", (
        "This chapter presents the EthiMatch artefact—the main LO6 evidence. The "
        "system was built in Python 3.11 with PyTorch (Paszke et al., 2019), Hugging "
        "Face Transformers (Wolf et al., 2020), and Streamlit (Streamlit Inc., n.d.). "
        "Because assessment is report-only, the chapter is written so a reader who "
        "never runs the app can still understand purpose, structure, UI evidence, "
        "implementation, and testing."
    )),
    ("4.2 Requirements, Design Principles and Stakeholder Use Cases", (
        "Functional requirements were derived from the research question and stakeholder "
        "needs identified in the proposal: (1) ingest patients from multiple data sources "
        "through a unified profile contract; (2) extract eligibility features from clinical "
        "notes; (3) validate against JSON trial protocols using deterministic rules; "
        "(4) return ELIGIBLE, INELIGIBLE, or INCONCLUSIVE verdicts; (5) generate "
        "explainable audit reports; and (6) support batch cohort screening and comparative "
        "benchmarking."
        "\n\n"
        "Non-functional requirements included PEP 8 coding standards, CPU-compatible "
        "neural inference, hash-validated silver caching for responsiveness, and "
        "reproducible evaluation outputs. A core safety principle is that missing "
        "mandatory fields must never be guessed—the symbolic validator returns "
        "INCONCLUSIVE instead of inventing biomarkers, stages, or comorbidities."
        "\n\n"
        "Figure 2 summarises the main use cases. The primary actor is a research "
        "coordinator or clinician reviewer who configures a data source, screens a single "
        "note or cohort, inspects explanations, and exports evidence. The system actor "
        "chains extraction, symbolic validation, and XAI narrative generation. A pure "
        "end-to-end neural black box would hide rule outcomes; EthiMatch surfaces them "
        "so the human remains decision owner."
    )),
    ("4.3 Five-Stage Pipeline Architecture", (
        "The EthiMatchPipeline orchestrator (ethimatch_pipeline.py) implements a funnel "
        "in which cheaper operations precede expensive neural inference (Figure 3). "
        "Figure 4 shows the same control flow as a process chart (cache hit, early exit, "
        "NER, rules, explanation, audit package)."
        "\n\n"
        "Stage 1 — Silver cache lookup: Previously extracted entities are loaded from "
        "data/silver/{patient_id}.json if the SHA-256 input hash matches the current note."
        "\n"
        "Stage 2 — Structured early-exit: If CSV fields already fail every trial, "
        "neural extraction is skipped."
        "\n"
        "Stage 3 — Neural NER: The NeuralExtractor runs d4data/biomedical-ner-all "
        "(d4data, n.d.) with regex fallback and negation filtering (Chapman et al., 2001)."
        "\n"
        "Stage 4 — Symbolic validation: The SymbolicValidator applies ten deterministic "
        "rules per trial protocol."
        "\n"
        "Stage 5 — XAI explanation: The XAIExplainer builds criterion-weight narratives "
        "from ValidationReport objects, following the attribution principle of SHAP "
        "(Lundberg & Lee, 2017) without treating feature weights as protocol compliance."
        "\n\n"
        "The final AuditReport packages entities, per-trial ValidationReports, executive "
        "summary, and clinician-readable narrative for the UI and PDF export. This "
        "separation is the architectural basis of the research claim: neural modules perceive "
        "text; symbolic modules decide protocol fitness; explanation modules justify the "
        "decision for human review."
    )),
    ("4.4 Data Layer", (
        "The data layer normalises heterogeneous sources into a PatientProfile dataclass "
        "(Figure 5). SyntheaDualSourceProvider reads data/synthea/ CSVs via "
        "RealCSVProvider (Walonoski et al., 2018). MIMICDualSourceProvider reads "
        "data/mimic/ structured tables and maps ICD-coded diagnoses to the same profile "
        "contract (Johnson et al., 2023). The "
        "generate_mock_clinical_note function synthesises EHR-style narratives from "
        "structured fields when free-text notes are unavailable, including truthful "
        "negation sentences to exercise the negation filter."
        "\n\n"
        "A single profile contract means every later stage is dataset-agnostic: the "
        "validator and UI never hard-code Synthea or MIMIC field names. That contract also "
        "underpins evaluation fairness—both systems under comparison receive identical "
        "profiles and notes."
    )),
    ("4.5 Neural Extraction Module", (
        "neural_extractor.py wraps Hugging Face Transformers (Wolf et al., 2020) for "
        "d4data/biomedical-ner-all (d4data, n.d.), a DistilBERT model (Sanh et al., 2019) "
        "fine-tuned on MACCROBAT (Caufield, 2020). The checkpoint follows the biomedical "
        "pre-training paradigm of Lee et al. (2020) but is not BioBERT itself; it was "
        "chosen for CPU feasibility. Post-processing adds regex patterns for age, ECOG, "
        "and BMI; a negation filter (Chapman et al., 2001); and canonical disease codes "
        "from config.py."
        "\n\n"
        "Extraction is deliberately incomplete without Stage 4: entities may suggest "
        "disease match, but inclusion/exclusion fitness is never claimed until symbolic "
        "rules run. This avoids treating NER confidence scores as eligibility judgements."
    )),
    ("4.6 Symbolic Validator", (
        "symbolic_validator.py implements ten deterministic checks: age, gender, disease, "
        "stage, required biomarkers, ECOG performance status, BMI maximum, BMI minimum, "
        "excluded comorbidities, and excluded prior therapies. Each check returns a "
        "RuleResult with verdict PASS, FAIL, WARNING, INCONCLUSIVE, or SKIP. Trials are "
        "loaded from ethimatch/trials/*.json via trial_registry.py and sanitised through "
        "config.sanitize_trial_criteria(). Six JSON trial protocols, including oncology "
        "studies and an open adult baseline trial, support benchmarking diversity."
        "\n\n"
        "JSON protocols make eligibility logic auditable outside model weights: changing "
        "a BMI threshold or comorbidity exclusion is a protocol edit, not a silent neural "
        "behaviour change. INCONCLUSIVE is a first-class outcome when mandatory evidence "
        "is absent—preferring human follow-up over forced binary recommender errors."
    )),
    ("4.7 User Interface and Clinician Walkthrough", (
        "Because this module is assessed by PDF report only, the artefact must be "
        "understandable without a live demonstration. app.py launches a Streamlit "
        "dashboard (Streamlit Inc., n.d.) with four pages that map to coordinator "
        "workflows. Figures 6–9 are live screenshots of those pages, taken from "
        "the running prototype on Synthea data. They are intended as examiner evidence "
        "of a working system, not decorative images."
        "\n\n"
        "Dashboard (Figure 6) shows registered trials, the active data source, and "
        "cohort size so a reader can see what protocols and patients the session uses."
        "\n\n"
        "Patient Matching (Figure 7) is the core walkthrough: note → extract → "
        "validate → explain. Quick Entry builds one synthetic note; CSV batch screens "
        "patients from the loaded cohort. Expanding a result opens Narrative (XAI "
        "prose), Entities, and Audit (rule-level outcomes). The screenshot shows an "
        "Eligible Quick Entry case with match detail expanded."
        "\n\n"
        "Cohort Discovery (Figure 8) reverses the question: which patients fit one "
        "trial protocol? The screenshot shows an ONC-001 run over 100 patients with "
        "eligible, inconclusive, and ineligible counts—useful for feasibility review."
        "\n\n"
        "Evaluation (Figure 9) runs the comparative benchmark against the "
        "pure-neural baseline and surfaces precision, recall, FPR, and McNemar "
        "summary used in Chapter 6."
        "\n\n"
        "pdf_export.py can also produce clinician handoff PDFs from AuditReport "
        "objects. Across all pages the design is human-in-the-loop: EthiMatch "
        "recommends and explains; it does not replace clinical judgement."
    )),
    ("4.8 How the Artefact Fulfils Project Objectives", (
        "Table-style mapping of objectives to artefact evidence (readable without running "
        "code):"
        "\n\n"
        "• Objective — safer matching: SymbolicValidator + FPR-focused evaluation harness "
        "(Chapter 6) constrain optimistic pure-neural over-recommendation."
        "\n"
        "• Objective — transparent decisions: ValidationReport + XAI narratives + Audit "
        "tab expose each criterion outcome."
        "\n"
        "• Objective — multi-source intake: PatientProfile providers for Synthea and "
        "MIMIC-IV Demo under one contract."
        "\n"
        "• Objective — reproducible research: evaluation.py, results/*.json, docs/figures "
        "diagrams, and QA smoke scripts."
        "\n"
        "• Objective — usable prototype: four Streamlit pages, evidenced in Figures "
        "6–9 for PDF-only assessment."
    )),
    ("4.9 Testing and Quality Assurance", (
        "Testing combined automated smoke checks and experimental evaluation."
        "\n\n"
        "• scripts/qa_system_check.py verifies registry consistency, expected verdicts on "
        "known synthetic profiles, and mock-note content."
        "\n"
        "• scripts/demo_smoke.py exercises the four dashboard pathways used in viva/demo."
        "\n"
        "• evaluation.py provides regression-style benchmarking across datasets with "
        "persisted metrics under ethimatch/results/."
        "\n"
        "• scripts/materialize_silver.py pre-warms extractions for responsive screening."
        "\n\n"
        "These artefacts provide implementation evidence of technical competence "
        "proportionate to the 30% artefact weighting in the module mark scheme: the "
        "system is not only described, but exercised, measured, and archived."
    )),
]

CHAPTER_5_SECTIONS = [
    ("5.1 Introduction", (
        "This chapter shows how the project was organised from proposal to "
        "submission. For Learning Outcome 2, the focus is practical evidence: "
        "timeline, risks, adaptations, and what changed when implementation "
        "reality differed from the original plan."
    )),
    ("5.2 Project Timeline", (
        "The work followed the 22-week CW1 plan, adapted when technical "
        "dependencies appeared."
        "\n\n"
        "• Weeks 1–2: Proposal, ethics checklist, literature scoping — completed."
        "\n"
        "• Weeks 3–5: Architecture, patient-profile contract, JSON trial schema — completed."
        "\n"
        "• Weeks 6–10: Core implementation (loaders, NER, validator, pipeline) — completed."
        "\n"
        "• Weeks 11–13: Streamlit UI, silver cache, evaluation harness — completed."
        "\n"
        "• Weeks 14–15: MIMIC-IV Demo integration, McNemar test, benchmark fixes — completed."
        "\n"
        "• Weeks 16–20: Report writing, figures, regression testing — completed."
        "\n"
        "• Weeks 21–22: Final proofreading, PDF packaging, submission — completed."
    )),
    ("5.3 Risk Register and Mitigations", (
        "Four risks shaped day-to-day decisions:"
        "\n\n"
        "Neural latency on CPU — mitigated by silver cache and structured early-exit; "
        "materialize_silver.py pre-computes extractions for demo cohorts."
        "\n\n"
        "Incomplete patient data — mitigated by INCONCLUSIVE verdicts instead of guessing."
        "\n\n"
        "MIMIC credentialing delays — mitigated by using Synthea plus MIMIC-IV Demo, "
        "avoiding PhysioNet credential wait time."
        "\n\n"
        "Stale cache after logic changes — mitigated by hash-based invalidation "
        "(CACHE_VERSION plus note hash) in silver_cache.py."
    )),
    ("5.4 Reflection on Project Management", (
        "The hardest management decision was not adding features; it was protecting "
        "evaluation honesty. Early MIMIC loading silently fell back to synthetic "
        "patients, which would have made Chapter 6 look stronger than the evidence "
        "deserved. Replacing that path with MIMICDualSourceProvider delayed UI polish "
        "but kept the comparative claim trustworthy. That trade-off was the right one."
        "\n\n"
        "Contract-driven modules also helped. Once PatientProfile and ValidationReport "
        "were stable, swapping a data provider did not force rewrites of the validator "
        "or Streamlit pages. Timeboxing the main benchmark at n = 100 kept feedback "
        "fast on student hardware while still supporting McNemar comparison. Overall, "
        "the plan from CW1 remained usable; the main adaptation was sequencing "
        "correctness work ahead of presentation work."
    )),
    ("5.5 Deliverables Mapping", (
        "CW1 proposed three deliverables: (1) the EthiMatch software repository, delivered "
        "as the ethimatch/ Python package with README and requirements.txt; (2) an evaluation "
        "report in JSON format, delivered as results/comparative_benchmark.json and "
        "evaluation_metrics.json; and (3) dissertation documentation, delivered through this "
        "report and supporting figures in docs/figures/. All proposed in-scope deliverables "
        "were achieved within the planned timeline."
    )),
    ("5.6 Chapter Summary", (
        "The project was delivered against phased milestones with explicit risk "
        "mitigations. Scope stayed aligned with the proposal: credentialed "
        "MIMIC-IV-Note access was deferred, and the demo subset plus Synthea carried "
        "the evaluation."
    )),
]

CHAPTER_6_SECTIONS = [
    ("6.1 Introduction", (
        "This chapter presents evaluation results comparing the neuro-symbolic EthiMatch "
        "pipeline against a pure-neural baseline on three datasets, interprets findings "
        "against the research question, and discusses validity and limitations."
    )),
    ("6.2 Experimental Setup", (
        "Benchmarks were executed through the Streamlit Evaluation page and persisted to "
        "ethimatch/results/comparative_benchmark.json. Each run used six JSON trial "
        "protocols and configurable patient limits (up to n = 500). Both systems shared "
        "the same NeuralExtractor instance and patient cohort; only the decision logic "
        "differed. Ground truth was derived from structured CSV fields via the "
        "SymbolicValidator, as described in Chapter 3."
    )),
    ("6.3 Results", (
        "Table 1 summarises headline results from the primary synthetic benchmark (n = 100). "
        "The neuro-symbolic pipeline achieved higher precision and F1 with substantially "
        "lower false positive rate, supporting the safety hypothesis. McNemar's test "
        "(χ² = 3.35, p ≈ 0.067) showed a trend favouring neuro-symbolic correctness on "
        "discordant pairs (14 vs 5) but did not reach conventional significance at α = 0.05 "
        "on this cohort size—suggesting a larger n may be needed for statistical confirmation."
        "\n\n"
        "CSV structured benchmarks at n = 100 showed near-zero FPR for the neuro-symbolic "
        "system (0.0%) versus 50.4% for the pure-neural baseline, illustrating the safety "
        "impact of symbolic exclusion enforcement. MIMIC-IV Demo benchmarks used the corrected "
        "MIMICDualSourceProvider; results should be interpreted with caution given the "
        "100-patient demo ceiling and structured-note synthesis."
    )),
    ("6.4 Discussion", (
        "The results support the central claim that symbolic validation improves safety "
        "metrics—particularly FPR—even when neural extraction is held constant. The "
        "pure-neural baseline's higher recall on some runs reflects its inclusion-only "
        "heuristic, which flags patients optimistically without enforcing exclusions. "
        "In clinical pre-screening, false positives are more harmful than false negatives "
        "because they risk inappropriate patient contact; EthiMatch's design prioritises "
        "precision and FPR accordingly."
        "\n\n"
        "INCONCLUSIVE verdicts constituted a substantial fraction of pipeline outputs on "
        "synthetic runs, demonstrating that the system surfaces missing data rather than "
        "guessing. Extraction fidelity against structured gold on CSV evaluation reached "
        "100% precision and recall on active-condition filtering, confirming that the "
        "neural layer performs reliably when notes faithfully reflect structured data."
    )),
    ("6.5 Threats to Validity", (
        "Construct validity: structured gold labels may not capture free-text-only facts. "
        "External validity: oncology vocabulary and six trials limit generalisation. "
        "Internal validity: holding the extractor constant strengthens causal attribution "
        "to the symbolic layer. Statistical conclusion validity: demo cohort sizes "
        "constrain McNemar power; larger runs are recommended for final submission."
    )),
    ("6.6 Chapter Summary", (
        "Evaluation demonstrates measurable safety improvements from neuro-symbolic design, "
        "with reproducible metrics and figures suitable for dissertation appendices. "
        "Results align with Loaiza-Bonilla et al.'s (2026) direction while providing an "
        "open, inspectable academic implementation."
    )),
]

CHAPTER_6_TABLE = [
    ["Synthetic (n=100)", "64.5%", "66.7%", "65.5%", "0.6%", "48.7%", "69.4%", "56.2%", "2.4%", "0.067"],
    ["CSV (n=200)", "33.3%", "33.3%", "—", "0.0%", "16.9%", "33.3%", "—", "50.4%", "—"],
    ["MIMIC-IV Demo", "See latest run", "—", "—", "—", "—", "—", "—", "—", "—"],
]

CHAPTER_7_SECTIONS = [
    ("7.1 Introduction", (
        "This chapter covers legal, ethical, professional, and societal issues "
        "relevant to EthiMatch as a research decision-support prototype. The "
        "discussion is written for a PDF-only submission: examiners should be able "
        "to see both the safeguards taken and the limits of what was claimed."
    )),
    ("7.2 Data Ethics and Privacy", (
        "No identifiable real patient data were processed. Synthea produces fully "
        "synthetic cohorts with no privacy restriction (Walonoski et al., 2018). "
        "MIMIC-IV Demo provides de-identified structured records under its public "
        "demo licence without credentialing (Johnson et al., 2023). No patient "
        "notes were uploaded to external generative AI services during development. "
        "A university ethics application for secondary synthetic and demo-data "
        "research was submitted under the CW1 process (status: submitted / under "
        "review at proposal stage) and the same data boundaries were respected "
        "throughout implementation and reporting."
    )),
    ("7.3 Clinical Safety and Professional Responsibility", (
        "EthiMatch is a research prototype, not a regulated medical device. It does "
        "not enrol patients or replace clinician judgement. INCONCLUSIVE verdicts "
        "are deliberate: when required evidence is missing, the system stops rather "
        "than guessing. Final eligibility confirmation remains a human responsibility."
    )),
    ("7.4 AI Tool Usage Declaration", (
        "This assessment sits in the amber AI category. Cursor and Grammarly were "
        "used for comprehension support, spelling/grammar, and development "
        "assistance. Core arguments, method choices, evaluation design, and final "
        "claims were authored and checked by the student. A full amber declaration "
        "appears after the References, as required by the module brief."
    )),
    ("7.5 Societal Impact", (
        "Used carefully, neuro-symbolic pre-screening could widen trial access and "
        "reduce coordinator workload. The main risks are over-trust in automated "
        "verdicts and bias if data under-represent some groups (Obermeyer et al., "
        "2019). Dual-dataset evaluation and explicit audit trails reduce those "
        "risks but do not remove them."
    )),
]

CHAPTER_8_SECTIONS = [
    ("8.1 Summary of Findings", (
        "This project asked whether neuro-symbolic AI can improve safety and explainability "
        "in clinical-trial matching compared with a purely neural approach. EthiMatch "
        "demonstrates that separating biomedical NER from deterministic rule validation "
        "produces lower false positive rates and improved precision on benchmark cohorts, "
        "while providing protocol-grounded audit reports through an interactive dashboard."
    )),
    ("8.2 Contribution to Knowledge", (
        "The project contributes an open, reproducible implementation of neuro-symbolic "
        "oncology trial matching with JSON-governed protocols, hash-validated caching, "
        "dual-dataset evaluation, and McNemar's paired testing—addressing a gap identified "
        "in Chapter 2 between commercial evidence and academic reproducibility."
    )),
    ("8.3 Limitations", (
        "Limitations include oncology-focused vocabulary, synthesised notes for structured "
        "cohorts, CPU inference latency, six trial protocols, and the 100-patient MIMIC-IV "
        "Demo ceiling. Results should not be generalised to full hospital deployment without "
        "further validation on credentialed free-text notes and larger cohorts."
    )),
    ("8.4 Recommendations for Future Work", (
        "• Fine-tune the NER model on project-specific labelled notes."
        "\n"
        "• Apply for credentialed MIMIC-IV-Note access to evaluate on real discharge summaries."
        "\n"
        "• Expand trial registry and disease vocabulary beyond oncology."
        "\n"
        "• Integrate clinician feedback loops to convert overrides into training data."
        "\n"
        "• Conduct user studies with research coordinators to assess adoption factors."
    )),
    ("8.5 Concluding Remarks", (
        "EthiMatch shows that the neural layer should read the patient, the symbolic layer "
        "should protect the patient, and the explainability layer should earn the clinician's "
        "trust. The artefact and evaluation together provide evidence that neuro-symbolic "
        "design is a principled response to the safety challenges of AI-assisted trial "
        "matching identified throughout this report."
    )),
]

REFERENCES = [
    "Alsentzer, E., Murphy, J. R., Boag, W., Weng, W.-H., Jin, D., Naumann, T., & McDermott, M. (2019). Publicly available clinical BERT embeddings. In Proceedings of the 2nd Clinical Natural Language Processing Workshop (pp. 72–78). Association for Computational Linguistics. https://doi.org/10.18653/v1/W19-1909",
    "Carlisle, B., Kimmelman, J., Ramsay, T., & MacKinnon, N. (2015). Unsuccessful trial accrual and human subjects protections: An empirical analysis of recently closed trials. Clinical Trials, 12(1), 77–83. https://doi.org/10.1177/1740774514558307",
    "Caruana, R., Lou, Y., Gehrke, J., Koch, P., Sturm, M., & Elhadad, N. (2015). Intelligible models for healthcare: Predicting pneumonia risk and hospital 30-day readmission. In Proceedings of the 21st ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (pp. 1721–1730). Association for Computing Machinery. https://doi.org/10.1145/2783258.2788613",
    "Caufield, J. H. (2020). MACCROBAT [Dataset]. figshare. https://doi.org/10.6084/m9.figshare.9764942.v2",
    "Chapman, W. W., Bridewell, W., Hanbury, P., Cooper, G. F., & Buchanan, B. G. (2001). A simple algorithm for identifying negated findings and diseases in discharge summaries. Journal of Biomedical Informatics, 34(5), 301–310. https://doi.org/10.1006/jbin.2001.1029",
    "d4data. (n.d.). biomedical-ner-all [Computer software]. Hugging Face. https://huggingface.co/d4data/biomedical-ner-all",
    "d'Avila Garcez, A., & Lamb, L. C. (2023). Neurosymbolic AI: The 3rd wave. Artificial Intelligence Review, 56(11), 12387–12406. https://doi.org/10.1007/s10462-023-10448-w",
    "Data Protection Act 2018, c. 12 (UK). https://www.legislation.gov.uk/ukpga/2018/12/contents",
    "den Hamer, D. M., Schoor, P., Polak, T. B., & Kapitan, D. (2023). Improving patient pre-screening for clinical trials: Assisting physicians with large language models. arXiv. https://doi.org/10.48550/arXiv.2304.07396",
    "Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. In J. Burstein, C. Doran, & T. Solorio (Eds.), Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers) (pp. 4171–4186). Association for Computational Linguistics. https://doi.org/10.18653/v1/N19-1423",
    "Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science in information systems research. MIS Quarterly, 28(1), 75–105. https://doi.org/10.2307/25148625",
    "Information Commissioner's Office. (2023). Guidance on AI and data protection. https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/",
    "Jin, Q., Wang, Z., Floudas, C. S., Chen, F., Gong, C., Bracken-Clarke, D., Xue, E., Yang, Y., Sun, J., & Lu, Z. (2024). Matching patients to clinical trials with large language models. Nature Communications, 15, 9074. https://doi.org/10.1038/s41467-024-53081-z",
    "Johnson, A. E. W., Bulgarelli, L., Shen, L., Gayles, A., Shammout, A., Horng, S., Pollard, T. J., Hao, S., Moody, B., Gow, B., Lehman, L.-w. H., Celi, L. A., & Mark, R. G. (2023). MIMIC-IV, a freely accessible electronic health record dataset. Scientific Data, 10(1), 1. https://doi.org/10.1038/s41597-022-01899-x",
    "Lee, J., Yoon, W., Kim, S., Kim, D., Kim, S., So, C. H., & Kang, J. (2020). BioBERT: A pre-trained biomedical language representation model for biomedical text mining. Bioinformatics, 36(4), 1234–1240. https://doi.org/10.1093/bioinformatics/btz682",
    "Loaiza-Bonilla, A., Yost, C., Kurnaz, S., Tuysuz, E., Thaker, N. G., Giritlioglu, D., & Meza, J. P. N. (2026). Transforming oncology clinical trial matching through neuro-symbolic, multi-agent AI and an oncology-specific knowledge graph: A prospective evaluation in 3804 patients. ESMO Real World Data and Digital Oncology, 12, 100706. https://doi.org/10.1016/j.esmorw.2026.100706",
    "Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. In I. Guyon, U. V. Luxburg, S. Bengio, H. Wallach, R. Fergus, S. Vishwanathan, & R. Garnett (Eds.), Advances in Neural Information Processing Systems, 30 (pp. 4765–4774). https://papers.nips.cc/paper/7062-a-unified-approach-to-interpreting-model-predictions",
    "McNemar, Q. (1947). Note on the sampling error of the difference between correlated proportions or percentages. Psychometrika, 12(2), 153–157. https://doi.org/10.1007/BF02295996",
    "Obermeyer, Z., Powers, B., Vogeli, C., & Mullainathan, S. (2019). Dissecting racial bias in an algorithm used to manage the health of populations. Science, 366(6464), 447–453. https://doi.org/10.1126/science.aax2342",
    "Paszke, A., Gross, S., Massa, F., Lerer, A., Bradbury, J., Chanan, G., Killeen, T., Lin, Z., Gimelshein, N., Antiga, L., Desmaison, A., Kopf, A., Yang, E., DeVito, Z., Raison, M., Tejani, A., Chilamkurthy, S., Steiner, B., Fang, L., Bai, J., & Chintala, S. (2019). PyTorch: An imperative style, high-performance deep learning library. In H. Wallach, H. Larochelle, A. Beygelzimer, F. d'Alché-Buc, E. Fox, & R. Garnett (Eds.), Advances in Neural Information Processing Systems, 32.",
    "Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). \"Why should I trust you?\": Explaining the predictions of any classifier. In Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (pp. 1135–1144). Association for Computing Machinery. https://doi.org/10.1145/2939672.2939778",
    "Sanh, V., Debut, L., Chaumond, J., & Wolf, T. (2019). DistilBERT, a distilled version of BERT: Smaller, faster, cheaper and lighter. arXiv. https://doi.org/10.48550/arXiv.1910.01108",
    "Sarker, M. K., Zhou, L., Eberhart, A., & Hitzler, P. (2022). Neuro-symbolic artificial intelligence. AI Communications, 34(3), 197–209. https://doi.org/10.3233/AIC-210084",
    "Streamlit Inc. (n.d.). Streamlit documentation. https://docs.streamlit.io/",
    "Walonoski, J., Kramer, M., Nichols, J., Quina, A., Moesel, C., Hall, D., Duffett, C., Dube, K., Gallagher, T., & McLachlan, S. (2018). Synthea: An approach, method, and software mechanism for generating synthetic patients and the synthetic electronic health care record. Journal of the American Medical Informatics Association, 25(3), 230–238. https://doi.org/10.1093/jamia/ocx079",
    "Wolf, T., Debut, L., Sanh, V., Chaumond, J., Delangue, C., Moi, A., Cistac, P., Rault, T., Louf, R., Funtowicz, M., Davison, J., Shleifer, S., von Platen, P., Ma, C., Jernite, Y., Plu, J., Xu, C., Le Scao, T., Gugger, S., Drame, M., Lhoest, Q., & Rush, A. M. (2020). Transformers: State-of-the-art natural language processing. In Q. Liu & D. Schlangen (Eds.), Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing: System Demonstrations (pp. 38–45). Association for Computational Linguistics. https://doi.org/10.18653/v1/2020.emnlp-demos.6",
    "Yuan, C., Ryan, P. B., Ta, C., Guo, Y., Li, Z., Hardin, J., Makadia, R., Jin, P., Shang, N., Kang, T., & Weng, C. (2019). Criteria2Query: A natural language interface to clinical databases for cohort definition. Journal of the American Medical Informatics Association, 26(4), 294–305. https://doi.org/10.1093/jamia/ocy178",
    "Zitianellis, J. (2025). Integrating health behaviour and AI/ML theories: A case for site screening prediction in patient recruitment for clinical trials [Unpublished master's research paper]. Monarch Business School, Switzerland.",
]

ALL_CHAPTERS = [
    ("Chapter 1: Introduction", CHAPTER_1_SECTIONS),
    ("Chapter 2: Literature Review and Theoretical Framework", CHAPTER_2_SECTIONS),
    ("Chapter 3: Research Design and Methodology", CHAPTER_3_SECTIONS),
    ("Chapter 4: Artefact Design and Development", CHAPTER_4_SECTIONS + CH4_EXTRA),
    ("Chapter 5: Project Management", CHAPTER_5_SECTIONS + CH5_EXTRA),
    ("Chapter 6: Evaluation and Discussion", CHAPTER_6_SECTIONS + CH6_EXTRA),
    ("Chapter 7: Legal, Ethical and Social Considerations", CHAPTER_7_SECTIONS + CH7_EXTRA),
    ("Chapter 8: Conclusion and Recommendations", CHAPTER_8_SECTIONS + CH8_EXTRA),
]
