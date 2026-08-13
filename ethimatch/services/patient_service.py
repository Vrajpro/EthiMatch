"""Patient registry access helpers."""

from __future__ import annotations

from typing import Any, Callable

from config import DEFAULT_CSV_DIR
from data_access.loader import normalise_source
from data_access.types import DATA_SOURCE_LABELS
from data_simulator import PatientProfile

def registry_limit_for_provider(limit_raw: int, limit_all: int) -> int | None:
    return None if limit_raw == limit_all else limit_raw

def registry_limit_label(limit_raw: int, limit_all: int) -> str:
    return "all rows" if limit_raw == limit_all else str(limit_raw)

def data_source_label(source: str) -> str:
    src = normalise_source(source)
    return DATA_SOURCE_LABELS.get(src, src)

def load_dashboard_registry(
    get_provider: Callable[[], Any],
) -> tuple[Any | None, list[PatientProfile], str]:
    try:
        registry = get_provider()
    except FileNotFoundError:
        return None, [], f"CSV not found ({DEFAULT_CSV_DIR})"
    patients = registry.get_all_patients()
    return registry, patients, registry.source_name()
