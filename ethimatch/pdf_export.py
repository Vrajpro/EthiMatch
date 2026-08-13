"""PDF export for EthiMatch audit and cohort reports."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from fpdf import FPDF

from ethimatch_pipeline import AuditReport
from symbolic_validator import SymbolicValidator
from xai_explainer import build_clinical_narrative, ENTITY_LABELS

_LIST_TRUNCATE_DEFAULT = 12

def _clean(text: str | None) -> str:
    """Make text safe for core PDF fonts and normalise whitespace."""
    if text is None:
        return ""
    text = str(text)
    text = text.replace("\u2014", "-").replace("\u2013", "-").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.encode("latin-1", errors="replace").decode("latin-1")

def _fmt_scalar(value: Any) -> str:
    """Format a single value for PDF key-value lines (0 and False are valid)."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)
    if isinstance(value, list):
        return _fmt_list(value)
    text = str(value).strip()
    return text if text else "-"

def _fmt_list(values: Any, *, max_items: int | None = None) -> str:
    """Format a list for PDF body text; optionally truncate very long clinical lists."""
    if values is None:
        return "-"
    if not isinstance(values, list):
        return _fmt_scalar(values)
    items = [str(v).strip() for v in values if v is not None and str(v).strip()]
    if not items:
        return "-"
    limit = max_items if max_items is not None else _LIST_TRUNCATE_DEFAULT
    if len(items) > limit:
        head = ", ".join(items[:limit])
        return f"{head} ... (+{len(items) - limit} more)"
    return ", ".join(items)

def _fmt_entity_value(key: str, val: Any) -> str:
    """Format extracted entity values; truncate noisy long lists in PDF."""
    if isinstance(val, list):
        if key in ("comorbidities", "prior_therapies"):
            return _fmt_list(val, max_items=10)
        return _fmt_list(val, max_items=_LIST_TRUNCATE_DEFAULT)
    if val is None or (isinstance(val, str) and not val.strip()):
        return "MISSING"
    return str(val)

class _AuditPDF(FPDF):
    line_h = 4.2
    section_gap = 0.8
    block_gap = 0.4

    def __init__(self) -> None:
        super().__init__()
        self.set_margins(14, 12, 14)
        self.set_auto_page_break(auto=True, margin=14)

    def _content_w(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def _reset_to_top(self) -> None:
        """Cursor must be reset after watermark rotation (rotation leaves Y mid-page)."""
        self.set_xy(self.l_margin, self.t_margin)

    def _draw_watermark(self) -> None:
        """Diagonal brand watermark — visible but behind body content."""
        cx = self.w / 2
        cy = self.h / 2
        self.set_font("Helvetica", "B", 40)
        # Brand teal, light enough for watermark but clearly readable
        self.set_text_color(140, 180, 205)
        with self.rotation(40, x=cx, y=cy):
            self.set_xy(cx - 36, cy - 5)
            self.cell(72, 10, "EthiMatch", align="C", border=0)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(165, 195, 215)
        with self.rotation(40, x=cx, y=cy):
            self.set_xy(cx - 36, cy + 5)
            self.cell(72, 5, "Neuro-Symbolic XAI", align="C", border=0)

    def header(self) -> None:
        self._draw_watermark()
        self._reset_to_top()
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(12, 74, 110)
        self.cell(0, 6, "EthiMatch - Clinical Trial Matching Report", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(100, 116, 139)
        self.cell(
            0,
            4,
            "Neuro-Symbolic XAI | Research Prototype | Not for clinical use",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.set_draw_color(226, 232, 240)
        y = self.get_y() + 0.5
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(1)

    def footer(self) -> None:
        self.set_y(-10)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(148, 163, 184)
        self.cell(0, 6, f"EthiMatch | Page {self.page_no()}", align="C")

    def _ensure_space(self, height: float) -> None:
        if self.get_y() + height > self.h - self.b_margin:
            self.add_page()

    def section_title(self, title: str, *, first: bool = False) -> None:
        self._ensure_space(9)
        if not first:
            self.ln(self.section_gap)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(15, 23, 42)
        self.multi_cell(self._content_w(), 5, _clean(title), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(226, 232, 240)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(self.block_gap)

    def body_text(
        self,
        text: str,
        *,
        size: int = 9,
        style: str = "",
        spacing_after: float | None = None,
    ) -> None:
        gap = self.block_gap if spacing_after is None else spacing_after
        self._ensure_space(6)
        self.set_font("Helvetica", style, size)
        self.set_text_color(71, 85, 105)
        self.multi_cell(self._content_w(), self.line_h, _clean(text), new_x="LMARGIN", new_y="NEXT")
        if gap > 0:
            self.ln(gap)

    def kv_line(self, label: str, value: Any) -> None:
        self.body_text(f"{label}: {_fmt_scalar(value)}", spacing_after=0.15)

    def patient_block_title(self, title: str) -> None:
        self._ensure_space(8)
        self.ln(0.3)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(15, 23, 42)
        self.set_fill_color(241, 245, 249)
        self.multi_cell(self._content_w(), 5, _clean(title), new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(0.25)

def _pdf_output_to_bytes(pdf: FPDF) -> bytes:
    raw = pdf.output()
    if isinstance(raw, bytearray):
        return bytes(raw)
    if isinstance(raw, bytes):
        return raw
    return str(raw).encode("latin-1")

def _write_criteria_summary(pdf: _AuditPDF, criteria: dict[str, Any]) -> None:
    pdf.section_title("Search Criteria")
    registered = criteria.get("registered_trial")
    if registered:
        pdf.kv_line("Protocol", f"{registered.get('trial_name')} ({registered.get('trial_id')})")
        inc = registered.get("inclusion") or {}
        excl = registered.get("exclusion") or {}
    else:
        pdf.kv_line("Protocol", "Custom cohort search (USER-001)")
        inc = {
            "age_min": criteria.get("age_min"),
            "age_max": criteria.get("age_max"),
            "gender": criteria.get("gender"),
            "diseases": criteria.get("diseases"),
            "stages": criteria.get("stages"),
            "ecog_max": criteria.get("ecog_max"),
            "bmi_max": criteria.get("bmi_max"),
            "required_biomarkers": criteria.get("required_biomarkers"),
        }
        excl = {
            "excluded_comorbidities": criteria.get("excluded_comorbidities"),
            "excluded_prior_therapies": criteria.get("excluded_prior_therapies"),
        }

    age_min, age_max = inc.get("age_min"), inc.get("age_max")
    if age_min is not None and age_max is not None:
        pdf.kv_line("Age", f"{age_min}-{age_max}")
    gender = inc.get("gender")
    pdf.kv_line("Gender", gender if gender else "any")
    diseases = inc.get("diseases")
    pdf.kv_line("Diseases", diseases if diseases else "any")
    stages = inc.get("stages")
    pdf.kv_line("Stages", stages if stages else "any")
    if inc.get("ecog_max") is not None:
        pdf.kv_line("ECOG max", inc.get("ecog_max"))
    if inc.get("bmi_max") is not None:
        pdf.kv_line("BMI max", inc.get("bmi_max"))
    biomarkers = inc.get("required_biomarkers")
    pdf.kv_line("Required biomarkers", biomarkers if biomarkers else "-")
    comorb = excl.get("excluded_comorbidities")
    pdf.kv_line("Excluded comorbidities", comorb if comorb else "None")
    therapies = excl.get("excluded_prior_therapies")
    pdf.kv_line("Excluded prior therapies", therapies if therapies else "None")

def _write_cohort_patient(pdf: _AuditPDF, row: dict[str, Any], index: int) -> None:
    pid = str(row.get("patient_id", "UNKNOWN"))
    status = "ELIGIBLE" if row.get("is_eligible") else (
        "CONDITIONAL" if row.get("is_conditional") else "INELIGIBLE"
    )
    profile = row.get("patient_profile") or {}
    score = row.get("match_score")
    score_txt = f" | Match {score:.1f}%" if isinstance(score, (int, float)) else ""

    pdf.patient_block_title(f"{index}. {status}{score_txt}")
    pdf.kv_line("Patient ID", pid)
    pdf.kv_line("Age", profile.get("age"))
    pdf.kv_line("Gender", profile.get("gender"))
    pdf.kv_line("Disease", profile.get("disease"))
    pdf.kv_line("Stage", profile.get("stage"))
    pdf.kv_line("ECOG", profile.get("ecog_ps"))
    pdf.kv_line("BMI", profile.get("bmi"))

    failed_rules = row.get("failed_rule_names") or []
    if failed_rules:
        pdf.kv_line("Failed rules", failed_rules)

    fail_reasons = row.get("fail_reasons") or []
    if fail_reasons:
        pdf.body_text("Fail reasons:", style="B", size=8)
        for reason in fail_reasons:
            pdf.body_text(f"- {reason}", size=8)

    conf = row.get("confidence_scores") or {}
    if isinstance(conf, dict) and conf:
        parts = []
        for key in ("age", "gender", "disease", "stage", "bmi", "ecog_ps"):
            val = conf.get(key)
            if isinstance(val, (int, float)):
                parts.append(f"{key}={val:.0%}")
        if parts:
            pdf.body_text("Extraction confidence: " + ", ".join(parts), size=8, style="I", spacing_after=0.3)

    pdf.ln(0.5)

def _write_audit_report_body(
    pdf: _AuditPDF,
    report: AuditReport,
    *,
    include_meta: bool = True,
) -> None:
    """Render full audit sections (note, entities, trials, summary) into an open PDF."""
    if include_meta:
        pdf.body_text(f"Generated: {report.timestamp}", size=8, spacing_after=0.15)
        pdf.body_text(f"Pipeline version: {report.pipeline_version}", size=8, spacing_after=0.15)
        pdf.body_text(f"Patient ID: {report.patient_id or '-'}", size=8, spacing_after=0.3)

    pdf.section_title("A. Input Clinical Note", first=not include_meta)
    pdf.body_text(report.raw_note or "(no note)")

    pdf.section_title("B. Neural Extraction Results")
    entities = report.extracted_entities or {}
    conf = entities.get("confidence_scores") or {}
    for key, label in ENTITY_LABELS.items():
        val = entities.get(key)
        display = _fmt_entity_value(key, val)
        score = conf.get(key)
        score_txt = f" (conf: {score:.0%})" if isinstance(score, (int, float)) else ""
        pdf.body_text(f"{label}: {display}{score_txt}")

    if entities.get("negated_fields"):
        pdf.body_text("Negation filter: " + _fmt_list(entities["negated_fields"]))

    pdf.section_title("C. Symbolic Validation and Trial Recommendations")
    for tr in report.trial_reports:
        score = SymbolicValidator.match_score(tr)
        verdict = "ELIGIBLE" if tr.eligible else "NOT ELIGIBLE"
        if tr.is_conditionally_eligible:
            verdict = "CONDITIONAL"

        pdf.patient_block_title(f"{tr.trial_id} - {tr.trial_name}")
        pdf.body_text(
            f"Match score: {score:.1f}% | Verdict: {verdict} | "
            f"Passed: {tr.pass_count} | Failed: {tr.fail_count} | "
            f"Pending: {tr.inconclusive_count}",
            size=8,
        )

        narrative = build_clinical_narrative(tr, entities)
        pdf.body_text(narrative, size=8, style="I")

        for rule in tr.rule_results:
            pdf.body_text(
                f"[{rule.verdict.value}] {rule.rule_name}: {rule.explanation}",
                size=8,
                spacing_after=0.1,
            )
        pdf.ln(0.3)

    pdf.section_title("D. Summary")
    eligible = sum(1 for r in report.trial_reports if r.eligible)
    pdf.body_text(f"Patient eligible for {eligible} of {len(report.trial_reports)} registered trial(s).")
    pdf.body_text(
        "This report was generated by the EthiMatch neuro-symbolic pipeline. "
        "All recommendations require clinician review before clinical action.",
    )

def audit_report_to_pdf(report: AuditReport) -> bytes:
    """Build a clinician-readable PDF audit report for one patient."""
    pdf = _AuditPDF()
    pdf.add_page()
    _write_audit_report_body(pdf, report, include_meta=True)
    return _pdf_output_to_bytes(pdf)

def matching_batch_report_to_pdf(
    data: dict[str, Any],
    reports: list[AuditReport],
) -> bytes:
    """Build a PDF for Patient Matching — single full audit or multi-patient batch."""
    if not reports:
        pdf = _AuditPDF()
        pdf.add_page()
        pdf.body_text("No patients in this export.")
        return _pdf_output_to_bytes(pdf)

    if len(reports) == 1:
        return audit_report_to_pdf(reports[0])

    pdf = _AuditPDF()
    pdf.add_page()
    pdf.body_text(
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        size=8,
        spacing_after=0.3,
    )

    summary = data.get("summary") or {}
    pdf.section_title("Patient Matching Batch Summary", first=True)
    pdf.kv_line("Data source", data.get("data_source", "-"))
    pdf.kv_line("Eligible", summary.get("eligible", 0))
    pdf.kv_line("Inconclusive", summary.get("inconclusive", 0))
    pdf.kv_line("Blocked", summary.get("blocked", 0))
    pdf.kv_line("Total screened", summary.get("total", len(reports)))

    result_rows = data.get("results") or []
    for idx, report in enumerate(reports, start=1):
        row = result_rows[idx - 1] if idx - 1 < len(result_rows) else {}
        verdict = row.get("verdict", "-")
        score = row.get("match_score")
        score_txt = f" | Match {score:.1f}%" if isinstance(score, (int, float)) else ""
        pdf.add_page()
        pdf.section_title(
            f"Patient {idx}: {report.patient_id or 'UNKNOWN'} — {verdict}{score_txt}",
            first=True,
        )
        _write_audit_report_body(pdf, report, include_meta=False)

    pdf.section_title("Disclaimer")
    pdf.body_text(
        "Research prototype output only. Verify all eligibility decisions against source "
        "clinical records before any recruitment action.",
        size=8,
    )

    return _pdf_output_to_bytes(pdf)

def cohort_report_to_pdf(data: dict[str, Any]) -> bytes:
    """Build a paginated, wrapped PDF for cohort discovery export."""
    pdf = _AuditPDF()
    pdf.add_page()

    pdf.body_text(
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        size=8,
        spacing_after=0.3,
    )

    summary = data.get("summary") or {}
    pdf.section_title("Cohort Search Summary", first=True)
    pdf.kv_line("Eligible", summary.get("eligible", 0))
    pdf.kv_line("Conditional", summary.get("conditional", 0))
    pdf.kv_line("Ineligible", summary.get("ineligible", 0))
    total = (
        int(summary.get("eligible", 0) or 0)
        + int(summary.get("conditional", 0) or 0)
        + int(summary.get("ineligible", 0) or 0)
    )
    pdf.kv_line("Total screened", total if total else len(data.get("results") or []))

    criteria = data.get("criteria") or {}
    if criteria:
        _write_criteria_summary(pdf, criteria)

    results = data.get("results") or []
    pdf.section_title(f"Patient Results ({len(results)})")

    if not results:
        pdf.body_text("No patients in this export.")
        return _pdf_output_to_bytes(pdf)

    for idx, row in enumerate(results, start=1):
        _write_cohort_patient(pdf, row, idx)

    pdf.section_title("Disclaimer")
    pdf.body_text(
        "Research prototype output only. Verify all eligibility decisions against source "
        "clinical records before any recruitment action.",
        size=8,
    )

    return _pdf_output_to_bytes(pdf)
