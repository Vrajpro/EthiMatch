"""
EthiMatch — automated system QA (run: python scripts/qa_system_check.py)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILURES: list[str] = []

def ok(name: str) -> None:
    print(f"  PASS  {name}")

def fail(name: str, detail: str) -> None:
    print(f"  FAIL  {name}: {detail}")
    FAILURES.append(f"{name}: {detail}")

def check(name: str, fn) -> None:
    try:
        fn()
        ok(name)
    except Exception as exc:
        fail(name, str(exc))

def main() -> int:
    print("EthiMatch System QA\n" + "=" * 48)

    print("\n[1] Module imports")
    for mod in (
        "config",
        "schemas",
        "data_loader",
        "trial_registry",
        "symbolic_validator",
        "mock_database",
        "ethimatch_pipeline",
        "evaluation",
        "xai_explainer",
        "ui.theme",
        "ui.components",
        "ui.pages",
        "app",
    ):
        check(f"import {mod}", lambda m=mod: __import__(m))

    from config import DEFAULT_CSV_DIR, theme_token, THEME
    from trial_registry import load_all_trials
    from data_simulator import build_trial_criteria
    from mock_database import get_default_csv_provider
    from symbolic_validator import SymbolicValidator, RuleVerdict, ValidationReport
    from ethimatch_pipeline import try_structured_early_exit, MatchingPatientResult, AuditReport
    from ui.components import (
        primary_validation_report,
        matching_registry_verdict,
        matching_verdict_label,
        build_evaluation_comparison_figure,
    )
    from ui.theme import get_theme_css

    print("\n[2] Configuration & registry")
    check("CSV directory exists", lambda: DEFAULT_CSV_DIR.is_dir())
    check("THEME has PASS/FAIL", lambda: "PASS" in THEME and "FAIL" in THEME)
    check("theme_token Eligible", lambda: theme_token("Eligible") == "PASS")
    check("trials load", lambda: len(load_all_trials()) >= 1)

    print("\n[3] Symbolic validator logic")
    v = SymbolicValidator()
    trials = build_trial_criteria()

    def _report(trial_id: str, *, eligible: bool, passes: int, fails: int, inconc: int = 0) -> ValidationReport:
        results = []
        for i in range(passes):
            results.append(
                type("R", (), {"verdict": RuleVerdict.PASS})()
            )
        for i in range(fails):
            results.append(
                type("R", (), {"verdict": RuleVerdict.FAIL})()
            )
        for i in range(inconc):
            results.append(
                type("R", (), {"verdict": RuleVerdict.INCONCLUSIVE})()
            )
        from symbolic_validator import RuleResult

        rule_results = []
        for i in range(passes):
            rule_results.append(
                RuleResult(rule_name=f"p{i}", verdict=RuleVerdict.PASS, explanation="ok")
            )
        for i in range(fails):
            rule_results.append(
                RuleResult(rule_name=f"f{i}", verdict=RuleVerdict.FAIL, explanation="no")
            )
        for i in range(inconc):
            rule_results.append(
                RuleResult(
                    rule_name=f"i{i}",
                    verdict=RuleVerdict.INCONCLUSIVE,
                    explanation="?",
                )
            )
        return ValidationReport(
            trial_id=trial_id,
            trial_name=trial_id,
            eligible=eligible,
            has_warnings=inconc > 0,
            rule_results=rule_results,
        )

    blocked = _report("T-BLOCK", eligible=False, passes=4, fails=1)
    eligible_r = _report("T-OK", eligible=True, passes=3, fails=0, inconc=2)
    best = SymbolicValidator.best_trial_report([blocked, eligible_r])
    check(
        "best_trial_report prefers eligible trial",
        lambda: best is not None and best.trial_id == "T-OK",
    )
    check(
        "ineligible match_score below eligible with same pass ratio",
        lambda: SymbolicValidator.match_score(blocked)
        < SymbolicValidator.match_score(eligible_r),
    )

    pre = {
        "age": 55,
        "disease": "NSCLC",
        "stage": "IIIA",
        "ecog_ps": 1,
        "bmi": 24,
        "biomarkers": ["EGFR+"],
        "comorbidities": [],
        "prior_therapies": [],
    }
    skip, reports, _ = try_structured_early_exit(pre, v, trials)
    check("structured early exit", lambda: skip and reports is not None)

    print("\n[4] CSV data layer")
    provider = get_default_csv_provider(limit=5)
    ids = provider.list_patient_ids()
    check("CSV patients load", lambda: len(ids) > 0)

    def _comorbidity_sane() -> None:
        p = provider.get_patient(ids[0])
        if p.disease and p.comorbidities:
            for c in p.comorbidities:
                mapped = provider.map_disease(c)
                if mapped == p.disease:
                    raise AssertionError(
                        f"Primary disease {p.disease!r} duplicated in comorbidities"
                    )

    check("comorbidities exclude primary malignancy", _comorbidity_sane)

    print("\n[5] UI / charts / theme")
    check(
        "2D evaluation chart builds",
        lambda: build_evaluation_comparison_figure(
            {"precision": 0.8, "recall": 0.7, "fpr": 0.1, "f1": 0.75},
            {"precision": 0.6, "recall": 0.5, "fpr": 0.2, "f1": 0.55},
        ),
    )
    css = get_theme_css()
    check("sidebar white text in theme", lambda: "#FFFFFF" in css and "stSidebar" in css)

    def _registry_verdict_consistent() -> None:
        audit = AuditReport(
            timestamp="2026-01-01T00:00:00",
            raw_note="test",
            extracted_entities={},
            trial_reports=[eligible_r, blocked],
            patient_id="TEST",
        )
        label, _, _ = matching_registry_verdict(audit)
        primary = primary_validation_report(audit)
        assert primary is not None
        assert label == matching_verdict_label(primary)

    check("matching registry verdict matches detail label", _registry_verdict_consistent)

    print("\n[6] Dual-source data loader")
    from data_loader import (
        DATA_SOURCE_LABELS,
        MIMICDualSourceProvider,
        SyntheaDualSourceProvider,
        load_provider,
        normalise_source,
    )

    check(
        "DATA_SOURCE_LABELS keys are MIMIC + Synthea",
        lambda: set(DATA_SOURCE_LABELS) == {"MIMIC", "Synthea"},
    )
    check(
        "normalise_source coerces loose strings",
        lambda: normalise_source("mimic-iv demo") == "MIMIC"
        and normalise_source("synthea") == "Synthea"
        and normalise_source(None) == "Synthea",
    )

    def _synthea_factory() -> None:
        prov = load_provider("Synthea", limit=3)
        assert isinstance(prov, SyntheaDualSourceProvider), type(prov)
        patients = prov.get_all_patients()
        assert patients, "Synthea factory returned zero patients"
        sample = patients[0]
        assert sample.data_source == "Synthea"
        assert isinstance(sample.active_conditions, list)
        assert isinstance(sample.medications, list)

    check("factory[Synthea] → unified PatientProfile", _synthea_factory)

    if MIMICDualSourceProvider.is_available():
        def _mimic_factory() -> None:
            prov = load_provider("MIMIC", limit=3)
            assert isinstance(prov, MIMICDualSourceProvider), type(prov)
            patients = prov.get_all_patients()
            assert patients, "MIMIC factory returned zero patients"
            sample = patients[0]
            assert sample.data_source == "MIMIC"
            assert sample.patient_id.startswith("MIMIC-")
            assert isinstance(sample.active_conditions, list)
            assert isinstance(sample.medications, list)

        check("factory[MIMIC] → unified PatientProfile", _mimic_factory)

        def _mimic_validator_propagates_source() -> None:
            prov = load_provider("MIMIC", limit=1)
            pid = prov.list_patient_ids()[0]
            entities = dict(prov.get_pre_extracted(pid) or {})
            entities.setdefault("data_source", "MIMIC")
            reports = v.validate_all_trials(entities, trials)
            assert reports, "validator returned no reports for MIMIC entities"
            assert any(r.data_source == "MIMIC" for r in reports), (
                "ValidationReport did not carry MIMIC data_source"
            )

        check("ValidationReport propagates MIMIC data_source", _mimic_validator_propagates_source)
    else:
        print("  SKIP  MIMIC factory checks (data/mimic/ not found)")

    print("\n[7] Symbolic engine — new JSON trials (ONC-001 + BASE-002)")
    from trial_registry import load_all_trials

    registered = load_all_trials()
    registered_ids = {t["trial_id"] for t in registered}
    check(
        "ONC-001 loaded from trials/",
        lambda: "ONC-001" in registered_ids,
    )
    check(
        "BASE-002 loaded from trials/",
        lambda: "BASE-002" in registered_ids,
    )

    onc_trial = next(t for t in registered if t["trial_id"] == "ONC-001")
    base_trial = next(t for t in registered if t["trial_id"] == "BASE-002")

    def _onc_rejects_diabetic_with_fentanyl() -> None:
        entities = {
            "age": 62, "gender": "male", "disease": "NSCLC",
            "comorbidities": ["diabetes"],
            "prior_therapies": ["fentanyl"],
            "data_source": "Synthea",
        }
        report = v.validate(entities, onc_trial)
        assert not report.eligible, "ONC-001 should FAIL for diabetes + fentanyl"
        rule_codes = {r.rule_name for r in report.rule_results}
        assert "Comorbidities" in rule_codes and "Prior Therapies" in rule_codes
        fails = {r.rule_name for r in report.rule_results
                 if r.verdict == RuleVerdict.FAIL}
        assert {"Comorbidities", "Prior Therapies"} <= fails, fails

    check(
        "ONC-001 rejects NSCLC patient with diabetes + fentanyl",
        _onc_rejects_diabetic_with_fentanyl,
    )

    def _onc_accepts_clean_nsclc() -> None:
        entities = {
            "age": 62, "gender": "male", "disease": "NSCLC",
            "comorbidities": [],
            "prior_therapies": [],
            "data_source": "Synthea",
        }
        report = v.validate(entities, onc_trial)
        assert report.eligible, (
            "ONC-001 should accept a clean 62yo NSCLC patient — got "
            f"{[(r.rule_name, r.verdict.value) for r in report.rule_results]}"
        )

    check("ONC-001 accepts clean NSCLC patient (age 62)", _onc_accepts_clean_nsclc)

    def _base_accepts_any_adult() -> None:
        entities = {"age": 30, "gender": "female", "data_source": "MIMIC"}
        report = v.validate(entities, base_trial)
        assert report.eligible, "BASE-002 should accept any adult"

    check("BASE-002 accepts any adult", _base_accepts_any_adult)

    print("\n[8] Mock clinical note generation")
    from data_loader import generate_mock_clinical_note
    from data_simulator import PatientProfile

    def _mock_note_contains_phenotype() -> None:
        p = PatientProfile(
            patient_id="DEMO-1",
            age=65, gender="male",
            disease="NSCLC",
            active_conditions=["Non-small cell lung cancer", "hypertension"],
            medications=["Paclitaxel", "Carboplatin"],
            data_source="Synthea",
        )
        note = generate_mock_clinical_note(p)
        assert "65-year-old male" in note, note
        assert "NSCLC" in note, note
        assert "Paclitaxel" in note, note
        assert "no history of" in note.lower(), note

    check("mock note contains demographics + meds + negation", _mock_note_contains_phenotype)

    def _mock_note_stamped_by_loader() -> None:
        prov = load_provider("Synthea", limit=3)
        sample = next(
            (p for p in prov.get_all_patients() if p.ehr_note), None,
        )
        assert sample is not None, "Synthea loader did not stamp any ehr_note"
        assert "Patient is" in sample.ehr_note, sample.ehr_note[:120]

    check("Synthea loader stamps ehr_note on profile", _mock_note_stamped_by_loader)

    print("\n[9] Evaluation (synthetic, no BioBERT notes)")
    from evaluation import run_comparative_benchmark

    def _synthetic_benchmark() -> None:
        result = run_comparative_benchmark(
            data_source="synthetic", n_patients=8, seed=99,
        )
        if result.get("error"):
            raise RuntimeError(result["error"])
        if result["n_patients"] < 1:
            raise AssertionError("benchmark returned zero patients")
        if "neuro_symbolic" not in result or "pure_neural" not in result:
            raise AssertionError("missing metric keys")

    check("synthetic comparative benchmark (small)", _synthetic_benchmark)

    print("\n" + "=" * 48)
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s)")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("ALL CHECKS PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
