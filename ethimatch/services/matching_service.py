"""Patient Matching backend — Quick Entry, batch filter, screening, export."""

from __future__ import annotations

from typing import Any, Callable

from config import disease_code_from_display, disease_filter_variants, disease_label_for_code
from data_simulator import PatientProfile
from ethimatch_pipeline import AuditReport, EthiMatchPipeline, MatchingPatientResult, reconcile_entities_with_profile
from data_access.csv_factory import select_patient_ids_for_screening
from xai_explainer import build_executive_summary

def compose_quick_entry_note(fields: dict[str, Any]) -> str:
    age = int(fields.get("qe_age", 55))
    gender = str(fields.get("qe_gender", "male"))
    disease = disease_code_from_display(str(fields.get("qe_disease", ""))) or str(fields.get("qe_disease", ""))
    stage = str(fields.get("qe_stage", "IIIA"))
    biomarkers = list(fields.get("qe_bio", []))
    bmi = float(fields.get("qe_bmi", 25.0))
    ecog = int(fields.get("qe_ecog", 1))
    comorb = list(fields.get("qe_comorb", []))
    therapies = list(fields.get("qe_rx", []))
    deny_diabetes = bool(fields.get("qe_neg"))

    parts = [f"Patient is a {age}-year-old {gender} diagnosed with Stage {stage} {disease}."]
    if biomarkers:
        parts.append(f"Molecular testing shows {', '.join(biomarkers)}.")
    parts.append(f"BMI is {bmi}. ECOG performance status {ecog}.")
    if deny_diabetes:
        parts.append("Patient denies diabetes.")
    elif comorb:
        parts.append(f"Medical history includes {', '.join(comorb)}.")
    else:
        parts.append("No significant comorbidities.")
    if therapies:
        parts.append(f"Prior therapies include {', '.join(therapies)}.")
    return " ".join(parts)

def build_quick_entry_profile(fields: dict[str, Any]) -> PatientProfile:
    disease = disease_code_from_display(str(fields.get("qe_disease", "")))
    comorb = list(fields.get("qe_comorb", []))
    if fields.get("qe_neg"):
        comorb = []
    return PatientProfile(
        patient_id="QUICK-ENTRY",
        age=int(fields.get("qe_age", 55)),
        gender=str(fields.get("qe_gender", "male")),
        disease=disease,
        stage=str(fields.get("qe_stage", "")),
        biomarkers=list(fields.get("qe_bio", [])),
        bmi=float(fields.get("qe_bmi", 25.0)),
        ecog_ps=int(fields.get("qe_ecog", 1)),
        comorbidities=comorb,
        prior_therapies=list(fields.get("qe_rx", [])),
        data_source="QuickEntry",
    )

def finalize_audit_with_profile(
    pipeline: EthiMatchPipeline,
    report: AuditReport,
    profile: PatientProfile,
) -> AuditReport:
    entities = reconcile_entities_with_profile(dict(report.extracted_entities or {}), profile)
    trial_reports = pipeline.validate_entities(entities)
    report.extracted_entities = entities
    report.trial_reports = trial_reports
    report.patient_id = profile.patient_id
    report.xai_narrative = pipeline.explain_reports(trial_reports, entities, report.raw_note)
    report.executive_summary = build_executive_summary(trial_reports, entities)
    return report

def extraction_path_label(report: AuditReport) -> str:
    sources = (report.extracted_entities or {}).get("extraction_sources") or {}
    path = str(sources.get("_pipeline", "neural"))
    if path == "silver":
        return "silver"
    if path.startswith("early_exit"):
        return "early_exit"
    return "neural"

def resolve_batch_filter(
    mode: str,
    qe_disease_label: str | None,
    picked_disease_label: str | None = None,
) -> tuple[bool, list[str] | None, str, bool]:
    """Return (oncology_only, disease_codes, filter_label, can_run)."""
    disease_codes: list[str] | None = None
    oncology_only = False
    filter_label = ""
    can_run = True
    qe_code = disease_code_from_display(str(qe_disease_label)) if qe_disease_label else None

    if mode == "oncology_any":
        oncology_only = True
        filter_label = "any oncology"
    elif mode == "quick_entry_disease":
        if not qe_code:
            can_run = False
            filter_label = "Quick Entry disease (not set)"
        else:
            disease_codes = sorted(disease_filter_variants(qe_code))
            filter_label = f"{disease_label_for_code(qe_code)} (disease only)"
    elif mode == "pick_disease":
        code = disease_code_from_display(str(picked_disease_label or ""))
        if code:
            disease_codes = sorted(disease_filter_variants(code))
            filter_label = disease_label_for_code(code)
        else:
            can_run = False
            filter_label = "specific disease (invalid)"
    else:
        filter_label = "all loaded patients"

    return oncology_only, disease_codes, filter_label, can_run

def run_quick_entry_screening(
    pipeline: EthiMatchPipeline,
    note: str,
    profile: PatientProfile,
) -> MatchingPatientResult:
    report = pipeline.run(note, silent=True, patient_id="QUICK-ENTRY")
    report = finalize_audit_with_profile(pipeline, report, profile)
    return MatchingPatientResult(
        patient_id="QUICK-ENTRY",
        audit_report=report,
        patient_profile=profile,
    )

def run_csv_batch_screening(
    pipeline: EthiMatchPipeline,
    provider: Any,
    *,
    batch_size: int,
    oncology_only: bool,
    disease_codes: list[str] | None,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> tuple[list[MatchingPatientResult], dict[str, int]]:
    ids = select_patient_ids_for_screening(
        provider,
        max_patients=batch_size,
        oncology_only=oncology_only,
        disease_codes=disease_codes,
    )
    if not ids:
        return [], {"silver": 0, "early_exit": 0, "neural": 0}

    reports: list[AuditReport] = []
    for i, pid in enumerate(ids):
        if progress_callback is not None:
            progress_callback(i + 1, len(ids), pid)
        reports.append(pipeline.run_patient(pid, data_provider=provider, silent=True))

    path_counts = {"silver": 0, "early_exit": 0, "neural": 0}
    for report in reports:
        path_counts[extraction_path_label(report)] += 1

    results = [
        MatchingPatientResult(
            patient_id=pid,
            audit_report=report,
            patient_profile=provider.get_patient(pid),
        )
        for pid, report in zip(ids, reports)
    ]
    for row in results:
        if row.patient_profile is not None:
            row.audit_report = finalize_audit_with_profile(pipeline, row.audit_report, row.patient_profile)
    return results, path_counts

def sort_matching_results(
    results: list[MatchingPatientResult],
    verdict_fn: Callable[[AuditReport], tuple[str, str, float]],
    sort_order_fn: Callable[[str], int],
) -> list[MatchingPatientResult]:
    return sorted(
        results,
        key=lambda r: (
            sort_order_fn(verdict_fn(r.audit_report)[0]),
            -verdict_fn(r.audit_report)[2],
        ),
    )

def build_matching_export_data(
    results: list[MatchingPatientResult],
    data_source: str,
    verdict_fn: Callable[[AuditReport], tuple[str, str, float]],
) -> dict[str, Any]:
    eligible = inconclusive = blocked = 0
    rows: list[dict[str, Any]] = []
    for r in results:
        verdict, _, score = verdict_fn(r.audit_report)
        if verdict == "Eligible":
            eligible += 1
        elif verdict in ("Inconclusive", "Conditional"):
            inconclusive += 1
        else:
            blocked += 1

        profile_dict = None
        if r.patient_profile is not None:
            prof = r.patient_profile
            profile_dict = {
                "patient_id": prof.patient_id,
                "age": prof.age,
                "gender": prof.gender,
                "disease": prof.disease,
                "stage": prof.stage,
                "bmi": prof.bmi,
                "ecog_ps": prof.ecog_ps,
            }

        rows.append({
            "patient_id": r.patient_id,
            "verdict": verdict,
            "match_score": score,
            "patient_profile": profile_dict,
            "audit_report": r.audit_report.to_dict(),
        })

    return {
        "data_source": data_source,
        "summary": {
            "eligible": eligible,
            "inconclusive": inconclusive,
            "blocked": blocked,
            "total": len(results),
        },
        "results": rows,
    }
