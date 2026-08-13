"""Chapter 1 section content for full report."""
from __future__ import annotations

CHAPTER_1_SECTIONS = [
    ("1.1 Background and Context", (
        "Clinical trials remain essential for evaluating new cancer treatments, yet "
        "recruiting enough eligible patients is still one of the hardest problems in "
        "oncology research. Coordinators must read long electronic health records, "
        "interpret unstructured notes, and compare each patient against detailed "
        "inclusion and exclusion rules. Carlisle et al. (2015) studied 2,579 phase 2 "
        "and 3 trials closed in 2011 and found that nearly one in five either stopped "
        "early because of poor accrual or finished below 85% of planned enrolment. "
        "Automated patient–trial matching is therefore attractive if it can widen "
        "screening without creating unsafe recommendations."
        "\n\n"
        "Biomedical NLP now makes it realistic to extract clinical facts from free "
        "text (Lee et al., 2020). The difficulty is safety: a neural model can miss "
        "negation, skip a required field, or look confident when evidence is incomplete. "
        "Adoption depends on transparency and a conservative response to missing "
        "information (Zitianellis, 2025)."
    )),
    ("1.2 Problem Statement", (
        "The practical problem is how to automate matching without trading speed for "
        "unsafe recommendations. Purely neural systems can read notes but cannot "
        "guarantee every protocol rule was applied. Purely rule-based systems can "
        "enforce criteria but struggle with narrative text. Loaiza-Bonilla et al. "
        "(2026) show neuro-symbolic designs improve matching safety at scale, yet "
        "open academic prototypes with explicit INCONCLUSIVE handling and paired "
        "evaluation remain uncommon. EthiMatch was built to close that gap."
    )),
    ("1.3 Research Question, Aim and Objectives", (
        "Research question: Can a neuro-symbolic architecture that pairs a biomedical "
        "text-reading model with a deterministic symbolic rule engine improve the "
        "safety and explainability of clinical-trial matching compared with a purely "
        "neural approach?"
        "\n\n"
        "Aim: To design, implement, and evaluate EthiMatch—an end-to-end research "
        "prototype that extracts eligibility features, validates them against JSON "
        "trial protocols, and presents an auditable explanation in a dashboard."
        "\n\n"
        "Objectives: (1) design a five-stage neuro-symbolic pipeline; (2) ingest "
        "Synthea (Walonoski et al., 2018) and MIMIC-IV Demo (Johnson et al., 2023) "
        "through one patient-profile contract; (3) implement biomedical NER with "
        "JSON rule validation and INCONCLUSIVE outcomes; (4) deliver a Streamlit "
        "dashboard for matching, cohort discovery, and evaluation; (5) benchmark "
        "against a pure-neural baseline with the extractor held constant using "
        "precision, recall, F1, FPR, and McNemar's test (McNemar, 1947); (6) "
        "reflect on ethical and professional constraints of a non-clinical prototype."
    )),
    ("1.4 Significance and Contribution", (
        "For coordinators, EthiMatch offers a safer pre-screen: fewer false positives "
        "and clearer reasons. Academically, it provides an open neuro-symbolic "
        "prototype with dual-dataset evaluation and a paired comparison that isolates "
        "the symbolic layer. Because assessment is PDF-only, Chapter 4 includes "
        "design diagrams and live UI screenshots so examiners can judge the artefact "
        "without a demonstration."
    )),
    ("1.5 Scope and Delimitations", (
        "In scope: Python prototype; JSON oncology protocols; Synthea and MIMIC-IV "
        "Demo evaluation; comparative benchmarking; explainable audit reporting. "
        "Out of scope: live EHR integration, medical-device approval, and real "
        "enrolment decisions. The vocabulary is limited to a defined oncology subset."
    )),
    ("1.6 Structure of the Report", (
        "Chapter 2 reviews literature and theory. Chapter 3 explains methodology. "
        "Chapter 4 presents the artefact with diagrams and UI screenshots. Chapter 5 "
        "covers project management. Chapter 6 evaluates performance. Chapter 7 "
        "addresses ethics. Chapter 8 concludes."
    )),
]
