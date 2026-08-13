"""
EthiMatch — Silver tier entity cache.

Stores materialized ``ExtractedEntities`` JSON per patient so BioBERT does not
need to re-run on every Streamlit session.  Files live under ``data/silver/``.

Cache invalidation
------------------
Each cached file records a hash of the exact input the neural extractor saw
(the synthesised note) together with a ``cache_version`` tag. On lookup the
caller may pass the current input hash; if it does not match the stored hash
the entry is treated as a **miss** so BioBERT re-runs and the stale entry is
refreshed. This makes the cache self-invalidating when the underlying patient
data — or the extraction logic/model version — changes.

Legacy files written before hashing was introduced carry no hash; these remain
valid (backward compatible) and are refreshed the next time they are written.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from config import ETHIMATCH_ROOT
from console import json_dumps, safe_print

SILVER_DIR = ETHIMATCH_ROOT / "data" / "silver"

# Bump this whenever the note-synthesis logic or NER model changes in a way that
# should invalidate every existing silver entry.
CACHE_VERSION = "v1"

_META_KEY = "_cache_meta"

def _safe_filename(patient_id: str) -> str:
    return re.sub(r"[^\w\-]", "_", patient_id.strip()) or "unknown"

def silver_path(patient_id: str) -> Path:
    return SILVER_DIR / f"{_safe_filename(patient_id)}.json"

def compute_input_hash(note: str | None) -> str:
    """Stable hash of the extractor input, namespaced by ``CACHE_VERSION``.

    Hashing the note text plus the version means the hash changes if either the
    patient's data changes or the cache version is bumped, so stale entries are
    detected automatically.
    """
    payload = f"{CACHE_VERSION}\n{note or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def load_silver_entities(
    patient_id: str,
    expected_hash: str | None = None,
) -> dict[str, Any] | None:
    """Return cached entities for *patient_id*, or ``None`` if not usable.

    If *expected_hash* is provided and the stored entry carries a different
    hash, the entry is treated as stale and ``None`` is returned (cache miss),
    forcing a fresh extraction. Entries without a stored hash (legacy files)
    are accepted for backward compatibility.
    """
    path = silver_path(patient_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None

    meta = data.get(_META_KEY)
    if isinstance(meta, dict):
        stored_pid = meta.get("patient_id")
        if isinstance(stored_pid, str) and stored_pid.strip() and stored_pid != patient_id:
            return None

    if expected_hash is not None:
        stored_hash = None
        if isinstance(meta, dict):
            stored_hash = meta.get("input_hash")
        # Only invalidate when a stored hash exists and differs. A missing hash
        # means a legacy file → keep it (backward compatible).
        if stored_hash is not None and stored_hash != expected_hash:
            return None

    return data

def save_silver_entities(
    patient_id: str,
    entities: dict[str, Any],
    input_hash: str | None = None,
) -> Path:
    """Persist entities to the silver tier, stamping the input hash + version."""
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    path = silver_path(patient_id)
    payload = dict(entities)
    payload.setdefault("extraction_sources", {})
    payload["extraction_sources"].setdefault("_silver", "silver")
    payload[_META_KEY] = {
        "cache_version": CACHE_VERSION,
        "input_hash": input_hash,
        "patient_id": patient_id,
    }
    path.write_text(json_dumps(payload, indent=2), encoding="utf-8")
    return path

def count_silver_entities() -> int:
    if not SILVER_DIR.is_dir():
        return 0
    return sum(1 for p in SILVER_DIR.glob("*.json") if p.is_file())

def list_silver_patient_ids() -> list[str]:
    if not SILVER_DIR.is_dir():
        return []
    return sorted(p.stem for p in SILVER_DIR.glob("*.json") if p.is_file())
