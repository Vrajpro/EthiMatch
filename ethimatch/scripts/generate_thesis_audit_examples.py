"""Generate thesis Clinical Audit examples — one INCONCLUSIVE, one INELIGIBLE."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data_simulator import build_trial_criteria
from config import DEFAULT_CSV_DIR
from mock_database import get_default_csv_provider
from neural_extractor import NeuralExtractor
from symbolic_validator import RuleVerdict, SymbolicValidator
from xai_explainer import (
    build_clinical_narrative,
    build_full_audit_narrative,
    explain_rule,
)

OUT = ROOT / "results" / "thesis_clinical_audit_examples.txt"

def main() -> None:
    provider = get_default_csv_provider(limit=50)
    extractor = NeuralExtractor(device=-1, verbose=False)
    validator = SymbolicValidator()
    trial = build_trial_criteria()[0]
    trial_id = trial["trial_id"]

    cases = [
        ("INCONCLUSIVE", "P001"),
        ("INELIGIBLE", "P002"),
    ]

    lines: list[str] = []
    lines.append("EthiMatch — Clinical Audit Examples (7005SCN Dissertation)")
    lines.append("=" * 72)

    for verdict_type, pid in cases:
        note = provider.get_patient_note(pid) or ""
        entities = extractor.extract(note, silent=True).to_dict()
        report = validator.validate(entities, trial)
        conditions = [c.description for c in provider.get_conditions(pid)]

        lines.append("")
        lines.append(f"EXAMPLE: {verdict_type}")
        lines.append(f"Patient ID     : {pid}")
        lines.append(f"Trial          : {trial_id} — {trial['trial_name']}")
        lines.append(f"System verdict : {verdict_type}")
        lines.append(f"Active conditions (STOP=null): {', '.join(conditions)}")
        lines.append("-" * 72)
        lines.append("")
        lines.append("CLINICAL NARRATIVE (XAI Layer)")
        lines.append(build_clinical_narrative(report, entities).replace("**", ""))
        lines.append("")
        lines.append("RULE-BY-RULE AUDIT TRACE")
        for rule in report.rule_results:
            tag = rule.verdict.value
            lines.append(f"  [{tag:14s}] {rule.rule_name}: {explain_rule(rule)}")
        lines.append("")
        lines.append("FULL AUDIT REPORT")
        lines.append(build_full_audit_narrative(note, entities, [report]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written to {OUT}")

if __name__ == "__main__":
    main()
