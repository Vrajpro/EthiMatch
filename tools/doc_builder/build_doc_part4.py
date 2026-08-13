"""Content sections: remaining file documentation (data dual providers, core, UI, eval),
trial protocols, references mapping."""
from __future__ import annotations

from build_doc_part1 import (
    NAVY, TEAL, GOLD, GREEN, RED, GREY, PURPLE,
    style_heading, body_para, callout, bullet, make_table, add_image,
    add_page_break,
)


def build_files_dual_providers(doc) -> None:
    style_heading(doc, "data_loader.py - Unified Dual-Source Providers", level=3)
    body_para(doc, "Role: The active loader used by the running app. Provides two concrete "
                   "implementations of PatientDataProvider that share a unified output shape, "
                   "and a single factory function load_provider().")
    make_table(
        doc, headers=["Method / Class", "Purpose"],
        rows=[
            ["generate_mock_clinical_note(profile)",
             "Synthesises an EHR-style note from a PatientProfile. Includes truthful negation "
             "('no history of diabetes') only when the structured data confirms absence."],
            ["_stamp_mock_note(profile)",
             "Sets profile.ehr_note if missing, ensuring every profile has a readable note."],
            ["SyntheaDualSourceProvider(RealCSVProvider)",
             "Wraps Synthea CSV loading and stamps each profile with data_source='Synthea'."],
            ["MIMICDualSourceProvider(PatientDataSource)",
             "Loads patients, admissions, diagnoses and prescriptions from Datasets/. Computes "
             "an admission-year correction to recover realistic ages from MIMIC's anchor-year scheme."],
            ["MIMICDualSourceProvider.is_available(data_dir) (static)",
             "Reports whether the four required CSVs are present. Used by the evaluation harness "
             "to decide if MIMIC can be benchmarked."],
            ["normalise_source(source)",
             "Coerces loose strings ('mimic', 'MIMIC-IV-Demo') into the canonical 'MIMIC' / 'Synthea'."],
            ["load_provider(source, limit, data_dir, verbose)",
             "Factory returning the correct provider for the requested source."],
        ],
        col_widths=[3.0, 3.4],
    )

    style_heading(doc, "mimic_database.py - Legacy MIMIC-IV-Note Loader", level=3)
    body_para(doc, "Role: Historical loader for credentialed MIMIC-IV-Note discharge summaries. "
                   "It is kept in the repository for reference but is no longer used in the "
                   "running pipeline - MIMICDualSourceProvider in data_loader.py replaced it. "
                   "Listed here for transparency, since the dissertation discusses why the "
                   "switch was necessary.")
    add_page_break(doc)


def build_files_core(doc) -> None:
    style_heading(doc, "8.3 Core Pipeline", level=2)

    style_heading(doc, "neural_extractor.py - Stage 3 (Neural)", level=3)
    body_para(doc, "Role: Loads and runs the biomedical NER model d4data/biomedical-ner-all "
                   "(a DistilBERT model fine-tuned on the MACCROBAT biomedical corpus), then "
                   "post-processes its output with regex fallbacks and a negation filter.")
    make_table(
        doc, headers=["Method", "What it does"],
        rows=[
            ["ExtractedEntities (dataclass)",
             "Structured output: age, gender, disease, stage, biomarkers, comorbidities, prior_therapies, ECOG, BMI, confidence_scores."],
            ["NeuralExtractor.__init__(model_name, device, verbose)",
             "Loads HuggingFace model lazily on first call to extract()."],
            ["extract(note)",
             "Public API. Runs NER, regex fallback, negation filter. Returns ExtractedEntities."],
            ["_run_ner(text)",
             "Calls the HuggingFace pipeline and groups sub-word tokens."],
            ["_apply_ner_results(...)",
             "Maps each detected entity to the right field (disease, biomarker, comorbidity, etc.)."],
            ["_apply_regex_fallback(...)",
             "Patterns for fields BioBERT misses: explicit age numbers, ECOG scores, BMI."],
            ["_apply_negation_filter(...)",
             "Strips facts found inside negation phrases ('no history of', 'denies', 'rule out')."],
            ["_normalise_disease / _normalise_biomarker(raw)",
             "Map free-text to the canonical codes listed in config.py."],
        ],
        col_widths=[2.8, 3.6],
    )

    style_heading(doc, "symbolic_validator.py - Stage 4 (Symbolic)", level=3)
    body_para(doc, "Role: The deterministic heart of EthiMatch. Applies ten rules to every "
                   "trial in the registry and produces a ValidationReport that the UI can display.")
    make_table(
        doc, headers=["Method", "What it does"],
        rows=[
            ["RuleVerdict (Enum)",
             "Exactly five values: PASS, FAIL, WARNING, INCONCLUSIVE, SKIP."],
            ["RuleResult (dataclass)",
             "One rule's outcome: rule_name, verdict, explanation, criterion, patient_val, rule_code."],
            ["ValidationReport (dataclass)",
             "Aggregates one trial's rule results into eligibility, counts and a JSON-safe dict."],
            ["SymbolicValidator.validate(entities, trial)",
             "Public API. Runs all ten checks and returns a ValidationReport."],
            ["validate_all_trials(entities, trials)",
             "Loops over the trial registry, returns reports sorted by eligibility."],
            ["match_score(report)",
             "Returns a 0-100 score used to rank trials in the UI."],
            ["best_trial_report(reports) (classmethod)",
             "Picks the headline trial for the patient when multiple trials match."],
            ["_check_age / _check_gender / _check_disease / _check_stage",
             "Demographic and disease rules. Each returns a RuleResult."],
            ["_check_required_biomarkers / _check_ecog / _check_bmi_max / _check_bmi_min",
             "Eligibility rules with numerical thresholds."],
            ["_check_excluded_comorbidities / _check_excluded_therapies",
             "Exclusion rules. A single fail blocks the patient unless a waiver applies."],
            ["_check_low_confidence_warnings",
             "Emits WARNING when a neural extraction has confidence below the threshold."],
        ],
        col_widths=[3.0, 3.4],
    )

    style_heading(doc, "ethimatch_pipeline.py - Orchestrator (Stages 1+2)", level=3)
    body_para(doc, "Role: The single class clients interact with. It implements stages 1 and 2 "
                   "of the funnel inline (cache lookup, structured early-exit) and delegates "
                   "stages 3, 4 and 5 to the specialised modules.")
    make_table(
        doc, headers=["Method", "What it does"],
        rows=[
            ["AuditReport (dataclass)",
             "Combined output for one patient: entities + trial reports + narrative + summary."],
            ["MatchingPatientResult / CohortResult",
             "Row-level results used by the Patient Matching and Cohort Discovery pages."],
            ["EthiMatchPipeline.__init__(...)",
             "Instantiates the NeuralExtractor, the SymbolicValidator, and loads the trial registry."],
            ["extract_entities(note, patient_id)",
             "Stage 1: silver-cache lookup with hash invalidation. Falls through to NeuralExtractor on miss."],
            ["_resolve_patient_entities_and_reports(...)",
             "The full funnel logic: cache, structured early-exit, neural extraction, validation."],
            ["validate_entities(entities)",
             "Calls SymbolicValidator.validate_all_trials."],
            ["explain_reports(entities, reports)",
             "Calls xai_explainer.build_full_audit_narrative."],
            ["_build_audit_report(...)",
             "Packages everything into an AuditReport for the UI / PDF export."],
            ["run(note)",
             "Public API for Quick Note Matching (single note in, AuditReport out)."],
            ["run_patient(patient_id, provider)",
             "Public API for patient-id-based matching."],
            ["run_batch(...) / run_batch_patients(...)",
             "Bulk variants used by Cohort Discovery and the evaluation harness."],
            ["run_cohort_search(criteria)",
             "Symbolic-only sweep against a single trial. Used by Cohort Discovery."],
        ],
        col_widths=[3.0, 3.4],
    )

    style_heading(doc, "silver_cache.py - Stage 1 Cache", level=3)
    body_para(doc, "Role: Persistent per-patient JSON cache with hash-based invalidation. Speeds "
                   "up repeated UI sessions and batch evaluations.")
    make_table(
        doc, headers=["Method", "Purpose"],
        rows=[
            ["_safe_filename(patient_id)",   "Strips characters that are illegal on Windows filenames."],
            ["silver_path(patient_id)",      "Returns the absolute path of the cache file."],
            ["compute_input_hash(note)",     "SHA-256 of 'CACHE_VERSION|note'. Stable identifier for cached data."],
            ["load_silver_entities(pid, expected_hash)",
             "Returns the cached dict if present AND the stored hash matches, otherwise None."],
            ["save_silver_entities(pid, entities, input_hash)",
             "Writes the cache file and stamps it with _cache_meta = {cache_version, input_hash}."],
            ["count_silver_entities() / list_silver_patient_ids()",
             "Diagnostics used by the dashboard and the materialize script."],
        ],
        col_widths=[3.0, 3.4],
    )

    style_heading(doc, "xai_explainer.py - Stage 5 (Explainability)", level=3)
    body_para(doc, "Role: Turns a list of ValidationReports into clinician-readable narratives "
                   "and computes SHAP-style attribution weights for the dashboard.")
    make_table(
        doc, headers=["Method", "Purpose"],
        rows=[
            ["explain_rule(rule)",
             "One-line natural-language explanation for a single RuleResult."],
            ["build_clinical_narrative(rule_results, trial)",
             "Paragraph-level narrative for one trial."],
            ["build_full_audit_narrative(note, entities, reports)",
             "Full audit narrative spanning every trial for one patient."],
            ["build_executive_summary(reports, entities)",
             "Short headline used in master-detail tables."],
            ["compute_criteria_advice_weights(reports)",
             "Per-criterion importance: how much each rule contributed to the verdict."],
            ["compute_extraction_impact(entities)",
             "Per-entity importance: how confident the extraction was per field."],
        ],
        col_widths=[3.0, 3.4],
    )

    style_heading(doc, "trial_registry.py - Trial Loader", level=3)
    body_para(doc, "Role: Reads JSON trial protocols from the trials/ folder, sanitises them "
                   "through config.py, and exposes a flat list for the validator.")
    make_table(
        doc, headers=["Method", "Purpose"],
        rows=[
            ["load_trial_file(path) / load_all_trials(directory)", "Reads and validates JSON (and optional YAML) trial protocols."],
            ["get_trial_by_id(trial_id)",                          "Lookup by ID, used by the UI."],
            ["trial_protocol_relpath(trial_id)",                   "Returns a friendly path for display."],
            ["trial_select_label(trial)",                          "Builds the dropdown label (Disease, Stage, ID)."],
            ["trials_for_export(trials)",                          "Strips internal fields before JSON export."],
            ["_normalize_trial(raw, source)",                      "Applies sanitize_trial_criteria from config.py to loose JSON."],
        ],
        col_widths=[3.0, 3.4],
    )
    add_page_break(doc)


def build_files_ui_eval(doc) -> None:
    style_heading(doc, "8.4 UI Layer (Streamlit)", level=2)

    style_heading(doc, "ui/pages.py - One Function per Tab", level=3)
    make_table(
        doc, headers=["Method", "Purpose"],
        rows=[
            ["page_dashboard()",            "Renders KPIs, sample notes, architecture preview, trial registry table."],
            ["page_matching(quick_note)",   "Renders Patient Matching: Quick Note + batch master/detail."],
            ["page_cohort(criteria)",       "Renders Cohort Discovery: trial-first symbolic sweep."],
            ["page_evaluation()",           "Renders the benchmark UI with McNemar + PNG export."],
            ["load_pipeline() (cached)",    "Memoised EthiMatchPipeline. Avoids reloading BioBERT on every click."],
            ["_get_patient_provider()",     "Returns the active provider based on sidebar selection."],
            ["_build_quick_note()",         "Form-based note builder so users do not need to type raw EHR."],
            ["_build_cohort_criteria()",    "Cohort search form (disease, stage, biomarkers, comorbidities)."],
        ],
        col_widths=[3.0, 3.4],
    )

    style_heading(doc, "ui/components.py - Reusable Widgets", level=3)
    make_table(
        doc, headers=["Function group", "Members"],
        rows=[
            ["Layout & headers",     "render_page_header, render_section, render_panel_start/end, clinical_panel, render_footer."],
            ["Status banners",       "render_clinical_notice, render_status_metric, render_themed_status_banner, render_verdict_pill_html."],
            ["Plotly charts",        "build_weight_of_advice_figure, build_criteria_weight_figure, build_extraction_impact_figure, build_evaluation_comparison_figure[_3d]."],
            ["Evaluation widgets",   "render_evaluation_benchmark_chart, _render_benchmark_png_export, render_benchmark_interpretation."],
            ["Master-detail",        "filter_matching_results, build_matching_master_table, render_matching_detail_panel, similar for cohort."],
            ["Patient 360",          "render_patient_360_panel, render_matching_patient_detail (full audit view)."],
        ],
        col_widths=[2.4, 4.0],
    )

    style_heading(doc, "ui/theme.py", level=3)
    body_para(doc, "Role: Exposes a single function get_theme_css() returning the global CSS "
                   "string (colour variables, typography, panel shadows). Imported by app.main().")

    style_heading(doc, "ui/auth.py - Optional Login (Placeholder)", level=3)
    body_para(doc, "Role: A no-op authentication module. Kept so the system can be wired into "
                   "hospital SSO without changing the UI. Functions: init_session, is_authenticated, "
                   "logout, render_login_page.")

    style_heading(doc, "8.5 Evaluation Layer", level=2)

    style_heading(doc, "evaluation.py - Benchmark Harness", level=3)
    make_table(
        doc, headers=["Method", "Purpose"],
        rows=[
            ["TrialMetrics (dataclass)",
             "TP/FP/TN/FN counts with derived accuracy, precision, recall, F1, specificity, FPR."],
            ["compute_metrics(preds, gold, trials, conditionals)",
             "Per-trial confusion matrices."],
            ["macro_average(metrics_list)",
             "Macro-averaged P / R / F1 across trials."],
            ["mcnemar_test(gold, pred_a, pred_b, trial_ids)",
             "Paired significance test: chi-square, p-value, discordant pair counts."],
            ["run_pipeline_on_note(note, extractor, validator, trials)",
             "Runs both Neuro-Symbolic and Pure Neural on the same note for direct comparison."],
            ["pure_neural_eligibility(entities, trial)",
             "The baseline decision rule: inclusion-only, no symbolic constraints."],
            ["run_comparative_benchmark(data_source, n_patients)",
             "Headline benchmark: P / R / F1 / FPR plus McNemar's test for one dataset."],
            ["run_dashboard_evaluation(n_patients, data_sources)",
             "Runs all three datasets and saves results/comparative_benchmark.json."],
            ["is_mimic_benchmark_available(mimic_dir)",
             "Pre-flight check for the MIMIC dataset (presence of patients/diagnoses/etc.)."],
            ["save_dashboard_benchmark_payload(payload)",
             "Persists the benchmark JSON to results/."],
        ],
        col_widths=[3.0, 3.4],
    )

    style_heading(doc, "evaluation_cohort.py - Gold-Label Generation", level=3)
    make_table(
        doc, headers=["Method", "Purpose"],
        rows=[
            ["profile_to_entities(profile)",
             "Converts structured patient data into the entity dict the validator expects."],
            ["compute_gold_standard(patients, trials, validator)",
             "Derives 'truly eligible' labels by running the SymbolicValidator on structured rows."],
            ["build_scaled_cohort(n, seed)",
             "Synthetic evaluation cohort for ablation studies."],
        ],
        col_widths=[3.0, 3.4],
    )

    style_heading(doc, "baseline_llm.py - Pure-Neural Baseline", level=3)
    make_table(
        doc, headers=["Class / Function", "Purpose"],
        rows=[
            ["BaselineClassifier (ABC)",
             "Interface for any baseline (predict_patient, predict_batch)."],
            ["HeuristicLLMBaseline",
             "Deterministic keyword/regex baseline. Provides a stable, no-API-cost reference."],
            ["OpenAIBaseline",
             "Optional GPT-4 baseline. Off by default; would require an API key."],
            ["get_baseline(mode)",
             "Factory returning the right baseline class."],
        ],
        col_widths=[2.4, 4.0],
    )

    style_heading(doc, "find_eligible_patients.py - CLI Scanner", level=3)
    body_para(doc, "Role: Command-line tool that scans the CSV cohort and prints eligible "
                   "patients for each trial. Used during early development and for spot checks "
                   "outside the Streamlit UI.")
    style_heading(doc, "finetune_ner.py - Optional NER Fine-Tuning", level=3)
    body_para(doc, "Role: Optional pipeline for fine-tuning the NER model on a labelled corpus "
                   "of EthiMatch notes. Not part of the production flow; included for examiners "
                   "interested in the extension path.")
    style_heading(doc, "pdf_export.py - PDF Audit Report Renderer", level=3)
    body_para(doc, "Role: Renders an AuditReport (or a cohort summary) into a single PDF for "
                   "clinician handoff. Uses fpdf2 to build the document with header, footer, "
                   "section titles, and a body that supports Unicode.")
    style_heading(doc, "sync_config.py - Vocabulary Sync Tool", level=3)
    body_para(doc, "Role: Maintenance tool that reads Synthea descriptions and reports any terms "
                   "missing from config.py. Helps keep the canonical vocabulary aligned with "
                   "real CSV ground truth.")

    style_heading(doc, "8.6 Scripts", level=2)
    make_table(
        doc, headers=["Script", "Purpose"],
        rows=[
            ["scripts/materialize_silver.py",
             "Pre-warms the silver cache for a chosen --source (synthea / mimic), batch-wise."],
            ["scripts/qa_system_check.py",
             "Smoke-test suite. Verifies registry, validators, mock notes, deterministic outcomes."],
            ["scripts/generate_thesis_audit_examples.py",
             "Emits sample audit reports for the dissertation appendix."],
            ["scripts/_verify_full_eval.py",
             "One-shot 3-dataset benchmark verifier (added in the final evaluation pass)."],
            ["scripts/evaluation.py",
             "Older standalone CLI evaluator. Kept for reference; newer evaluation.py at root is canonical."],
        ],
        col_widths=[2.7, 3.7],
    )
    add_page_break(doc)


def build_trials(doc) -> None:
    style_heading(doc, "9. Trial Protocols (JSON Contracts)", level=1)
    body_para(
        doc,
        "Trial protocols live in ethimatch/trials/ as one JSON file per trial. The "
        "JSON schema is intentionally simple: every trial has a trial_id, a "
        "disease_target, an inclusion block and an exclusion block. This means new "
        "trials can be added by clinicians without touching any Python.",
    )
    trial_rows = [
        ["trial_001.json",          "NSCLC, Stage III-IV",          "Primary oncology trial."],
        ["trial_002.json",          "Breast cancer, Stage II-IV",   "Demonstrates non-NSCLC support."],
        ["trial_003.json",          "SCLC, Stage III-IV",           "Small-cell variant."],
        ["trial_004.json",          "NSCLC, Stage IIIB-IV",         "Late-stage NSCLC variant."],
        ["oncology_trial_001.json", "Pembrolizumab + chemo, NSCLC",  "Realistic immuno-onc protocol."],
        ["baseline_trial_002.json", "Any adult patient (>=18)",      "Open-cohort CONTROL trial for benchmarking."],
    ]
    make_table(
        doc, headers=["File", "Disease / Stage", "Notes"],
        rows=trial_rows, col_widths=[2.4, 2.0, 2.0],
    )
    callout(
        doc,
        title="Why JSON for Protocols?",
        body=(
            "Trial criteria evolve frequently. Storing them in JSON instead of Python "
            "code means a clinician can edit a trial without becoming a developer, the "
            "git history shows protocol changes clearly, and the symbolic validator "
            "always reads the same canonical structure."
        ),
        fill_hex="FFF3E0", border_hex="F0A04B",
    )
    add_page_break(doc)


def build_references_mapping(doc) -> None:
    style_heading(doc, "10. Literature References and Implementation Mapping", level=1)
    body_para(
        doc,
        "Every academic reference cited in the proposal is anchored to a concrete "
        "module of EthiMatch. This section shows the trace: paper -> concept -> file "
        "-> function. The diagram below summarises the mapping at a glance, and the "
        "table that follows gives the per-paper details.",
    )
    add_image(doc, "06_references_map.png", width_in=6.5,
              caption="Figure 10.1 - Each paper maps to a specific module")

    style_heading(doc, "10.1 Per-Paper Trace", level=2)
    ref_rows = [
        ["Carlisle et al. (2015)",
         "19% of trials fail accrual",
         "Problem motivation",
         "README.md, proposal section 1",
         "Used to justify the need for automated screening - the introduction of every dissertation chapter and the dashboard's headline KPI both quote this."],
        ["Lee et al. (2020) - BioBERT",
         "Domain-tuned biomedical transformers outperform general ones",
         "Choice of NER model",
         "neural_extractor.py (d4data/biomedical-ner-all)",
         "Inspired the choice of a biomedical-pretrained model. EthiMatch uses a DistilBERT model trained on the MACCROBAT biomedical corpus (the spiritual successor of BioBERT) for the same reason."],
        ["Johnson et al. (2023) - MIMIC-IV",
         "Real-world EHR dataset for clinical NLP benchmarking",
         "Real-data evaluation",
         "data_loader.py (MIMICDualSourceProvider), Datasets/",
         "Used as the real-world counterpart to Synthea. The MIMIC-IV Demo subset (100 patients, no credentialing) provides authentic data without ethical risk."],
        ["Loaiza-Bonilla et al. (2026)",
         "Neuro-symbolic AI improves trial-matching safety on 3,804 cancer patients",
         "Architectural blueprint",
         "symbolic_validator.py + ethimatch_pipeline.py",
         "Direct inspiration for the neuro-symbolic split. EthiMatch implements an open, reproducible academic version of the same idea (separate neural extraction and symbolic validation), with explicit INCONCLUSIVE semantics."],
        ["Lundberg and Lee (2017) - SHAP",
         "A unified, additive framework for explaining model predictions",
         "Explainability layer",
         "xai_explainer.py (compute_criteria_advice_weights, compute_extraction_impact)",
         "EthiMatch presents SHAP-style attribution weights for both rules and extracted entities, so clinicians see exactly which fact contributed to a verdict."],
        ["Zitianellis (2025)",
         "Pre-screening clinical-trial recruitment requires interpretable AI for adoption",
         "Verdict semantics and UX",
         "config.py + ui/components.py (INCONCLUSIVE verdict, missing-data analysis)",
         "Justifies the deliberate decision to expose INCONCLUSIVE rather than falling back to a YES/NO guess. The UI surfaces missing data as a first-class result."],
    ]
    make_table(
        doc, headers=["Paper", "Key claim used", "Role in EthiMatch", "Implemented in", "How / why"],
        rows=ref_rows, col_widths=[1.4, 1.5, 1.2, 1.4, 1.5],
    )

    callout(
        doc,
        title="Implementation Trace Rule",
        body=(
            "If a paper cannot be traced to a concrete file or function in this project, it does "
            "not belong in the reference list. Every cited paper above passes that test, which "
            "is what makes the literature review and the system internally consistent."
        ),
        fill_hex="E8F5E9", border_hex="3A7D44",
    )
    add_page_break(doc)
