"""
EthiMatch trial registry — load clinical trial protocols from ``trials/*.json`` / ``*.yaml``.

Drop a new protocol file into ``trials/`` and restart the app (or clear Streamlit cache)
to register it across the pipeline and dashboard.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TRIALS_DIR = Path(__file__).resolve().parent / "trials"

_REQUIRED_TOP_LEVEL = ("trial_id", "trial_name", "inclusion", "exclusion")

def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            f"PyYAML is required to load {path.name}. "
            "Install with: pip install pyyaml"
        ) from exc
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def _normalize_trial(raw: dict[str, Any], source: Path) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"{source.name}: trial definition must be a JSON/YAML object.")

    missing = [k for k in _REQUIRED_TOP_LEVEL if k not in raw]
    if missing:
        raise ValueError(f"{source.name}: missing required fields: {', '.join(missing)}")

    inclusion = raw.get("inclusion")
    exclusion = raw.get("exclusion")
    if not isinstance(inclusion, dict) or not isinstance(exclusion, dict):
        raise ValueError(f"{source.name}: 'inclusion' and 'exclusion' must be objects.")

    trial = {
        "trial_id": str(raw["trial_id"]).strip(),
        "trial_name": str(raw["trial_name"]).strip(),
        "description": str(raw.get("description", "")).strip(),
        "inclusion": dict(inclusion),
        "exclusion": dict(exclusion),
    }
    if not trial["trial_id"]:
        raise ValueError(f"{source.name}: trial_id cannot be empty.")
    return trial

def load_trial_file(path: Path) -> dict[str, Any]:
    """Load and validate a single trial protocol file."""
    suffix = path.suffix.lower()
    if suffix == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
    elif suffix in (".yaml", ".yml"):
        raw = _load_yaml(path)
    else:
        raise ValueError(f"Unsupported trial file type: {path.name}")

    trial = _normalize_trial(raw, path)
    trial["_source_file"] = path.name
    return trial

def load_all_trials(directory: Path | str | None = None) -> list[dict[str, Any]]:
    """Load every ``*.json`` / ``*.yaml`` trial protocol from *directory*."""
    root = Path(directory) if directory else TRIALS_DIR
    if not root.is_dir():
        return []

    paths = sorted(
        p for p in root.iterdir()
        if p.is_file() and p.suffix.lower() in (".json", ".yaml", ".yml")
    )

    trials: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for path in paths:
        trial = load_trial_file(path)
        tid = trial["trial_id"]
        if tid in seen_ids:
            raise ValueError(f"Duplicate trial_id '{tid}' in {path.name}")
        seen_ids.add(tid)
        trials.append(trial)

    trials.sort(key=lambda t: t["trial_id"])
    return trials

def get_trial_by_id(trial_id: str, directory: Path | str | None = None) -> dict[str, Any] | None:
    for trial in load_all_trials(directory):
        if trial["trial_id"] == trial_id:
            return trial
    return None

def trial_protocol_relpath(trial_id: str, directory: Path | str | None = None) -> str:
    """Return protocol path for UI tooltips, e.g. ``trials/trial_001.json``."""
    root = Path(directory) if directory else TRIALS_DIR
    for trial in load_all_trials(root):
        if trial["trial_id"] == trial_id:
            return f"trials/{trial.get('_source_file', 'unknown.json')}"
    return f"trials/{trial_id}.json"

def trial_select_label(trial: dict[str, Any]) -> str:
    """User-facing label for Streamlit selectboxes."""
    return f"{trial['trial_id']} — {trial['trial_name']}"

def trials_for_export(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip internal metadata before JSON export."""
    return [
        {k: v for k, v in t.items() if not k.startswith("_")}
        for t in trials
    ]
