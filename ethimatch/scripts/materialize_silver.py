"""
Materialize the silver data tier — offline BioBERT batch over CSV patients.

Writes one JSON file per patient to ``data/silver/{patient_id}.json`` so the
Streamlit UI can skip neural inference on cache hits.

Usage:
  python scripts/materialize_silver.py
  python scripts/materialize_silver.py --limit 200 --force
  python scripts/materialize_silver.py --oncology-only
  python scripts/materialize_silver.py --source mimic
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import console  # noqa: F401 — UTF-8 on Windows
from config import DEFAULT_CSV_DIR
from console import safe_print
from data_loader import DEFAULT_MIMIC_DEMO_DIR, load_provider, normalise_source
from device_utils import resolve_torch_device
from mock_database import get_default_csv_provider, select_patient_ids_for_screening
from neural_extractor import NeuralExtractor
from silver_cache import (
    SILVER_DIR,
    compute_input_hash,
    load_silver_entities,
    save_silver_entities,
)

def main() -> None:
    parser = argparse.ArgumentParser(description="Batch materialize silver entity cache")
    parser.add_argument(
        "--source",
        type=str,
        default="synthea",
        choices=["synthea", "mimic"],
        help="Patient data source: 'synthea' (default) or 'mimic' (MIMIC-IV Demo).",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Override the source's default data directory. "
             "Defaults: Synthea→config.DEFAULT_CSV_DIR, MIMIC→config.DEFAULT_MIMIC_DIR.",
    )
    parser.add_argument(
        "--csv-dir",
        type=str,
        default=None,
        help="Deprecated alias for --data-dir (kept for backwards compatibility).",
    )
    parser.add_argument("--limit", type=int, default=None, help="Max CSV rows to load")
    parser.add_argument("--batch", type=int, default=None, help="Max patients to process")
    parser.add_argument("--oncology-only", action="store_true")
    parser.add_argument("--force", action="store_true", help="Overwrite existing silver JSON")
    parser.add_argument("--device", type=int, default=-1, help="-1=auto, 0=GPU, -1=CPU")
    args = parser.parse_args()

    src = normalise_source(args.source)
    data_dir = args.data_dir or args.csv_dir
    if src == "MIMIC":
        default_dir = data_dir or str(DEFAULT_MIMIC_DEMO_DIR)
        safe_print(f"[Silver] Source: MIMIC-IV Demo  ({default_dir})")
        provider = load_provider("MIMIC", limit=args.limit, data_dir=data_dir, verbose=True)
    else:
        default_dir = data_dir or str(DEFAULT_CSV_DIR)
        safe_print(f"[Silver] Source: Synthea  ({default_dir})")
        provider = get_default_csv_provider(
            data_dir=data_dir, limit=args.limit, verbose=True
        )

    batch_cap = args.batch if args.batch is not None else len(provider.list_patient_ids())
    ids = select_patient_ids_for_screening(
        provider,
        max_patients=batch_cap,
        oncology_only=args.oncology_only,
    )
    if not ids:
        raise SystemExit("No patients selected — adjust --limit or disable --oncology-only.")

    device = resolve_torch_device(args.device)
    extractor = NeuralExtractor(device=device, verbose=True)

    safe_print(f"\n[Silver] Output directory: {SILVER_DIR.resolve()}")
    safe_print(f"[Silver] Processing {len(ids)} patient(s) on device "
               f"{'GPU:0' if device == 0 else 'CPU'}…\n")

    t0 = time.time()
    written = skipped = errors = 0

    for i, pid in enumerate(ids, 1):
        note = provider.get_patient_note(pid)
        if not note:
            errors += 1
            safe_print(f"  [{i:04d}] ERROR no note for {pid}")
            continue

        # Skip only when a cached entry exists AND its stored input hash still
        # matches the current note (stale entries fall through and re-extract).
        note_hash = compute_input_hash(note)
        if not args.force and load_silver_entities(pid, expected_hash=note_hash) is not None:
            skipped += 1
            if i % 25 == 1:
                safe_print(f"  [{i:04d}/{len(ids)}] SKIP (cached) {pid[:20]}…")
            continue

        try:
            entities = extractor.extract(note, silent=True).to_dict()
            path = save_silver_entities(pid, entities, input_hash=note_hash)
            written += 1
            if i % 10 == 1 or len(ids) <= 20:
                safe_print(f"  [{i:04d}/{len(ids)}] Wrote {path.name}")
        except Exception as exc:
            errors += 1
            safe_print(f"  [{i:04d}] ERROR {pid}: {exc}")

    elapsed = time.time() - t0
    safe_print(
        f"\n[Silver] Done in {elapsed:.1f}s — "
        f"written={written}, skipped={skipped}, errors={errors}"
    )

if __name__ == "__main__":
    main()
