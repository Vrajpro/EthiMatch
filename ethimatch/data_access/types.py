"""Shared dual-source loader types and display constants."""

from __future__ import annotations

from typing import Literal

from config import DEFAULT_MIMIC_DIR

DataSource = Literal["MIMIC", "Synthea"]

DEFAULT_MIMIC_DEMO_DIR = DEFAULT_MIMIC_DIR

DATA_SOURCE_LABELS: dict[DataSource, str] = {
    "MIMIC": "MIMIC-IV Demo (Clinical Benchmark)",
    "Synthea": "Synthea (Synthetic Prototyping)",
}
