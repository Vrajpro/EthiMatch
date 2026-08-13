# Data folders

| Folder | Contents |
|--------|----------|
| `synthea/` | Synthea synthetic patient CSVs used by EthiMatch |
| `mimic/` | MIMIC-IV Demo structured tables (public demo subset) |

Core tracked Synthea files include `patients.csv`, `conditions.csv`, `medications.csv`, `careplans.csv`, and `encounters.csv`.

Very large Synthea exports (`claims.csv`, `claims_transactions.csv`, `observations.csv`, `imaging_studies.csv`) are kept locally when available but are not published on GitHub because of file-size limits. The Streamlit app runs with the core CSVs above.
