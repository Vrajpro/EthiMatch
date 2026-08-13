"""Shared HTML and patient-profile helpers."""
from __future__ import annotations

import html
import re
from typing import Any

from data_access.interfaces import PatientDataProvider

def resolve_patient_profile(
    patient_id: str,
    profile: Any | None,
    provider: PatientDataProvider | None = None,
) -> Any | None:
    """Return the profile for *patient_id*, refetching from the provider when needed."""
    if provider is not None:
        fresh = provider.get_patient(patient_id)
        if fresh is not None:
            return fresh
    if profile is not None and getattr(profile, "patient_id", None) == patient_id:
        return profile
    return None

def _esc(text: Any) -> str:
    return html.escape(str(text) if text is not None else "")

def _md_inline(text: str) -> str:
    """Escape then convert minimal markdown bold to HTML."""
    escaped = _esc(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)

def _matching_fmt(val: Any) -> str:
    if val is None:
        return "Missing"
    if isinstance(val, list):
        return ", ".join(str(v) for v in val) if val else "Missing"
    return str(val)

def _short_patient_id(patient_id: str, *, max_len: int = 20) -> str:
    if len(patient_id) <= max_len:
        return patient_id
    return f"{patient_id[:10]}…{patient_id[-4:]}"

def _records_to_dataframe(records: list[Any], columns: dict[str, str]) -> "Any":
    import pandas as pd

    if not records:
        return pd.DataFrame(columns=list(columns.values()))
    rows = [{label: getattr(rec, attr, "") or "—" for attr, label in columns.items()} for rec in records]
    return pd.DataFrame(rows)
