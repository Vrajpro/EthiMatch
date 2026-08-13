# Documentation Builder

These scripts **generate the Word design document and diagrams**. They are **not part of the EthiMatch application** — you never need them to run the Streamlit dashboard.

## Files

| File | Purpose |
|------|---------|
| `build_diagrams.py` | Creates all PNG diagrams → `docs/figures/` |
| `build_doc.py` | Assembles the full Word document → `docs/reports/EthiMatch_Design_Document.docx` |
| `build_doc_part1.py` | Shared styling helpers (colours, tables, images) |
| `build_doc_part2.py` | Cover, index, introduction, naming conventions, architecture |
| `build_doc_part3.py` | Flowchart, use case, data flow, component diagram, file docs (part A) |
| `build_doc_part4.py` | File docs (part B), trials, literature mapping |
| `build_doc_part5.py` | Evaluation, rationale, pros/cons, risks, glossary, conclusion |
| `archive/` | Retired one-off scripts (safe to ignore) |

## How to regenerate

From the **project root** (`EthiMatch/`):

```powershell
.\ethimatch\venv\Scripts\python.exe tools\doc_builder\build_diagrams.py
.\ethimatch\venv\Scripts\python.exe tools\doc_builder\build_full_report.py
```

For individual chapters only:

```powershell
.\ethimatch\venv\Scripts\python.exe tools\doc_builder\build_chapter1.py
.\ethimatch\venv\Scripts\python.exe tools\doc_builder\build_chapter2.py
.\ethimatch\venv\Scripts\python.exe tools\doc_builder\build_chapter3.py
```

## Outputs

- Diagrams: `docs/figures/*.png`
- **Full dissertation report (all 8 chapters):** `docs/reports/EthiMatch_Project_Report.docx`
- Design document (technical): `docs/reports/EthiMatch_Design_Document.docx` (via `build_doc.py`)

After opening the Word file, right-click the Table of Contents and choose **Update Field** to refresh page numbers.
