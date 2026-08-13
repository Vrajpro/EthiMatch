"""Content sections: flowchart, use case, data flow, components, file documentation A."""
from __future__ import annotations

from build_doc_part1 import (
    NAVY, TEAL, GOLD, GREEN, RED, GREY, PURPLE,
    style_heading, body_para, callout, bullet, make_table, add_image,
    add_page_break,
)


def build_flowchart(doc) -> None:
    style_heading(doc, "4. System Flow Chart", level=1)
    body_para(
        doc,
        "The flow chart below traces a single Patient Matching request from start to finish. "
        "Diamond shapes are decision points, rectangles are processing steps, ovals are "
        "start/end states. The chart shows how the silver cache short-circuits expensive "
        "operations, and how the verdict propagates into the final audit report.",
    )
    add_image(doc, "04_flowchart.png", width_in=5.5,
              caption="Figure 4.1 - End-to-end flow for a single Patient Matching call")

    style_heading(doc, "4.1 Decision Points Explained", level=2)
    bullet(doc, "Silver cache hit? - Uses SHA-256 of the synthesised note (plus CACHE_VERSION). "
                "A miss forces re-extraction even if a stale file exists on disk.")
    bullet(doc, "Structured early-exit possible? - True when every trial in the registry already "
                "fails on a structured field (age, disease, gender). Avoids unnecessary BioBERT calls.")
    bullet(doc, "Verdict - Combines the eligible-flag from every trial. 'INCONCLUSIVE' is treated "
                "as a first-class outcome rather than a fallback or an error.")
    add_page_break(doc)


def build_use_case(doc) -> None:
    style_heading(doc, "5. Use Case Diagram", level=1)
    body_para(
        doc,
        "The use case diagram identifies three actors and the twelve functions they can "
        "trigger inside the EthiMatch boundary. The diagram follows the standard UML "
        "convention: stick figures for actors, ellipses for use cases, lines for "
        "associations.",
    )
    add_image(doc, "03_use_case.png", width_in=6.5,
              caption="Figure 5.1 - Actors and the EthiMatch system boundary")

    style_heading(doc, "5.1 Actor Responsibilities", level=2)
    actor_rows = [
        ["Oncologist / Research Coordinator",
         "Primary clinical user. Runs Quick Note Matching, screens cohorts, reads audit "
         "reports, and exports PDFs. Has zero requirement to understand AI internals."],
        ["Hospital IT Administrator",
         "Pre-warms the silver cache, configures the active data source (Synthea or MIMIC), "
         "and inspects cache status. Operates the system at the infrastructure level."],
        ["Researcher / Dissertation Evaluator",
         "Runs the comparative benchmark across all data sources, inspects McNemar's "
         "significance test, exports publication-ready PNG figures, and edits trial "
         "protocols in JSON."],
    ]
    make_table(
        doc, headers=["Actor", "Responsibilities"],
        rows=actor_rows, col_widths=[2.4, 4.0],
    )
    add_page_break(doc)


def build_dataflow(doc) -> None:
    style_heading(doc, "6. Data Flow Diagram", level=1)
    body_para(
        doc,
        "The data flow diagram shows every piece of information in the system: where it "
        "originates, which module transforms it, and where it is delivered to the user.",
    )
    add_image(doc, "02_dataflow.png", width_in=6.5,
              caption="Figure 6.1 - Inputs, providers, core pipeline, output")

    style_heading(doc, "6.1 Data Tiers (Medallion Architecture)", level=2)
    medallion_rows = [
        ["Bronze",
         "data/synthea/, data/mimic/, trials/*.json",
         "Raw inputs as received from Synthea, MIMIC-IV Demo, and protocol authors. Never modified."],
        ["Silver",
         "ethimatch/data/silver/*.json",
         "Cached BioBERT extractions, one file per patient, stamped with input hash and cache version."],
        ["Gold",
         "ethimatch/results/*.json + figures/*.png",
         "Verified evaluation outputs (precision, recall, F1, FPR, McNemar) and publication figures."],
    ]
    make_table(
        doc, headers=["Tier", "Location", "Description"],
        rows=medallion_rows, col_widths=[0.8, 2.4, 3.2],
    )

    callout(
        doc,
        title="Why Medallion?",
        body=(
            "Separating raw, processed and verified data into three named tiers prevents "
            "accidental corruption of inputs, makes cache invalidation explicit (the silver "
            "tier is the only one that changes), and gives the dissertation a clean audit "
            "trail. Every result in the gold tier can be traced back through silver to bronze."
        ),
        fill_hex="FFF3E0", border_hex="F0A04B",
    )
    add_page_break(doc)


def build_components(doc) -> None:
    style_heading(doc, "7. Module Dependency / Component Diagram", level=1)
    body_para(
        doc,
        "The component diagram visualises which modules import which. Solid arrows mean "
        "the source module imports symbols from the target. The diagram is layered so that "
        "the UI sits on top, the pipeline in the middle, and the data and configuration "
        "modules at the base.",
    )
    add_image(doc, "05_components.png", width_in=6.5,
              caption="Figure 7.1 - Module dependency diagram")
    style_heading(doc, "7.1 Dependency Rules", level=2)
    bullet(doc, "UI never imports from data providers directly: it always goes through the pipeline.")
    bullet(doc, "Evaluation can import from the pipeline and providers, but never from UI.")
    bullet(doc, "Configuration (config.py) and schemas (schemas.py) are leaf modules: they import "
                "nothing from the rest of EthiMatch.")
    bullet(doc, "There are no circular imports. This is enforced by treating each layer as a "
                "directed acyclic graph of responsibilities.")
    add_page_break(doc)


def build_files_intro(doc) -> None:
    style_heading(doc, "8. File-by-File Documentation", level=1)
    body_para(
        doc,
        "The forty-eight files in EthiMatch are documented below in seven functional groups: "
        "Entry Points, Data Layer, Core Pipeline, UI Layer, Evaluation Layer, Trial Protocols, "
        "and Utility Scripts. Each entry lists the file's role, the key methods it exposes, and "
        "what each method does in clinical / engineering terms.",
    )

    style_heading(doc, "8.1 Entry Points", level=2)

    style_heading(doc, "app.py - Streamlit Launcher", level=3)
    body_para(doc, "Role: The single entry point. Boots Streamlit, draws the sidebar, dispatches "
                   "to the four UI pages.")
    make_table(
        doc, headers=["Method", "What it does", "Why it exists"],
        rows=[
            ["init_session()",
             "Seeds st.session_state with default values used across pages.",
             "Avoids KeyError when the user lands on a tab before any other has run."],
            ["_csv_registry_limit_label(value)",
             "Renders 'All patients' for None or the numeric cap.",
             "Keeps sidebar labels human-readable."],
            ["main()",
             "Injects theme CSS, builds the sidebar, and routes to the active page.",
             "The single source of truth for navigation state."],
        ],
        col_widths=[1.7, 2.7, 2.0],
    )

    style_heading(doc, "console.py - UTF-8 Safe Output", level=3)
    body_para(doc, "Role: Wraps stdout/stderr so Windows terminals do not garble accented or "
                   "non-ASCII output (a recurring problem when running on PowerShell).")
    make_table(
        doc, headers=["Method", "Purpose"],
        rows=[
            ["_configure_stdio()",   "Forces stdout/stderr to UTF-8 encoding."],
            ["safe_print(*args)",    "print() that survives Unicode characters."],
            ["to_json_safe(obj)",    "Recursive JSON-safe coercion (dataclasses, dates, enums)."],
            ["json_dumps(obj)",      "json.dumps with the safe coercer pre-applied."],
        ],
        col_widths=[2.2, 4.2],
    )

    style_heading(doc, "device_utils.py - Hardware Detection", level=3)
    body_para(doc, "Role: Single helper that returns 0 (CUDA GPU) or -1 (CPU) for the HuggingFace "
                   "pipeline. Lets the rest of the code stay device-agnostic.")
    add_page_break(doc)


def build_files_data(doc) -> None:
    style_heading(doc, "8.2 Data Layer", level=2)

    style_heading(doc, "data_interface.py - Abstract Contracts", level=3)
    body_para(doc, "Role: Defines the contract every data provider must satisfy. This is the "
                   "boundary that lets Synthea and MIMIC interchange without changing the pipeline.")
    make_table(
        doc, headers=["Method / Class", "Purpose"],
        rows=[
            ["ConditionRecord", "Typed record for one condition row (description, dates, active flag)."],
            ["MedicationRecord", "Typed record for one prescription row."],
            ["CarePlanRecord",   "Typed record for one care-plan row."],
            ["PatientDataProvider (ABC)",
             "Abstract base class. Concrete subclasses implement get_patient, get_conditions, "
             "get_medications, get_careplans, list_patient_ids, get_all_patients, source_name, "
             "get_patient_note."],
            ["compose_clinical_note(profile, conditions, medications)",
             "Fallback note composer used when a provider does not synthesise its own note."],
            ["_calc_age(birthdate, ref)",
             "Computes the patient's age in years, used by every provider."],
        ],
        col_widths=[2.3, 4.1],
    )

    style_heading(doc, "schemas.py - Typed CSV Row Classes", level=3)
    body_para(doc, "Role: Wraps every CSV row in a typed dataclass so the rest of the code "
                   "never deals with raw dictionaries. Each class has a from_row(row) factory "
                   "that performs type coercion and returns None for invalid rows.")
    make_table(
        doc, headers=["Class", "Source", "Used by"],
        rows=[
            ["MIMICPatient",         "patients.csv",      "MIMICDualSourceProvider"],
            ["MIMICAdmission",       "admissions.csv",    "Anchor-year correction"],
            ["MIMICDiagnosis",       "diagnoses_icd.csv", "Condition extraction"],
            ["MIMICDiagnosisDict",   "d_icd_diagnoses.csv", "ICD-9/10 to description lookup"],
            ["MIMICProcedureDict",   "d_icd_procedures.csv", "Procedure description lookup"],
            ["MIMICPrescription",    "prescriptions.csv", "Medication extraction"],
            ["SyntheaPatient",       "patients.csv (Synthea)", "RealCSVProvider"],
            ["SyntheaCondition",     "conditions.csv",   "Active-condition filter (STOP is null)"],
            ["SyntheaMedication",    "medications.csv",  "Active-prescription filter"],
            ["SyntheaCarePlan",      "careplans.csv",    "Care-plan extraction"],
        ],
        col_widths=[2.0, 2.0, 2.4],
    )

    style_heading(doc, "data_simulator.py - Synthetic Generator", level=3)
    body_para(doc, "Role: Generates a procedurally varied cohort of PatientProfile objects with "
                   "matching synthetic EHR notes. Used by the evaluation harness when neither "
                   "Synthea nor MIMIC is available, and as the canonical structure for all real data.")
    make_table(
        doc, headers=["Method / Class", "What it produces"],
        rows=[
            ["PatientProfile",            "The canonical data class for one patient (age, gender, disease, biomarkers, etc.)."],
            ["SyntheticNoteGenerator.generate_note(profile)",
             "Turns a profile into a realistic free-text EHR note (used for benchmarking)."],
            ["build_synthetic_patients(n)",    "Creates n diverse profiles with random but realistic field combinations."],
            ["build_trial_criteria()",     "Returns the trial protocols used by the evaluation harness."],
            ["save_trials_json(...) / save_patients_json(...)", "Persists trial and patient JSON for reproducibility."],
        ],
        col_widths=[3.0, 3.4],
    )

    style_heading(doc, "mock_database.py - Synthea CSV Provider (RealCSVProvider)", level=3)
    body_para(doc, "Role: Loads Synthea synthetic patient CSVs from disk into memory. Despite the "
                   "filename containing 'mock', this provider reads real CSV files; the name "
                   "reflects the historical evolution of the project.")
    make_table(
        doc, headers=["Method", "Purpose"],
        rows=[
            ["RealCSVProvider.__init__(...)",     "Opens patients/conditions/medications/careplans CSVs, indexes them by patient_id."],
            ["_load_conditions / _medications / _careplans / _notes(path)",
             "Per-table loaders. Tolerate column-name variants via _resolve_column."],
            ["_enrich_profile_from_rows(pid, profile)",
             "Derives disease, comorbidities, prior therapies from CSV rows."],
            ["_profile_to_entities(p)",
             "Converts a profile into the entity dict the symbolic validator expects."],
            ["map_disease(description) (classmethod)",
             "Maps SNOMED descriptions to canonical EthiMatch disease codes."],
            ["get_patient(pid) / get_conditions / get_medications / get_pre_extracted",
             "Implements the PatientDataProvider contract."],
            ["select_patient_ids_for_screening(provider, max_patients, oncology_only)",
             "Bounded ID selector with an oncology filter, used by Cohort Discovery."],
            ["get_default_csv_provider(...)",   "Factory returning a default Synthea provider."],
        ],
        col_widths=[2.6, 3.8],
    )
    add_page_break(doc)
