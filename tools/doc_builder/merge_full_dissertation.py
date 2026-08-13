"""Merge detailed Evaluation + Conclusion chapters into the full project report.

Output (only):
  docs/reports/EthiMatch_Project_Report.docx

Run:
  .\\ethimatch\\venv\\Scripts\\python.exe tools\\doc_builder\\merge_full_dissertation.py
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_full_report import (  # noqa: E402
    ALL_CHAPTERS,
    add_footer,
    add_page_break,
    build_abstract,
    build_ai_declaration,
    build_cover,
    build_references,
    build_toc,
)
from report_styles import (  # noqa: E402
    add_bullet,
    add_chapter_heading,
    add_image,
    add_para,
    add_section_heading,
    setup_document,
)

REPORTS = ROOT / "docs" / "reports"
OUT = REPORTS / "EthiMatch_Project_Report.docx"
_TMP = Path(tempfile.gettempdir()) / "ethimatch_report_build"
EVAL_DOC = _TMP / "eval_chapter.docx"
CONC_DOC = _TMP / "conc_chapter.docx"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _append_body(target: Document, source: Document) -> int:
    """Copy all body elements from source into target (keep target sectPr last)."""
    body = target.element.body
    sect_pr = None
    for child in list(body):
        if child.tag == qn("w:sectPr"):
            sect_pr = child
            body.remove(child)
            break

    count = 0
    for child in list(source.element.body):
        if child.tag == qn("w:sectPr"):
            continue
        body.append(deepcopy(child))
        count += 1

    if sect_pr is not None:
        body.append(sect_pr)
    return count


def _ensure_chapter_docs() -> None:
    """Load chapter builders. Evaluation is written into the main doc (images stay valid)."""
    _TMP.mkdir(parents=True, exist_ok=True)
    conc_mod = _load_module(
        "build_conclusion_and_viva",
        Path(__file__).resolve().parent / "build_conclusion_and_viva.py",
    )
    conc_mod.OUT_CONCLUSION = CONC_DOC
    conc_mod.build_conclusion()


def _write_standard_chapter(doc: Document, title: str, sections) -> int:
    add_chapter_heading(doc, title)
    wc = 0
    # section_title -> list of (filename, caption)
    chapter_figures = {
        "Chapter 3: Research Design and Methodology": {
            "3.6 Comparative Evaluation Design": [
                ("07_evaluation.png", "Figure 1 — Controlled evaluation design (neuro-symbolic vs pure neural)."),
            ],
        },
        "Chapter 4: Artefact Design and Development": {
            "4.2 Requirements, Design Principles and Stakeholder Use Cases": [
                ("03_use_case.png", "Figure 2 — EthiMatch primary stakeholder use cases."),
            ],
            "4.3 Five-Stage Pipeline Architecture": [
                ("01_architecture.png", "Figure 3 — EthiMatch five-stage neuro-symbolic architecture."),
                ("04_flowchart.png", "Figure 4 — End-to-end pipeline control flow (cache, early-exit, NER, rules, XAI)."),
            ],
            "4.4 Data Layer": [
                ("02_dataflow.png", "Figure 5 — Data flow from sources through pipeline to AuditReport."),
            ],
            "4.7 User Interface and Clinician Walkthrough": [
                (
                    "screenshots/01_dashboard.png",
                    "Figure 6 — EthiMatch Dashboard: registered trials, Synthea cohort overview, and session controls.",
                ),
                (
                    "screenshots/02c_patient_matching_audit.png",
                    "Figure 7 — Patient Matching: Quick Entry result showing Eligible verdict with expanded patient detail and audit tabs.",
                ),
                (
                    "screenshots/03_cohort_discovery.png",
                    "Figure 8 — Cohort Discovery: trial-centric screening of 100 patients against ONC-001 (eligible, inconclusive, and ineligible counts).",
                ),
                (
                    "screenshots/04_evaluation.png",
                    "Figure 9 — Evaluation page: neuro-symbolic vs pure-neural benchmark settings with cached synthetic results and McNemar summary.",
                ),
            ],
            "4.10 Repository and Component Organisation": [
                ("05_components.png", "Figure 10 — Logical component map (data, neural, symbolic, XAI, UI)."),
            ],
        },
    }
    figs = chapter_figures.get(title, {})
    for sec_title, body in sections:
        add_section_heading(doc, sec_title)
        for para in body.split("\n\n"):
            text = para.strip()
            if not text:
                continue
            if text.lstrip().startswith("•"):
                for line in text.split("\n"):
                    add_bullet(doc, line.strip().lstrip("•").strip())
            else:
                add_para(doc, text)
            wc += len(text.split())
        for item in figs.get(sec_title, []):
            fname, cap = item
            add_image(doc, fname, cap)
    return wc


def main() -> None:
    print("[merge] refreshing Evaluation + Conclusion + Viva docs...")
    _ensure_chapter_docs()

    print("[merge] building full project report with detailed Ch6 + Ch8...")
    doc = setup_document()
    add_footer(doc)
    build_cover(doc)
    build_abstract(doc)
    build_toc(doc)

    total_words = 0
    for title, sections in ALL_CHAPTERS:
        if title.startswith("Chapter 6:"):
            print("  writing Evaluation chapter into this document (embedded figures)...")
            eval_mod = _load_module(
                "build_evaluation_chapter",
                Path(__file__).resolve().parent / "build_evaluation_chapter.py",
            )
            eval_mod.write_evaluation_chapter(doc)
            add_page_break(doc)
            continue

        if title.startswith("Chapter 8:"):
            print("  inserting detailed Conclusion chapter...")
            n = _append_body(doc, Document(str(CONC_DOC)))
            print(f"  Chapter 8 elements copied: {n}")
            add_page_break(doc)
            continue

        wc = _write_standard_chapter(doc, title, sections)
        total_words += wc
        print(f"  {title}: ~{wc} words")
        add_page_break(doc)

    build_references(doc)
    build_ai_declaration(doc)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        doc.save(str(OUT))
    except PermissionError:
        raise PermissionError(
            f"Cannot write {OUT.name}. Close Microsoft Word (and the file) then run again."
        ) from None

    print(f"[merge] SAVED: {OUT}")
    print(f"[merge] Size KB: {OUT.stat().st_size / 1024:.1f}")
    print(f"[merge] Approx words (Ch1-5,7 only counted): {total_words}")
    print("[merge] Open in Word, right-click TOC, Update Field, Update entire table")


if __name__ == "__main__":
    main()
