"""Symbolic pathway — deterministic trial eligibility rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List

from config import (
    ALLOWED_DISEASES,
    ALLOWED_STAGES,
    BIOMARKERS,
    COMORBIDITIES,
    ECOG_LEVELS,
    ENTITY_FIELD_LABELS,
    GENDERS,
    PRIOR_THERAPIES,
    normalize_disease,
    normalize_gender,
    normalize_stage,
    sanitize_list_values,
    sanitize_trial_criteria,
)

class RuleVerdict(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    INCONCLUSIVE = "INCONCLUSIVE"
    SKIP = "SKIP"

@dataclass
class RuleResult:
    rule_name: str
    verdict: RuleVerdict
    explanation: str
    criterion: Any = None
    patient_val: Any = None
    rule_code: str = ""

@dataclass
class ValidationReport:
    trial_id: str
    trial_name: str
    eligible: bool
    has_warnings: bool
    rule_results: List[RuleResult] = field(default_factory=list)
    # Dual-source provenance: which cohort the patient came from.
    # Empty string preserves backwards compatibility with legacy call sites.
    data_source: str = ""

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.rule_results if r.verdict == RuleVerdict.PASS)

    @property
    def fail_count(self) -> int:
        return sum(1 for r in self.rule_results if r.verdict == RuleVerdict.FAIL)

    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.rule_results if r.verdict == RuleVerdict.WARNING)

    @property
    def inconclusive_count(self) -> int:
        return sum(1 for r in self.rule_results if r.verdict == RuleVerdict.INCONCLUSIVE)

    @property
    def total_rules(self) -> int:
        return len(self.rule_results)

    @property
    def is_conditionally_eligible(self) -> bool:
        return self.eligible and self.inconclusive_count > 0

    def to_dict(self) -> dict:
        return {
            "trial_id": self.trial_id,
            "trial_name": self.trial_name,
            "eligible": self.eligible,
            "has_warnings": self.has_warnings,
            "data_source": self.data_source,
            "rule_results": [
                {
                    "rule_name": r.rule_name,
                    "verdict": r.verdict.value,
                    "explanation": r.explanation,
                    "criterion": r.criterion,
                    "patient_val": r.patient_val,
                }
                for r in self.rule_results
            ],
        }

class SymbolicValidator:

    _BENCHMARK_TRIAL_IDS = frozenset({"BASE-002"})

    def validate(self, entities: dict, trial: Any) -> ValidationReport:
        
        if not isinstance(trial, dict):
            return ValidationReport(
                trial_id="UNKNOWN",
                trial_name="UNKNOWN",
                eligible=False,
                has_warnings=True,
                rule_results=[
                    RuleResult(
                        rule_name="Trial Integrity",
                        verdict=RuleVerdict.INCONCLUSIVE,
                        explanation="Invalid trial object supplied to validator.",
                        criterion="trial must be dict",
                        patient_val=type(trial).__name__,
                    )
                ],
            )

        inclusion = trial.get("inclusion")
        exclusion = trial.get("exclusion")

        if not isinstance(inclusion, dict):
            inclusion = {}
        if not isinstance(exclusion, dict):
            exclusion = {}

        trial = sanitize_trial_criteria({**trial, "inclusion": inclusion, "exclusion": exclusion})
        inclusion = trial["inclusion"]
        exclusion = trial["exclusion"]
        entities = self._normalize_entities(entities)

        results = [
            self._check_age(entities, inclusion),
            self._check_gender(entities, inclusion),
            self._check_disease(entities, inclusion),
            self._check_stage(entities, inclusion),
            self._check_required_biomarkers(entities, inclusion),
            self._check_ecog(entities, inclusion),
            self._check_bmi_max(entities, inclusion),
            self._check_excluded_comorbidities(entities, exclusion),
            self._check_excluded_therapies(entities, exclusion),
            self._check_bmi_min(entities, exclusion),
        ]
        results.extend(self._check_low_confidence_warnings(entities))

        has_fail = any(r.verdict == RuleVerdict.FAIL for r in results)
        has_soft = any(
            r.verdict in (RuleVerdict.WARNING, RuleVerdict.INCONCLUSIVE)
            for r in results
        )

        data_source = ""
        if isinstance(entities, dict):
            ds = entities.get("data_source")
            if isinstance(ds, str):
                data_source = ds
        return ValidationReport(
            trial_id=trial.get("trial_id", "UNKNOWN"),
            trial_name=trial.get("trial_name", "UNKNOWN"),
            eligible=not has_fail,
            has_warnings=has_soft,
            rule_results=results,
            data_source=data_source,
        )
    # Universal Safety Helpers
    def _get_val(self, entities: dict, key: str) -> Any:
        if not isinstance(entities, dict):
            return None
        val = entities.get(key)
        if isinstance(val, dict):
            val = val.get("value")
        if self._is_missing_scalar(key, val):
            return None
        return val

    @staticmethod
    def _is_missing_scalar(field: str, val: Any) -> bool:
        """Treat None, empty strings, 'Unknown', and invalid zeros as missing."""
        if val is None:
            return True
        if isinstance(val, str) and val.strip().lower() in ("", "unknown", "none", "nat"):
            return True
        # BMI of 0 is not clinically valid — treat as absent data
        if field == "bmi" and val in (0, 0.0):
            return True
        # Age of 0 indicates failed extraction / missing birthdate
        if field == "age" and val == 0:
            return True
        return False

    def _normalize_entities(self, entities: dict) -> dict:
        """Map extracted values to canonical config vocabularies."""
        if not isinstance(entities, dict):
            return entities
        out = dict(entities)

        disease = self._get_val(out, "disease")
        if disease is not None:
            normalized = normalize_disease(str(disease))
            if normalized:
                out["disease"] = normalized

        stage = self._get_val(out, "stage")
        if stage is not None:
            normalized = normalize_stage(str(stage))
            if normalized:
                out["stage"] = normalized

        gender = self._get_val(out, "gender")
        if gender is not None:
            normalized = normalize_gender(str(gender))
            if normalized:
                out["gender"] = normalized

        ecog = self._get_val(out, "ecog_ps")
        if ecog is not None and ecog not in ECOG_LEVELS:
            out["ecog_ps"] = None

        for list_key, allowed in (
            ("biomarkers", BIOMARKERS),
            ("comorbidities", COMORBIDITIES),
            ("prior_therapies", PRIOR_THERAPIES),
        ):
            raw = self._get_val(out, list_key)
            if isinstance(raw, list):
                out[list_key] = sanitize_list_values(raw, allowed)

        return out

    def _get_list(self, criteria: dict, key: str) -> list:
        if not isinstance(criteria, dict):
            return []
        val = criteria.get(key)
        return val if isinstance(val, list) else []

    # Rule Implementations
    def validate_all_trials(
        self,
        entities: dict,
        trials: list[Any],
    ) -> list[ValidationReport]:
        """Validate extracted entities against every trial in the registry."""
        reports: list[ValidationReport] = []
        for trial in trials:
            reports.append(self.validate(entities, trial))
        return sorted(reports, key=self._trial_rank_key)

    @staticmethod
    def _trial_rank_key(report: ValidationReport) -> tuple:
        """Eligible trials first; clinical protocols before benchmark controls."""
        ratio = report.pass_count / max(report.total_rules, 1)
        is_benchmark = report.trial_id in SymbolicValidator._BENCHMARK_TRIAL_IDS
        return (
            not report.eligible,
            is_benchmark,
            -ratio,
            -report.total_rules,
            report.trial_id,
        )

    @staticmethod
    def match_score(report: ValidationReport) -> float:
        """Compute a 0–100 eligibility score for ranked recommendations."""
        if report.total_rules == 0:
            return 0.0
        base = report.pass_count / report.total_rules * 100
        if not report.eligible:
            fail_penalty = report.fail_count * 20
            return round(max(0.0, min(100.0, base - fail_penalty)), 1)
        penalty = report.inconclusive_count * 5 + report.warning_count * 2
        return round(max(0.0, min(100.0, base - penalty)), 1)

    @classmethod
    def best_trial_report(cls, reports: list[ValidationReport]) -> ValidationReport | None:
        """Pick the trial report clinicians should see first (eligible before blocked)."""
        if not reports:
            return None
        return min(reports, key=cls._trial_rank_key)

    def _check_low_confidence_warnings(
        self, entities: dict,
    ) -> list[RuleResult]:
        """Flag low-confidence extractions as WARNING (not hard FAIL).

        Missing data is handled per-rule as INCONCLUSIVE.
        Low confidence means data exists but neural extraction is uncertain.
        """
        conf = entities.get("confidence_scores", {}) if isinstance(entities, dict) else {}
        field_labels = ENTITY_FIELD_LABELS
        warnings: list[RuleResult] = []
        threshold = 0.70

        for key, label in field_labels.items():
            val = self._get_val(entities, key)
            if val in (None, []):
                continue
            score = conf.get(key)
            if isinstance(score, (int, float)) and score < threshold:
                src = entities.get("extraction_sources", {}).get(key, "ner")
                if src == "gold" or src == "regex":
                    continue
                warnings.append(RuleResult(
                    rule_name=f"{label} (Confidence)",
                    verdict=RuleVerdict.WARNING,
                    explanation=(
                        f"{label} extracted with low confidence ({score:.0%}). "
                        "Manual verification recommended."
                    ),
                    criterion=f">= {threshold:.0%} confidence",
                    patient_val=val,
                    rule_code="low_confidence_warning",
                ))
        return warnings

    def _check_age(self, e: dict, inc: Any) -> RuleResult:
        if not isinstance(inc, dict):
            return RuleResult(
                rule_name="Age",
                verdict=RuleVerdict.SKIP,
                explanation="No age criteria provided.",
            )

        age = self._get_val(e, "age")
        age_min = inc.get("age_min")
        age_max = inc.get("age_max")

        if age is None:
            return RuleResult(
                rule_name="Age",
                verdict=RuleVerdict.INCONCLUSIVE,
                explanation="Patient age missing.",
                criterion=f"{age_min}–{age_max}",
                patient_val=None,
                rule_code="age_missing",
            )

        if age_min is not None and age < age_min:
            return RuleResult(
                rule_name="Age",
                verdict=RuleVerdict.FAIL,
                explanation=f"Age {age} below minimum {age_min}.",
                criterion=f"≥ {age_min}",
                patient_val=age,
                rule_code="age_below_min",
            )

        if age_max is not None and age > age_max:
            return RuleResult(
                rule_name="Age",
                verdict=RuleVerdict.FAIL,
                explanation=f"Age {age} exceeds maximum {age_max}.",
                criterion=f"≤ {age_max}",
                patient_val=age,
                rule_code="age_above_max",
            )

        return RuleResult(
            rule_name="Age",
            verdict=RuleVerdict.PASS,
            explanation="Age criteria satisfied.",
            criterion=f"{age_min}–{age_max}",
            patient_val=age,
            rule_code="age_pass",
        )

    def _check_gender(self, e, inc) -> RuleResult:
        allowed = self._get_list(inc, "gender")
        val = self._get_val(e, "gender")

        if not allowed:
            return RuleResult("Gender", RuleVerdict.PASS, "No gender restriction.")

        if val is None:
            return RuleResult("Gender", RuleVerdict.INCONCLUSIVE, "Gender missing.")

        ok = str(val).lower() in [str(a).lower() for a in allowed]
        return RuleResult(
            "Gender",
            RuleVerdict.PASS if ok else RuleVerdict.FAIL,
            f"Gender {val} {'allowed' if ok else 'not allowed'}.",
            allowed,
            val,
        )

    def _check_disease(self, e, inc) -> RuleResult:
        allowed = self._get_list(inc, "diseases")
        val = self._get_val(e, "disease")

        if not allowed:
            return RuleResult("Disease", RuleVerdict.PASS, "No disease restriction.")

        if val is None:
            return RuleResult("Disease", RuleVerdict.INCONCLUSIVE, "Disease missing.",
                              allowed, None, rule_code="disease_missing")

        if val not in ALLOWED_DISEASES:
            return RuleResult(
                "Disease",
                RuleVerdict.INCONCLUSIVE,
                f"Disease '{val}' is not a recognised trial disease code.",
                allowed,
                val,
                rule_code="disease_unrecognised",
            )

        ok = val in allowed
        return RuleResult(
            "Disease",
            RuleVerdict.PASS if ok else RuleVerdict.FAIL,
            f"Disease {val} {'eligible' if ok else 'not eligible'}.",
            allowed,
            val,
            rule_code="disease_pass" if ok else "disease_fail",
        )

    def _check_stage(self, e, inc) -> RuleResult:
        allowed = self._get_list(inc, "stages")
        val = self._get_val(e, "stage")

        if not allowed:
            return RuleResult("Stage", RuleVerdict.PASS, "No stage restriction.")

        if val is None:
            return RuleResult("Stage", RuleVerdict.INCONCLUSIVE, "Stage missing.",
                              allowed, None, rule_code="stage_missing")

        if val not in ALLOWED_STAGES:
            return RuleResult(
                "Stage",
                RuleVerdict.INCONCLUSIVE,
                f"Stage '{val}' is not a recognised cancer stage.",
                allowed,
                val,
                rule_code="stage_unrecognised",
            )

        ok = val in allowed
        return RuleResult(
            "Stage",
            RuleVerdict.PASS if ok else RuleVerdict.FAIL,
            f"Stage {val} {'eligible' if ok else 'not eligible'}.",
            allowed,
            val,
        )

    def _check_required_biomarkers(self, e, inc) -> RuleResult:
        required = self._get_list(inc, "required_biomarkers")
        patient = self._get_val(e, "biomarkers") or []

        if not required:
            return RuleResult("Biomarkers", RuleVerdict.PASS, "No biomarker requirement.")

        if not patient:
            return RuleResult(
                "Biomarkers",
                RuleVerdict.INCONCLUSIVE,
                "Biomarkers missing.",
                required,
                None,
            )

        missing = [b for b in required if b not in patient]
        if missing:
            return RuleResult(
                "Biomarkers",
                RuleVerdict.FAIL,
                f"Missing required biomarkers: {', '.join(missing)}.",
                required,
                patient,
            )

        return RuleResult("Biomarkers", RuleVerdict.PASS, "All required biomarkers present.", required, patient)

    def _check_ecog(self, e, inc) -> RuleResult:
        max_ecog = inc.get("ecog_max") if isinstance(inc, dict) else None
        val = self._get_val(e, "ecog_ps")

        if max_ecog is None:
            return RuleResult("ECOG", RuleVerdict.PASS, "No ECOG restriction.")

        if val is None:
            return RuleResult("ECOG", RuleVerdict.INCONCLUSIVE, "ECOG missing.",
                              f"<= {max_ecog}", None, rule_code="ecog_missing")

        if val not in ECOG_LEVELS:
            return RuleResult(
                "ECOG",
                RuleVerdict.INCONCLUSIVE,
                f"ECOG value {val} is outside recognised range {ECOG_LEVELS}.",
                f"≤ {max_ecog}",
                val,
                rule_code="ecog_unrecognised",
            )

        if val > max_ecog:
            return RuleResult(
                "ECOG",
                RuleVerdict.FAIL,
                f"ECOG {val} exceeds limit {max_ecog}.",
                f"≤ {max_ecog}",
                val,
                rule_code="ecog_fail",
            )

        return RuleResult("ECOG", RuleVerdict.PASS, "ECOG criteria satisfied.", f"≤ {max_ecog}", val)

    def _check_bmi_max(self, e, inc) -> RuleResult:
        bmi_max = inc.get("bmi_max") if isinstance(inc, dict) else None
        val = self._get_val(e, "bmi")

        if bmi_max is None:
            return RuleResult("BMI (Max)", RuleVerdict.PASS, "No BMI upper limit.")

        if val is None:
            return RuleResult("BMI (Max)", RuleVerdict.INCONCLUSIVE, "BMI missing.",
                              f"<= {bmi_max}", None, rule_code="bmi_max_missing")

        if val > bmi_max:
            return RuleResult(
                "BMI (Max)",
                RuleVerdict.FAIL,
                f"BMI {val} exceeds maximum {bmi_max}.",
                f"≤ {bmi_max}",
                val,
                rule_code="bmi_max_fail",
            )

        return RuleResult("BMI (Max)", RuleVerdict.PASS, "BMI within limit.", f"≤ {bmi_max}", val)

    def _check_bmi_min(self, e, exc) -> RuleResult:
        bmi_min = exc.get("bmi_min") if isinstance(exc, dict) else None
        val = self._get_val(e, "bmi")

        if bmi_min is None:
            return RuleResult("BMI (Min)", RuleVerdict.PASS, "No BMI lower limit.")

        if val is None:
            return RuleResult("BMI (Min)", RuleVerdict.INCONCLUSIVE, "BMI missing.",
                              f"≥ {bmi_min}", None, rule_code="bmi_min_missing")

        if val < bmi_min:
            return RuleResult(
                "BMI (Min)",
                RuleVerdict.FAIL,
                f"BMI {val} below minimum {bmi_min}.",
                f"≥ {bmi_min}",
                val,
            )

        return RuleResult("BMI (Min)", RuleVerdict.PASS, "BMI above minimum.", f"≥ {bmi_min}", val)

    def _check_excluded_comorbidities(self, e, exc) -> RuleResult:
        excluded = self._get_list(exc, "excluded_comorbidities")
        patient = self._get_val(e, "comorbidities") or []

        if not excluded:
            return RuleResult("Comorbidities", RuleVerdict.PASS, "No excluded comorbidities.")

        hit = [c for c in patient if c in excluded]
        if hit:
            return RuleResult(
                "Comorbidities",
                RuleVerdict.FAIL,
                f"Excluded comorbidities present: {', '.join(hit)}.",
                excluded,
                patient,
            )

        return RuleResult("Comorbidities", RuleVerdict.PASS, "No excluded comorbidities detected.", excluded, patient)

    def _check_excluded_therapies(self, e, exc) -> RuleResult:
        excluded = self._get_list(exc, "excluded_prior_therapies")
        patient = self._get_val(e, "prior_therapies") or []

        if not excluded:
            return RuleResult("Prior Therapies", RuleVerdict.PASS, "No excluded therapies.")

        hit = [t for t in patient if t in excluded]
        if hit:
            return RuleResult(
                "Prior Therapies",
                RuleVerdict.FAIL,
                f"Excluded therapies present: {', '.join(hit)}.",
                excluded,
                patient,
            )

        return RuleResult("Prior Therapies", RuleVerdict.PASS, "No excluded therapies detected.", excluded, patient)
