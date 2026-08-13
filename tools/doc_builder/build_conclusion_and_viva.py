"""Build EthiMatch Conclusion chapter + viva demo rehearsal script."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "doc_builder"))

from report_styles import (  # noqa: E402
    add_bullet,
    add_chapter_heading,
    add_para,
    add_section_heading,
    add_table,
    setup_document,
)

RESULTS = ROOT / "ethimatch" / "results"
OUT_CONCLUSION = ROOT / "docs" / "reports" / "EthiMatch_Conclusion_Chapter.docx"
OUT_VIVA = ROOT / "docs" / "reports" / "EthiMatch_Viva_Demo_Script.docx"


def _pct(x: float) -> str:
    return f"{100 * float(x):.1f}%"


def build_conclusion() -> None:
    comparative = json.loads(
        (RESULTS / "comparative_benchmark.json").read_text(encoding="utf-8")
    )
    synth = comparative["comparative"]["synthetic"]
    ns = synth["neuro_symbolic"]
    pn = synth["pure_neural"]
    mc = synth["mcnemar"]

    doc = setup_document()
    add_chapter_heading(doc, "Chapter 8: Conclusion and Recommendations")

    add_para(
        doc,
        "This chapter restates the research aim, summarises findings, clarifies "
        "contribution and limits, and recommends future work.",
    )

    add_section_heading(doc, "8.1 Restatement of the Research Aim and Objectives")
    add_para(
        doc,
        "The project asked whether a neuro-symbolic architecture—biomedical NER plus "
        "deterministic validation and explainable narratives—can provide safer and more "
        "transparent trial matching support than a purely neural approach. The intended "
        "user is a research coordinator who remains responsible for final decisions.",
    )
    add_para(
        doc,
        "For PDF-only assessment, objectives are closed against outcomes "
        "(methods in Chapter 3; artefact in Chapter 4; metrics in Chapter 6):",
    )
    add_table(
        doc,
        ["Objective theme", "Outcome status"],
        [
            [
                "Build neuro-symbolic matching artefact",
                "Achieved — five-stage pipeline + Streamlit UI (Ch4)",
            ],
            [
                "Compare vs pure-neural baseline",
                "Achieved — shared extractor, paired metrics (Ch6)",
            ],
            [
                "Improve safety-related behaviour (FPR)",
                "Supported — lower FPR on synthetic/CSV; McNemar not sig. at 0.05",
            ],
            [
                "Provide inspectable explanations",
                "Achieved — Audit/Narrative panels + XAI + PDF export",
            ],
            [
                "Clinical deployment readiness",
                "Out of scope / not claimed",
            ],
        ],
        caption="Table 6 — Objective–outcome closure for examiners.",
    )

    add_section_heading(doc, "8.2 Summary of Findings")
    add_para(
        doc,
        "EthiMatch is an end-to-end Streamlit prototype with Dashboard, Patient Matching, "
        "Cohort Discovery, and Evaluation views (Figures 6–9). The pipeline separates "
        "extraction, symbolic validation, explainability, and clinician review—the core "
        "claim of the project.",
    )
    add_bullet(doc, "Extraction: biomedical NER + regex (and silver-cache reuse) convert notes into structured entities.")
    add_bullet(doc, "Symbolic validation: deterministic protocol rules produce pass/fail/inconclusive verdicts.")
    add_bullet(doc, "Explainability: ValidationReport objects are translated into clinician-readable narratives.")
    add_bullet(doc, "Clinician review: interactive master–detail UI supports human-in-the-loop oversight.")

    add_para(
        doc,
        "On the main synthetic comparative benchmark "
        f"(n = {synth['n_patients']}, {synth['n_trials']} trials), EthiMatch achieved "
        f"F1 = {_pct(ns['f1'])} versus {_pct(pn['f1'])} for the pure-neural baseline "
        f"(ΔF1 ≈ {(ns['f1'] - pn['f1']) * 100:+.1f} percentage points). Precision improved "
        f"from {_pct(pn['precision'])} to {_pct(ns['precision'])}. Most importantly for "
        f"safety, false positive rate fell from {_pct(pn['fpr'])} to {_pct(ns['fpr'])}.",
    )
    add_para(
        doc,
        "McNemar's paired comparison favoured EthiMatch in discordant counts "
        f"({mc['ethimatch_correct_baseline_wrong']} vs "
        f"{mc['ethimatch_wrong_baseline_correct']}) but did not reach conventional "
        f"significance at α = 0.05 (p ≈ {mc['p_value_approx']:.3f}). This is reported "
        "honestly: the directional effect supports the design hypothesis, while stronger "
        "statistical claims require larger paired samples.",
    )
    add_para(
        doc,
        "Cross-source summaries and an ONC-001 full Synthea safety case further showed "
        "that the symbolic layer can block dangerous false positives that a pure-neural "
        "baseline may accept. Qualitative UI design supports inspectability of Narrative / "
        "Entities / Audit views; this is design evidence of explainability, not a formal "
        "clinician RCT.",
    )

    add_section_heading(doc, "8.3 Contribution to Knowledge and Practice")
    add_para(
        doc,
        "The contribution is both technical and methodological:",
    )
    add_bullet(
        doc,
        "A reproducible neuro-symbolic matching artefact with clear separation of "
        "extraction, validation, explanation, and clinician review.",
    )
    add_bullet(
        doc,
        "JSON protocol governance that makes inclusion/exclusion criteria explicit "
        "and auditable rather than buried in opaque model weights.",
    )
    add_bullet(
        doc,
        "A comparative evaluation harness reporting Precision, Recall, F1, FPR, and "
        "McNemar's paired test (McNemar, 1947) against a pure-neural baseline.",
    )
    add_bullet(
        doc,
        "A dual-source data pathway (Synthea + MIMIC-IV Demo) supporting engineering "
        "validation under ethically appropriate demo/synthetic conditions.",
    )
    add_para(
        doc,
        "Practically, the system demonstrates a feasible pattern for safer pre-screening "
        "support: the neural layer reads the note; the symbolic layer protects the patient; "
        "the explainability layer earns clinician trust.",
    )

    add_section_heading(doc, "8.4 Discussion of Strengths")
    add_bullet(
        doc,
        "Safety orientation: reduced FPR is consistently the strongest empirical signal.",
    )
    add_bullet(
        doc,
        "Transparency: rule-level audit trails and XAI narratives support accountable review.",
    )
    add_bullet(
        doc,
        "Engineering completeness: runnable demo covering matching, cohort search, and evaluation.",
    )
    add_bullet(
        doc,
        "Professional structure: UI/services/data_access separation improves maintainability "
        "and examiner inspection of the artefact.",
    )

    add_section_heading(doc, "8.5 Limitations")
    add_para(
        doc,
        "The following limitations bound the claims that can be made:",
    )
    add_bullet(
        doc,
        "Prototype status: EthiMatch is not a regulated medical device and must not be "
        "used for clinical decision-making.",
    )
    add_bullet(
        doc,
        "Data constraints: Synthea is synthetic; MIMIC-IV Demo is small and oncology-sparse; "
        "neither replaces multi-site real-world validation.",
    )
    add_bullet(
        doc,
        "Gold-standard construction: structured profile/CSV gold is reproducible but weaker "
        "than independent clinician adjudication of free-text notes.",
    )
    add_bullet(
        doc,
        "Statistical power: McNemar on the main synthetic paired run approached, but did not "
        "reach, significance at 0.05.",
    )
    add_bullet(
        doc,
        "Scope limits: oncology-focused vocabulary, limited protocol set, and CPU inference "
        "latency constrain immediate generalisation.",
    )
    add_para(
        doc,
        "Table 7 restates the claim boundary in one place so the conclusion cannot be "
        "read as a deployment recommendation.",
    )
    add_table(
        doc,
        ["Claim level", "Supported by this project?"],
        [
            ["Working research prototype / system walkthrough (Chapter 4 figures)", "Yes"],
            ["Improved F1 and precision on synthetic benchmark (n = 100)", "Yes"],
            ["Reduced false positive rate vs pure neural", "Yes"],
            ["McNemar significant at α = 0.05 (main synthetic)", "No (p ≈ 0.067)"],
            ["Ready for real clinical deployment", "No"],
        ],
        caption="Table 7 — Final claim discipline summary.",
    )

    add_section_heading(doc, "8.6 Recommendations for Future Work")
    add_bullet(
        doc,
        "Scale paired evaluation with larger cohorts and report confidence intervals alongside McNemar.",
    )
    add_bullet(
        doc,
        "Obtain credentialed free-text clinical notes (where ethically approved) for stronger external validity.",
    )
    add_bullet(
        doc,
        "Fine-tune biomedical NER on project-specific labelled notes and negation cases.",
    )
    add_bullet(
        doc,
        "Expand protocol libraries beyond the current controlled registry and broaden disease coverage.",
    )
    add_bullet(
        doc,
        "Conduct usability studies with research coordinators, including override capture as feedback data.",
    )
    add_bullet(
        doc,
        "Formalise risk management, bias assessment, and deployment governance if moving toward pilot use.",
    )

    add_section_heading(doc, "8.7 Concluding Remarks")
    add_para(
        doc,
        "EthiMatch answers its research question with a working artefact and measured "
        "evidence: neuro-symbolic design can improve the safety profile of AI-assisted "
        "trial matching relative to a pure-neural baseline, while keeping decisions "
        "inspectable for human reviewers. The strongest claim supported by the evaluation "
        "is safer behaviour through lower false positives under synthetic/demo conditions, "
        "not perfect clinical readiness and not p < 0.05 certainty. Within those bounds, "
        "the project provides a coherent contribution to responsible neuro-symbolic clinical "
        "decision-support research—and a PDF that can be understood without a presentation.",
    )

    OUT_CONCLUSION.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_CONCLUSION)
    print(f"Wrote: {OUT_CONCLUSION}")


def build_viva_script() -> None:
    doc = setup_document()
    add_chapter_heading(doc, "EthiMatch Viva / Demo Rehearsal Script (5–7 minutes)")

    add_para(
        doc,
        "Use this script exactly during practice. Keep calm, click slowly, and always "
        "state that EthiMatch is a research prototype, not for clinical use.",
    )

    add_section_heading(doc, "0. Before you start (1 minute)")
    add_bullet(doc, "Close other apps; open only EthiMatch and this script.")
    add_bullet(doc, r"Start app: cd C:\Users\91846\Desktop\EthiMatch\ethimatch then run_app.bat")
    add_bullet(doc, "Sidebar settings: Data Source = Synthea; Patients loaded = 100 (or higher).")
    add_bullet(doc, "Have Evaluation chapter / Conclusion chapter open offline as backup evidence.")

    add_section_heading(doc, "1. Opening statement (30–40 seconds)")
    add_para(
        doc,
        "Say: “EthiMatch is a neuro-symbolic clinical trial matching prototype. "
        "It extracts clinical entities from notes with BioBERT, checks them against "
        "deterministic trial rules, explains the decision, and keeps a clinician in the loop. "
        "It is a research prototype and not for clinical use.”",
        italic=True,
    )

    add_section_heading(doc, "2. Dashboard (40–50 seconds)")
    add_bullet(doc, "Open Dashboard.")
    add_bullet(doc, "Point to registered trials and patient registry size.")
    add_para(
        doc,
        "Say: “This is the system overview—protocols and patient sources used by the pipeline.”",
        italic=True,
    )

    add_section_heading(doc, "3. Patient Matching — Quick Entry (90 seconds)")
    add_bullet(doc, "Open Patient Matching.")
    add_bullet(doc, "In sidebar Quick Entry: Age 55, Male, NSCLC, Stage IIIA, BMI 25, ECOG 1.")
    add_bullet(doc, "Generate note → Screen Quick Entry Note.")
    add_bullet(doc, "Expand the QUICK-ENTRY row.")
    add_bullet(doc, "Show Narrative tab, then Entities, then Audit.")
    add_para(
        doc,
        "Say: “This demonstrates the full loop: note → extraction → symbolic validation → "
        "explainability → clinician review.”",
        italic=True,
    )

    add_section_heading(doc, "4. Patient Matching — CSV batch (60 seconds)")
    add_bullet(doc, "Keep BioBERT batch size small (for example 5–10) for a fast demo.")
    add_bullet(doc, "Select Oncology only.")
    add_bullet(doc, "Run CSV batch.")
    add_bullet(doc, "Open one patient and show primary trial + match percentage.")
    add_para(
        doc,
        "Say: “Batch mode screens real loaded patients. Quick Entry age does not filter the "
        "CSV list—only the chosen disease filter does.”",
        italic=True,
    )

    add_section_heading(doc, "5. Cohort Discovery (60 seconds)")
    add_bullet(doc, "Open Cohort Discovery.")
    add_bullet(doc, "Choose a registered protocol (for example ONC-001).")
    add_bullet(doc, "Click Search Cohort.")
    add_bullet(doc, "Show Eligible / Conditional / Ineligible banner, then expand one patient.")
    add_para(
        doc,
        "Say: “Matching asks which trials fit a patient. Cohort Discovery asks which "
        "patients fit one trial. Cohort mode is symbolic-only and fast.”",
        italic=True,
    )

    add_section_heading(doc, "6. Evaluation (60–75 seconds)")
    add_bullet(doc, "Open Evaluation.")
    add_bullet(doc, "Select Synthetic Data; keep patient count modest if live-running.")
    add_bullet(doc, "If results are already cached, show them; otherwise click Run Benchmark.")
    add_bullet(doc, "Point to 2D chart: Precision / Recall / FPR.")
    add_para(
        doc,
        "Say: “On synthetic n=100, EthiMatch reached about 65.5% F1 versus 56.2% for pure "
        "neural, and reduced FPR from about 2.4% to 0.6%. McNemar favoured EthiMatch but "
        "was not significant at 0.05 (p≈0.067), so I do not overclaim statistical certainty.”",
        italic=True,
    )

    add_section_heading(doc, "7. Closing (20–30 seconds)")
    add_para(
        doc,
        "Say: “In summary, EthiMatch shows that symbolic safety constraints and explainable "
        "audit trails can improve the safety profile of AI-assisted trial matching. It is "
        "demo-ready as a research prototype, with clear limitations and a path for future "
        "clinical validation.”",
        italic=True,
    )

    add_section_heading(doc, "Likely viva questions (short answers)")
    add_table(
        doc,
        ["Question", "One-line answer"],
        [
            [
                "What is novel?",
                "Neuro-symbolic separation of NER, rules, XAI, and clinician review with reproducible evaluation.",
            ],
            [
                "Why symbolic layer?",
                "To reduce unsafe false positives and make protocol criteria explicit/auditable.",
            ],
            [
                "Why not 100% clinical ready?",
                "Synthetic/demo data, limited protocols, and unpaired clinician gold labels.",
            ],
            [
                "What do P/R/F1 mean?",
                "Precision=correct yes; Recall=found true cases; F1=balance of both.",
            ],
            [
                "Biggest result?",
                "Lower false positive rate with competitive/improved F1 versus pure neural.",
            ],
        ],
    )

    add_section_heading(doc, "Demo risk controls")
    add_bullet(doc, "If BioBERT is slow: show Quick Entry result already cached; keep batch small.")
    add_bullet(doc, "If Evaluation is slow: open saved chart/table from Evaluation chapter document.")
    add_bullet(doc, "If oncology filter is empty: increase patient limit to 100+ or choose All patients briefly.")
    add_bullet(doc, "Never claim clinical deployment readiness.")

    OUT_VIVA.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_VIVA)
    print(f"Wrote: {OUT_VIVA}")


def main() -> None:
    build_conclusion()
    build_viva_script()
    print("Done.")


if __name__ == "__main__":
    main()
