"""Content sections: evaluation methodology, design rationale, pros/cons, risks,
future work, glossary, conclusion."""
from __future__ import annotations

from build_doc_part1 import (
    NAVY, TEAL, GOLD, GREEN, RED, GREY, PURPLE,
    style_heading, body_para, callout, bullet, make_table, add_image,
    add_page_break,
)


def build_evaluation(doc) -> None:
    style_heading(doc, "11. Evaluation Methodology and Statistical Validity", level=1)
    body_para(
        doc,
        "EthiMatch is evaluated by a controlled experiment: the SAME patients and the SAME "
        "neural extractions are fed into two decision logics. Path A is the full "
        "neuro-symbolic system. Path B is a pure-neural baseline that uses the same "
        "extractions but skips symbolic validation. Because only the decision logic differs, "
        "any change in performance is attributable to the symbolic layer.",
    )
    add_image(doc, "07_evaluation.png", width_in=6.5,
              caption="Figure 11.1 - Controlled comparison: same inputs, two decision logics")

    style_heading(doc, "11.1 Metrics", level=2)
    metric_rows = [
        ["Precision", "Of patients flagged eligible, how many truly are.", "Higher = fewer unsafe trial offers."],
        ["Recall",    "Of truly eligible patients, how many were found.",  "Higher = fewer missed candidates."],
        ["F1-score",  "Harmonic mean of precision and recall.",           "Balanced single-number summary."],
        ["FPR",       "Of ineligible patients, how many were wrongly flagged.", "Lower = safer for the patient."],
        ["McNemar p", "Paired test on discordant predictions.",           "Tells us if the difference is real, not luck."],
    ]
    make_table(
        doc, headers=["Metric", "Meaning", "Why it matters clinically"],
        rows=metric_rows, col_widths=[1.2, 3.0, 2.2],
    )

    style_heading(doc, "11.2 Why McNemar's Test?", level=2)
    body_para(
        doc,
        "Because both systems are evaluated on exactly the same patients, the observations "
        "are paired, not independent. McNemar's test is the correct statistical tool for "
        "paired binary outcomes: it looks only at the cases where the two systems disagree "
        "(the discordant pairs) and asks whether one system is reliably better. A standard "
        "two-sample test would be invalid here because it assumes independent samples.",
    )
    callout(
        doc,
        title="Reproducibility Guarantee",
        body=(
            "All evaluation runs use fixed random seeds (seed=42) and content-keyed silver-cache "
            "reads. Re-running the same benchmark on the same data produces byte-identical numbers, "
            "which was verified twice during development. Outputs are written to "
            "results/comparative_benchmark.json and results/figures/ as 2D and 3D PNGs."
        ),
        fill_hex="E3F2FD", border_hex="0B2447",
    )
    add_page_break(doc)


def build_rationale(doc) -> None:
    style_heading(doc, "12. Design Rationale: Why EthiMatch Was Built This Way", level=1)

    style_heading(doc, "12.1 Why Neuro-Symbolic and not Pure Neural?", level=2)
    body_para(
        doc,
        "A pure neural system can read text fluently but cannot guarantee that it applied "
        "every eligibility rule, and it can hallucinate facts. A pure rule system is safe "
        "but cannot read free-text notes. EthiMatch combines the strengths of both: the "
        "neural layer reads, the symbolic layer decides. This mirrors the architecture "
        "shown to improve safety in oncology by Loaiza-Bonilla et al. (2026).",
    )

    style_heading(doc, "12.2 Why 'INCONCLUSIVE' is a First-Class Verdict", level=2)
    body_para(
        doc,
        "In a clinical setting, a confident wrong answer is more dangerous than an honest "
        "'I do not know'. When a required field is missing, EthiMatch returns INCONCLUSIVE "
        "rather than guessing. This converts silent failures into visible, auditable gaps "
        "that a clinician can resolve.",
    )

    style_heading(doc, "12.3 Why Contracts Between Layers?", level=2)
    body_para(
        doc,
        "Each layer exchanges a typed object (PatientProfile, ExtractedEntities, "
        "ValidationReport, AuditReport). This means each layer can be built, tested and "
        "upgraded in isolation. Swapping Synthea for MIMIC required zero changes to the "
        "validator, because both providers emit the same PatientProfile contract.",
    )

    style_heading(doc, "12.4 Why a Silver Cache with Hashing?", level=2)
    body_para(
        doc,
        "Running BioBERT on every UI click would make the dashboard unusable on CPU. The "
        "silver cache stores extractions on disk. Crucially, each cache file is stamped "
        "with a hash of its input, so if the underlying note or the synthesis logic ever "
        "changes, the stale cache is automatically invalidated and the patient is "
        "re-extracted. This gives both speed and correctness.",
    )
    add_page_break(doc)


def build_pros_cons(doc) -> None:
    style_heading(doc, "13. Advantages of the Chosen Design", level=1)
    advantages = [
        ["Safety", "Symbolic rules guarantee every criterion is checked; missing data is never guessed."],
        ["Explainability", "Every verdict carries per-rule reasons and SHAP-style weights, satisfying clinical adoption requirements."],
        ["Speed", "Silver cache + structured early-exit avoid the majority of neural calls on real cohorts."],
        ["Modularity", "Typed contracts let each layer be developed, tested and replaced independently."],
        ["Reproducibility", "Fixed seeds and content-keyed caching make every result repeatable byte-for-byte."],
        ["Portability", "Runs on a CPU-only student laptop; Docker support enables one-command deployment."],
        ["Data flexibility", "Synthea and MIMIC are interchangeable behind one provider contract; dual-dataset strategy mitigates access risk."],
        ["Statistical rigour", "McNemar's paired test proves the symbolic layer's contribution is real, not random."],
    ]
    make_table(
        doc, headers=["Advantage", "Explanation"],
        rows=advantages, col_widths=[1.7, 4.7],
        header_fill="3A7D44",
    )

    style_heading(doc, "14. Limitations and Trade-Offs", level=1)
    limitations = [
        ["Vocabulary scope", "Diseases, stages and biomarkers are limited to an oncology subset defined in config.py. Expanding to other domains needs new vocabulary and trials."],
        ["NER ceiling", "The off-the-shelf model is not fine-tuned on EthiMatch notes, so very unusual phrasings may be missed (mitigated by regex fallback)."],
        ["Synthetic bias", "Synthea data is generated by rules, so it may flatter a rule-based system. This is why MIMIC-IV Demo is included as a real-world check."],
        ["Small MIMIC demo", "The MIMIC-IV Demo cohort is only 100 patients, limiting statistical power on that dataset alone."],
        ["No live EHR", "The project deliberately excludes live hospital EHR integration and regulatory approval (out of scope per the proposal)."],
        ["CPU latency", "First neural extraction per patient is slow on CPU; mitigated, not eliminated, by the silver cache."],
    ]
    make_table(
        doc, headers=["Limitation", "Detail and mitigation"],
        rows=limitations, col_widths=[1.7, 4.7],
        header_fill="C53030",
    )
    add_page_break(doc)


def build_risks(doc) -> None:
    style_heading(doc, "15. Risk Register and Mitigations", level=1)
    body_para(
        doc,
        "The risks below were identified at design time and each has a concrete mitigation "
        "already implemented in the codebase.",
    )
    risk_rows = [
        ["Neural-inference latency", "Medium", "Silver cache stores extractions on disk; structured early-exit avoids most neural calls."],
        ["Incomplete patient data",  "High",   "Symbolic validator returns INCONCLUSIVE for missing fields rather than guessing."],
        ["Data-access delays (MIMIC)","Medium", "Pipeline runs end-to-end on Synthea + MIMIC-IV Demo, so completion never depends on full credentialing."],
        ["Stale cache after logic change", "Medium", "Hash-based invalidation re-extracts automatically when the input or CACHE_VERSION changes."],
        ["Over-fitting to synthetic data", "Medium", "Real MIMIC-IV Demo cohort included; McNemar's test reported per dataset."],
        ["Cross-platform encoding bugs", "Low", "console.py forces UTF-8 I/O for Windows PowerShell."],
    ]
    make_table(
        doc, headers=["Risk", "Severity", "Mitigation (already in code)"],
        rows=risk_rows, col_widths=[2.2, 1.0, 3.2],
    )
    add_page_break(doc)


def build_future_glossary_conclusion(doc) -> None:
    style_heading(doc, "16. Future Work", level=1)
    bullet(doc, "Fine-tune the NER model on EthiMatch-style notes using finetune_ner.py to lift extraction recall.")
    bullet(doc, "Apply for full MIMIC-IV credentialing to scale the real-world evaluation beyond 100 patients.")
    bullet(doc, "Expand the trial registry and vocabulary to non-oncology domains.")
    bullet(doc, "Add a feedback loop so clinician overrides become labelled training data.")
    bullet(doc, "Integrate with a live FHIR endpoint behind the existing provider contract.")

    style_heading(doc, "17. Glossary", level=1)
    glossary = [
        ["Neuro-symbolic", "Combining a neural model (reads text) with a symbolic engine (applies rules)."],
        ["NER", "Named Entity Recognition - finding diseases, drugs, ages etc. in text."],
        ["BioBERT / DistilBERT", "Transformer language models adapted to biomedical text."],
        ["Silver cache", "On-disk store of extracted entities (the medallion 'silver' tier)."],
        ["Cache invalidation", "Detecting stale cached data via an input hash and re-computing it."],
        ["Symbolic validator", "The deterministic rule engine that decides eligibility."],
        ["INCONCLUSIVE", "Verdict used when required data is missing - never a guess."],
        ["XAI", "Explainable AI - making the system's reasoning visible to a human."],
        ["McNemar's test", "A statistical test for paired binary classifier comparisons."],
        ["Medallion architecture", "Bronze (raw) / Silver (processed) / Gold (verified) data tiers."],
        ["FPR", "False Positive Rate - ineligible patients wrongly flagged eligible."],
        ["Provider contract", "The abstract interface every data source implements."],
    ]
    make_table(
        doc, headers=["Term", "Meaning"],
        rows=glossary, col_widths=[1.9, 4.5],
    )

    style_heading(doc, "18. Conclusion", level=1)
    body_para(
        doc,
        "EthiMatch demonstrates that a disciplined, contract-driven neuro-symbolic "
        "architecture can deliver clinical-trial matching that is simultaneously fast, "
        "safe and explainable. The coding standards were fixed before implementation and "
        "followed throughout; the architecture cleanly separates reading from deciding; "
        "every academic reference maps to a concrete module; and the evaluation uses a "
        "paired statistical test to prove the symbolic layer's contribution is real. The "
        "design choices documented here are what turn a research idea into a defensible, "
        "reproducible dissertation artefact.",
    )
    callout(
        doc,
        title="One-line summary",
        body=(
            "The neural layer reads the patient; the symbolic layer protects the patient; "
            "the explainability layer earns the clinician's trust."
        ),
        fill_hex="E3F2FD", border_hex="0B2447",
    )
