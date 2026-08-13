"""Additional report sections to reach dissertation word count."""
from __future__ import annotations

CH4_EXTRA = [
    ("4.10 Repository and Component Organisation", (
        "The repository separates application code (ethimatch/), datasets "
        "(data/synthea and data/mimic), documentation (docs/), and tooling "
        "(tools/doc_builder). The public project source is available at "
        "https://github.com/Vrajpro/EthiMatch. Figure 10 shows the component map: data providers "
        "feed the pipeline; neural extraction and silver cache sit behind the "
        "orchestrator; the symbolic validator and trial registry own protocol logic; "
        "XAI and PDF export decorate audit outputs; Streamlit pages and the "
        "evaluation harness consume the same contracts."
        "\n\n"
        "Key modules include config.py, data_loader.py, neural_extractor.py, "
        "symbolic_validator.py, ethimatch_pipeline.py, xai_explainer.py, "
        "silver_cache.py, evaluation.py, and app.py. Later services/ and "
        "data_access/ packages keep UI code thin. An examiner can map Figure 10 "
        "to source folders without running the stack."
    )),
    ("4.11 Implementation Challenges and Solutions", (
        "Three challenges shaped the final design. First, CPU neural latency "
        "required silver-cache materialisation and structured early-exit. Second, "
        "a legacy MIMIC note loader silently substituted synthetic patients and "
        "was replaced with MIMICDualSourceProvider. Third, cache staleness after "
        "note-synthesis changes was fixed with SHA-256 hashing plus CACHE_VERSION. "
        "Each fix remains in the artefact."
    )),
    ("4.12 Chapter Summary", (
        "EthiMatch realises the neuro-symbolic framework as a modular Python "
        "artefact with clear layer contracts, JSON trial logic, design diagrams "
        "(Figures 2–5), UI screenshots (Figures 6–9), and a component map "
        "(Figure 10). The next chapter "
        "records how the project was managed."
    )),
]

CH5_EXTRA = []

CH6_EXTRA = []

CH7_EXTRA = [
    ("7.6 Data Protection and GDPR Considerations", (
        "Although no identifiable personal data were processed, the project adopted "
        "data-minimisation principles consistent with the Data Protection Act 2018: "
        "only eligibility fields are loaded, demo datasets are used, and no patient "
        "content was sent to external generative AI services. A production deployment "
        "would require information-governance review against ICO guidance on AI and "
        "data protection (Information Commissioner's Office, 2023), beyond the scope "
        "of this MSc prototype."
    )),
    ("7.7 Chapter Summary", (
        "Ethical design choices—synthetic/demo data, INCONCLUSIVE semantics, and human-in-the-loop "
        "positioning—align the artefact with responsible clinical AI research practice."
    )),
]

CH8_EXTRA = []
