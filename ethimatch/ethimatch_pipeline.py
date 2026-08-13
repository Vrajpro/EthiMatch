"""Pipeline orchestrator: extract, validate, explain."""

from __future__ import annotations

import json
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from data_simulator import PatientProfile
from trial_registry import load_all_trials, trials_for_export
from data_access.interfaces import PatientDataProvider
from console import safe_print, to_json_safe
from neural_extractor import NeuralExtractor, ExtractedEntities
from symbolic_validator import (
    SymbolicValidator,
    ValidationReport,
    RuleVerdict,
)
from silver_cache import compute_input_hash, load_silver_entities
from xai_explainer import (
    build_executive_summary,
    build_full_audit_narrative,
)

# Structured CSV / PatientProfile fields that must stay aligned with patient_id.
_PROFILE_ENTITY_FIELDS = (
    "age", "gender", "disease", "stage", "bmi", "ecog_ps",
    "biomarkers", "comorbidities", "prior_therapies",
)

def reconcile_entities_with_profile(
    entities: dict[str, Any],
    profile: PatientProfile,
) -> dict[str, Any]:
    """Align extracted entities with structured profile demographics."""
    out = dict(entities)
    sources = dict(out.get("extraction_sources") or {})
    conf = dict(out.get("confidence_scores") or {})

    for field in _PROFILE_ENTITY_FIELDS:
        val = getattr(profile, field, None)
        source_tag = "quick_entry" if profile.patient_id == "QUICK-ENTRY" else "csv_profile"
        if field in ("biomarkers", "comorbidities", "prior_therapies"):
            if val:
                out[field] = list(val)
                sources[field] = source_tag
                conf[field] = 1.0
            continue
        if val is None or val == "" or val == 0:
            continue
        out[field] = val
        sources[field] = source_tag
        conf[field] = 1.0

    out["extraction_sources"] = sources
    out["confidence_scores"] = conf
    out["patient_id"] = profile.patient_id
    return out

def try_structured_early_exit(
    pre_extracted: dict[str, Any] | None,
    validator: SymbolicValidator,
    trials: list[dict[str, Any]],
) -> tuple[bool, list[ValidationReport] | None, str]:
    """Skip BioBERT when structured CSV fields already hard-fail every trial.

    Returns ``(skip_neural, trial_reports, reason)``.  Neural extraction is
    still run when any trial is eligible/conditional, or when disqualification
    is due to missing data (INCONCLUSIVE-only) that notes might resolve.
    """
    if not pre_extracted:
        return False, None, ""

    reports = validator.validate_all_trials(pre_extracted, trials)

    if any(r.eligible for r in reports):
        return False, None, ""

    if not reports:
        return False, None, ""

    if all(r.fail_count > 0 for r in reports):
        return True, reports, "structured_hard_fail_all_trials"

    return False, None, ""

@dataclass
class AuditReport:
    """Immutable record of a complete EthiMatch pipeline run.

    ``trial_reports`` holds ``ValidationReport`` objects — the standard
    contract passed from SymbolicValidator to XAIExplainer.
    """
    timestamp:          str
    raw_note:           str
    extracted_entities: dict[str, Any]
    trial_reports:      list[ValidationReport]
    pipeline_version:   str = "1.0.0"
    patient_id:         Optional[str] = None
    xai_narrative:      str = ""
    executive_summary:  dict[str, Any] = field(default_factory=dict)
    # Dual-source provenance (propagated to XAI narrative + UI badges).
    data_source:        str = ""

    def format_for_doctor(self) -> str:
        """Render clinician-friendly audit report via XAI narrative layer."""
        if self.xai_narrative:
            return self.xai_narrative
        return build_full_audit_narrative(
            self.raw_note,
            self.extracted_entities,
            self.trial_reports,
        )

    def format_for_doctor_legacy(self) -> str:
        """Legacy box-drawing audit report (kept for reference)."""
        lines: list[str] = []

        lines.append("")
        lines.append("╔" + "═" * 62 + "╗")
        lines.append("║   ETHIMATCH — CLINICAL TRIAL MATCHING AUDIT REPORT" +
                      " " * 10 + "║")
        lines.append("╚" + "═" * 62 + "╝")
        lines.append(f"  Generated : {self.timestamp}")
        lines.append(f"  Pipeline  : v{self.pipeline_version}")
        lines.append("")

        lines.append("┌─── §A. INPUT CLINICAL NOTE " + "─" * 34 + "┐")
        wrapped = textwrap.fill(self.raw_note, width=60, initial_indent="│ ",
                                subsequent_indent="│ ")
        lines.append(wrapped)
        lines.append("└" + "─" * 62 + "┘")
        lines.append("")

        lines.append("┌─── §B. NEURAL EXTRACTION RESULTS " + "─" * 27 + "┐")
        for key, val in self.extracted_entities.items():
            status = "" if val not in (None, []) else "️  MISSING"
            lines.append(f"│  {key:20s}: {str(val):30s} {status}")
        lines.append("└" + "─" * 62 + "┘")
        lines.append("")

        lines.append("┌─── §C. SYMBOLIC VALIDATION RESULTS " + "─" * 25 + "┐")
        for report in self.trial_reports:
            lines.append("│")
            lines.append(f"│  ▸ {report.trial_name}")
            lines.append(f"│    Trial ID: {report.trial_id}")

            for rule in report.rule_results:
                icon = {
                    RuleVerdict.PASS:         "",
                    RuleVerdict.FAIL:         "",
                    RuleVerdict.WARNING:      "️ ",
                    RuleVerdict.INCONCLUSIVE: "❓",
                    RuleVerdict.SKIP:         "⏭️ ",
                }[rule.verdict]
                lines.append(f"│    {icon} {rule.rule_name}: "
                             f"{rule.explanation}")

            # Verdict
            if not report.eligible:
                lines.append(f"│    ╔══ VERDICT:  NOT ELIGIBLE ══╗")
            elif report.is_conditionally_eligible:
                lines.append(f"│    ╔══ VERDICT: ❓ CONDITIONALLY ELIGIBLE "
                             f"({report.inconclusive_count} inconclusive) ══╗")
            elif report.has_warnings:
                lines.append(f"│    ╔══ VERDICT:  ELIGIBLE (with warnings) ══╗")
            else:
                lines.append(f"│    ╔══ VERDICT:  ELIGIBLE ══╗")

            lines.append(f"│    ║  Rules: {report.pass_count} passed, "
                          f"{report.fail_count} failed, "
                          f"{report.inconclusive_count} inconclusive, "
                          f"{report.warning_count} warnings")
            lines.append(f"│    ╚{'═' * 40}╝")

        lines.append("│")
        lines.append("└" + "─" * 62 + "┘")

        lines.append("")
        lines.append("┌─── §D. MATCHING SUMMARY " + "─" * 37 + "┐")
        eligible_trials = [r for r in self.trial_reports if r.eligible]
        lines.append(f"│  Eligible for {len(eligible_trials)} of "
                      f"{len(self.trial_reports)} trial(s):")
        for r in self.trial_reports:
            marker = "" if r.eligible else ""
            lines.append(f"│    {marker}  {r.trial_id} — {r.trial_name}")
        lines.append("└" + "─" * 62 + "┘")
        lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serialise the full report for JSON archival."""
        return to_json_safe({
            "timestamp": self.timestamp,
            "pipeline_version": self.pipeline_version,
            "raw_note": self.raw_note,
            "extracted_entities": self.extracted_entities,
            "trial_reports": [
                {
                    "trial_id": r.trial_id,
                    "trial_name": r.trial_name,
                    "eligible": r.eligible,
                    "has_warnings": r.has_warnings,
                    "rules": [
                        {
                            "rule_name": rule.rule_name,
                            "verdict": rule.verdict.value,
                            "explanation": rule.explanation,
                            "criterion": str(rule.criterion),
                            "patient_value": str(rule.patient_val),
                        }
                        for rule in r.rule_results
                    ],
                }
                for r in self.trial_reports
            ],
        })

@dataclass
class CohortResult:
    """Result of cohort discovery for a single patient.

    Used by run_cohort_search() to package per-patient eligibility
    with full audit trails for the Cohort Discovery UI.
    """
    patient_id:          str
    patient_profile:     Optional[PatientProfile]
    extracted_entities:  dict[str, Any]
    trial_reports:       list[ValidationReport]
    is_eligible:         bool
    is_conditional:      bool   = False
    fail_reasons:        list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialise for JSON export."""
        profile_dict = None
        if self.patient_profile:
            profile_dict = {
                "patient_id": self.patient_profile.patient_id,
                "age": self.patient_profile.age,
                "gender": self.patient_profile.gender,
                "disease": self.patient_profile.disease,
                "stage": self.patient_profile.stage,
                "biomarkers": self.patient_profile.biomarkers,
                "bmi": self.patient_profile.bmi,
                "ecog_ps": self.patient_profile.ecog_ps,
                "comorbidities": self.patient_profile.comorbidities,
                "prior_therapies": self.patient_profile.prior_therapies,
            }
        primary = self.trial_reports[0] if self.trial_reports else None
        failed_rule_names: list[str] = []
        primary_match_score = 0.0
        if primary:
            primary_match_score = SymbolicValidator.match_score(primary)
            failed_rule_names = [
                r.rule_name for r in primary.rule_results if r.verdict == RuleVerdict.FAIL
            ]
        return to_json_safe({
            "patient_id": self.patient_id,
            "patient_profile": profile_dict,
            "is_eligible": self.is_eligible,
            "is_conditional": self.is_conditional,
            "fail_reasons": self.fail_reasons,
            "match_score": primary_match_score,
            "failed_rule_names": failed_rule_names,
            "confidence_scores": dict(self.extracted_entities.get("confidence_scores") or {}),
            "trial_reports": [
                {
                    "trial_id": r.trial_id,
                    "trial_name": r.trial_name,
                    "eligible": r.eligible,
                    "has_warnings": r.has_warnings,
                    "rules": [
                        {
                            "rule_name": rule.rule_name,
                            "verdict": rule.verdict.value,
                            "explanation": rule.explanation,
                        }
                        for rule in r.rule_results
                    ],
                }
                for r in self.trial_reports
            ],
        })

@dataclass
class MatchingPatientResult:
    """Patient Matching master-detail row — full BioBERT audit cached in session."""
    patient_id: str
    audit_report: AuditReport
    patient_profile: Optional[PatientProfile] = None

    @property
    def primary_trial_report(self) -> Optional[ValidationReport]:
        return SymbolicValidator.best_trial_report(self.audit_report.trial_reports)

class EthiMatchPipeline:
    

    def __init__(
        self,
        model_name: str = "d4data/biomedical-ner-all",
        device: int = -1,
        trials: Optional[list[dict[str, Any]]] = None,
        data_provider: Optional[PatientDataProvider] = None,
        verbose: bool = True,
    ) -> None:
        self.verbose = verbose
        self.data_provider = data_provider
        if verbose:
            safe_print("\n" + "=" * 64)
            safe_print("  EthiMatch Pipeline — Initialising")
            safe_print("=" * 64)

        self.extractor = NeuralExtractor(
            model_name=model_name, device=device, verbose=verbose,
        )
        self.validator = SymbolicValidator()
        self.trials = trials or trials_for_export(load_all_trials())

        if verbose:
            src = data_provider.source_name() if data_provider else "none (note-only mode)"
            safe_print(f"[Pipeline] Data provider: {src}")
            safe_print(f"[Pipeline] Ready. {len(self.trials)} trial(s) loaded.\n")

    
    def extract_entities(
        self,
        note: str,
        silent: bool | None = None,
        patient_id: str | None = None,
    ) -> dict[str, Any]:
        quiet = silent if silent is not None else not self.verbose

        if patient_id:
            cached = load_silver_entities(
                patient_id, expected_hash=compute_input_hash(note),
            )
            if cached is not None:
                if not quiet:
                    safe_print(f"[Pipeline] Silver cache hit for {patient_id}")
                out = dict(cached)
                out.setdefault("extraction_sources", {})
                out["extraction_sources"]["_pipeline"] = "silver"
                return out

        entities_obj: ExtractedEntities = self.extractor.extract(
            note, silent=quiet,
        )
        return entities_obj.to_dict()

    def _resolve_patient_entities_and_reports(
        self,
        patient_id: str,
        note: str,
        provider: PatientDataProvider,
        quiet: bool,
        force_neural: bool = False,
    ) -> tuple[dict[str, Any], list[ValidationReport], str]:
        """Silver cache → (optional) structured early exit → BioBERT NER.

        ``force_neural=True`` disables the structured early-exit fast path so
        BioBERT actively ingests the synthesised ``ehr_note`` rather than
        reusing the CSV-derived structured phenotype. The silver cache still
        applies — first call runs BioBERT, subsequent calls hit cache.
        """
        pre_extracted: dict[str, Any] | None = None
        if hasattr(provider, "get_pre_extracted"):
            pre_extracted = provider.get_pre_extracted(patient_id) or {}

        # Pick up cohort provenance once; stamped into every entities dict so
        # the validator and downstream XAI layer can cite the source dataset.
        data_source = self._provider_data_source(provider, pre_extracted)

        cached = load_silver_entities(
            patient_id, expected_hash=compute_input_hash(note),
        )
        if cached is not None:
            if not quiet:
                safe_print(f"[Pipeline] Silver cache hit for {patient_id}")
            entities = dict(cached)
            entities.setdefault("extraction_sources", {})
            entities["extraction_sources"]["_pipeline"] = "silver"
            self._stamp_data_source(entities, data_source)
            return entities, self.validate_entities(entities), "silver"

        if not force_neural:
            skip, early_reports, reason = try_structured_early_exit(
                pre_extracted, self.validator, self.trials,
            )
            if skip and early_reports is not None and pre_extracted is not None:
                if not quiet:
                    safe_print(
                        f"[Pipeline] Early exit (structured CSV) for {patient_id}: {reason}"
                    )
                entities = dict(pre_extracted)
                entities.setdefault("extraction_sources", {})
                entities["extraction_sources"]["_pipeline"] = f"early_exit:{reason}"
                self._stamp_data_source(entities, data_source)
                # Re-validate so the report carries the freshly-stamped data_source.
                return entities, self.validate_entities(entities), f"early_exit:{reason}"

        if not quiet:
            n_chars = len(note or "")
            safe_print(
                f"[Pipeline] >> Neuro-Symbolic handoff: feeding BioBERT a "
                f"{n_chars}-char synthesised note for {patient_id} "
                f"(data_source={data_source or 'unknown'}, "
                f"force_neural={force_neural})"
            )
        entities = self.extract_entities(note, silent=quiet, patient_id=patient_id)
        entities.setdefault("extraction_sources", {})
        entities["extraction_sources"]["_pipeline"] = "neural"
        self._stamp_data_source(entities, data_source)
        if not quiet:
            extracted_disease = entities.get("disease")
            extracted_meds = entities.get("prior_therapies") or []
            extracted_comorb = entities.get("comorbidities") or []
            safe_print(
                f"[Pipeline] << BioBERT extracted: "
                f"disease={extracted_disease!r}, "
                f"medications={extracted_meds}, "
                f"comorbidities={extracted_comorb}"
            )
        return entities, self.validate_entities(entities), "neural"

    @staticmethod
    def _provider_data_source(
        provider: PatientDataProvider,
        pre_extracted: dict[str, Any] | None,
    ) -> str:
        """Resolve provenance: provider attribute → pre-extracted hint → blank."""
        candidate = getattr(provider, "data_source", "")
        if isinstance(candidate, str) and candidate:
            return candidate
        if isinstance(pre_extracted, dict):
            ds = pre_extracted.get("data_source")
            if isinstance(ds, str) and ds:
                return ds
        return ""

    @staticmethod
    def _stamp_data_source(entities: dict[str, Any], data_source: str) -> None:
        if not data_source:
            return
        # Don't clobber an existing provenance tag (e.g. silver cache from MIMIC).
        if not entities.get("data_source"):
            entities["data_source"] = data_source

    def validate_entities(
        self, entities: dict[str, Any],
    ) -> list[ValidationReport]:
        """Run SymbolicValidator — returns ValidationReport contract objects."""
        return self.validator.validate_all_trials(entities, self.trials)

    def explain_reports(
        self,
        trial_reports: list[ValidationReport],
        entities: dict[str, Any],
        raw_note: str,
    ) -> str:
        """XAIExplainer layer — consumes ValidationReport objects only."""
        return build_full_audit_narrative(raw_note, entities, trial_reports)

    def _build_audit_report(
        self,
        raw_note: str,
        entities: dict[str, Any],
        trial_reports: list[ValidationReport],
        patient_id: Optional[str] = None,
    ) -> AuditReport:
        narrative = self.explain_reports(trial_reports, entities, raw_note)
        data_source = ""
        if isinstance(entities, dict):
            ds = entities.get("data_source")
            if isinstance(ds, str):
                data_source = ds
        return AuditReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            raw_note=raw_note,
            extracted_entities=entities,
            trial_reports=trial_reports,
            patient_id=patient_id,
            xai_narrative=narrative,
            executive_summary=build_executive_summary(trial_reports, entities),
            data_source=data_source,
        )

    def run(self, note: str, silent: bool | None = None,
            patient_id: Optional[str] = None) -> AuditReport:
        """Execute the full pipeline on a raw clinical note."""
        quiet = silent if silent is not None else not self.verbose
        if not quiet:
            safe_print("\n" + "#" * 64)
            safe_print("  EthiMatch Pipeline — Processing Note")
            safe_print("#" * 64)
            safe_print("\n  STEP 1: Neural Extraction (BioBERT + Regex)")

        entities = self.extract_entities(note, silent=quiet, patient_id=patient_id)

        if not quiet:
            safe_print("  STEP 2: Symbolic Validation (Rule Engine)")
        trial_reports = self.validate_entities(entities)

        if not quiet:
            safe_print("  STEP 3: XAI Explanation (ValidationReport → narrative)")
        return self._build_audit_report(note, entities, trial_reports, patient_id)

    def run_patient(
        self,
        patient_id: str,
        data_provider: Optional[PatientDataProvider] = None,
        silent: bool | None = None,
        force_neural: bool = True,
    ) -> AuditReport:
        """Run pipeline for one patient via PatientDataProvider ingestion.

        Loads patient demographics, active conditions, and medications
        through the abstract interface — never reads CSVs directly.

        ``force_neural`` defaults to ``True`` here so single-patient calls
        (Patient Matching detail view) always exercise the BioBERT NER pass
        on the synthesised ``ehr_note``. Bulk cohort screening continues to
        use the structured fast path via ``run_cohort_search``.
        """
        provider = data_provider or self.data_provider
        if provider is None:
            raise ValueError(
                "A PatientDataProvider is required. Pass data_provider to "
                "EthiMatchPipeline(...) or run_patient(...)."
            )

        patient = provider.get_patient(patient_id)
        if patient is None:
            raise KeyError(f"Patient '{patient_id}' not found in {provider.source_name()}")

        conditions = provider.get_conditions(patient_id)
        medications = provider.get_medications(patient_id)
        # Prefer the synthesised ehr_note stamped by data_loader; fall back to
        # provider's composed note for legacy backends that don't populate it.
        note = (patient.ehr_note or "").strip() or provider.get_patient_note(patient_id)
        if not note:
            raise ValueError(f"No clinical note available for patient '{patient_id}'.")

        quiet = silent if silent is not None else not self.verbose
        if not quiet:
            note_origin = (
                "synthesised (data_loader)"
                if patient.ehr_note and patient.ehr_note.strip()
                else "provider composed"
            )
            safe_print(
                f"\n[Pipeline] Patient {patient_id}: "
                f"{len(conditions)} active condition(s), "
                f"{len(medications)} medication(s), "
                f"note_origin={note_origin}"
            )

        entities, trial_reports, path_label = self._resolve_patient_entities_and_reports(
            patient_id, note, provider, quiet, force_neural=force_neural,
        )
        entities = reconcile_entities_with_profile(entities, patient)
        trial_reports = self.validate_entities(entities)

        if not quiet:
            safe_print(f"  Extraction path: {path_label}")
            n_elig = sum(1 for r in trial_reports if r.eligible)
            n_block = len(trial_reports) - n_elig
            safe_print(
                f"  STEP 3: XAI Explanation — symbolic verdict: "
                f"{n_elig} eligible / {n_block} blocked across {len(trial_reports)} trial(s)"
            )

        report = self._build_audit_report(note, entities, trial_reports, patient_id)
        report.extracted_entities.setdefault("provider_conditions", [
            c.to_dict() for c in conditions
        ])
        report.extracted_entities.setdefault("provider_medications", [
            m.to_dict() for m in medications
        ])
        return report

    def run_batch(
        self, notes: list[str],
    ) -> list[AuditReport]:
        """Process multiple notes sequentially."""
        return [self.run(note) for note in notes]

    def run_batch_patients(
        self,
        patient_ids: list[str] | None = None,
        data_provider: Optional[PatientDataProvider] = None,
        silent: bool = True,
    ) -> list[AuditReport]:
        """Process multiple patients from a PatientDataProvider."""
        provider = data_provider or self.data_provider
        if provider is None:
            raise ValueError("PatientDataProvider required for run_batch_patients().")
        ids = patient_ids or provider.list_patient_ids()
        return [self.run_patient(pid, provider, silent=silent) for pid in ids]

    def run_cohort_search(
        self,
        data_provider: PatientDataProvider,
        trial: dict[str, Any],
    ) -> list[CohortResult]:
        """Run Trial-Centric cohort discovery via PatientDataProvider."""
        if self.verbose:
            safe_print(f"\n[Pipeline] Cohort Search: {trial['trial_id']}")

        patients = data_provider.get_all_patients()
        if hasattr(data_provider, "get_all_pre_extracted"):
            pre_extracted = data_provider.get_all_pre_extracted()
        else:
            pre_extracted = {}
        results: list[CohortResult] = []

        for patient in patients:
            pid = patient.patient_id
            entities = pre_extracted.get(pid, {})

            if not entities and hasattr(data_provider, "get_pre_extracted"):
                entities = data_provider.get_pre_extracted(pid) or {}

            # ValidationReport is the validator → downstream contract
            report: ValidationReport = self.validator.validate(entities, trial)

            is_eligible = report.eligible and not report.is_conditionally_eligible
            is_conditional = report.eligible and report.is_conditionally_eligible

            fail_reasons = [
                rule.explanation
                for rule in report.rule_results
                if rule.verdict == RuleVerdict.FAIL
            ]

            results.append(CohortResult(
                patient_id=pid,
                patient_profile=(
                    patient
                    if patient.patient_id == pid
                    else data_provider.get_patient(pid)
                ),
                extracted_entities=entities,
                trial_reports=[report],
                is_eligible=is_eligible,
                is_conditional=is_conditional,
                fail_reasons=fail_reasons,
            ))

        results.sort(key=lambda r: (not r.is_eligible, not r.is_conditional))

        n_elig = sum(1 for r in results if r.is_eligible)
        n_cond = sum(1 for r in results if r.is_conditional)
        n_fail = sum(1 for r in results if not r.is_eligible and not r.is_conditional)
        if self.verbose:
            safe_print(
                f"[Pipeline] Cohort: {n_elig} eligible, "
                f"{n_cond} conditional, {n_fail} ineligible"
            )

        return results

def main() -> None:
    """Run the complete EthiMatch pipeline on patients from local CSV files."""
    from mock_database import get_default_csv_provider

    provider = get_default_csv_provider(limit=8, verbose=False)
    pipeline = EthiMatchPipeline(data_provider=provider, verbose=True)

    all_reports: list[AuditReport] = []
    for pid in provider.list_patient_ids():
        report = pipeline.run_patient(pid)
        all_reports.append(report)
        print(report.format_for_doctor())

    print("\n" + "█" * 64)
    print("  EthiMatch — BATCH PROCESSING SUMMARY")
    print("█" * 64)
    print(f"  Patients processed : {len(all_reports)}")
    print(f"  Trials evaluated   : {len(pipeline.trials)}")
    print()

    for report in all_reports:
        eligible_ids = [r.trial_id for r in report.trial_reports if r.eligible]
        status = (
            f"Eligible for: {', '.join(eligible_ids)}"
            if eligible_ids else "No eligible trials"
        )
        print(f"  {report.patient_id}: {status}")

    print(f"\n   Pipeline run complete.\n")

if __name__ == "__main__":
    main()
