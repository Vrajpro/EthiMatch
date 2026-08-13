"""Synthea CSV provider with unified PatientProfile fields."""

from __future__ import annotations

from pathlib import Path

from config import DEFAULT_CSV_DIR

from data_access.csv_provider import RealCSVProvider
from data_access.types import DataSource
from data_access.mock_clinical_note import generate_mock_clinical_note

class SyntheaDualSourceProvider(RealCSVProvider):
    """Synthea CSV provider that populates the unified ``PatientProfile`` fields.

    Inherits all CSV parsing from :class:`RealCSVProvider` (Synthea/OMOP layout
    is already its native format) and then injects ``active_conditions``,
    ``medications`` and ``data_source="Synthea"`` so every patient emitted is
    fully-typed for the dual-source contract.
    """

    data_source: DataSource = "Synthea"

    def __init__(
        self,
        data_dir: str | Path | None = None,
        limit: int | None = None,
        verbose: bool = False,
    ) -> None:
        super().__init__(
            data_dir=Path(data_dir) if data_dir else DEFAULT_CSV_DIR,
            limit=limit,
            verbose=verbose,
        )
        self._stamp_unified_fields()

    def _stamp_unified_fields(self) -> None:
        for pid, profile in self._patients.items():
            active = [
                c.description
                for c in self._conditions.get(pid, [])
                if c.description and (c.stop_date in (None, "", "nan", "NaT"))
            ]
            meds = [m.description for m in self._medications.get(pid, []) if m.description]
            profile.active_conditions = active
            profile.medications = meds
            profile.data_source = "Synthea"
            # Always overwrite ehr_note with the dual-source synthesised note —
            # the parent class seeds a legacy composition that doesn't match the
            # BioBERT-ready format (no explicit negation, no "65-year-old"
            # phrasing the NER + regex patterns expect).
            profile.ehr_note = generate_mock_clinical_note(profile)
            # Refresh structured entities so stage/disease match the synthesised note.
            self._pre_extracted[pid] = self._profile_to_entities(profile)
            pre = self._pre_extracted.get(pid)
            if isinstance(pre, dict):
                pre["data_source"] = "Synthea"

    def source_name(self) -> str:
        return f"Synthea CSV ({len(self._patients)} patients @ {self.data_dir})"