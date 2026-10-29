# Tables for the paper

Keep each table as **both** a CSV (source of truth) and a Markdown rendering (for drafting).

## Planned tables

### Table 1 — Main synthetic benchmark

- Source: `ethimatch/results/comparative_benchmark.json`
- Columns: Metric, EthiMatch, Pure-neural baseline, Δ
- Rows: F1, Precision, Recall, FPR
- Save as: `table1_main_benchmark.csv` + `table1_main_benchmark.md`

### Table 2 — Cross-source summary

- Source: `ethimatch/results/thesis/final_benchmark_table.md`
- Columns: Dataset, System, F1, Precision, FPR, *n*
- Rows: Synthea × {EthiMatch, baseline}, MIMIC-IV Demo × {EthiMatch, baseline}
- Save as: `table2_cross_source.csv` + `table2_cross_source.md`

### Table 3 — Error taxonomy

- Built during Results drafting; sample ~20 discordant patients.
- Columns: Error type, Count (EthiMatch), Count (baseline), Example trial
- Rows: FP, FN, INCONCLUSIVE, correct ELIGIBLE, correct INELIGIBLE
- Save as: `table3_error_taxonomy.csv` + `table3_error_taxonomy.md`

## Rule

Every number in a table must be traceable to a file in `ethimatch/results/`. If you cannot cite the source file, do not put the number in the table.
