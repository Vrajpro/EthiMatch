"""Structured clinical row records shared by all patient data providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class ConditionRecord:
    """One clinical condition row (active or historical)."""

    code: str = ""
    description: str = ""
    start_date: Optional[str] = None
    stop_date: Optional[str] = None
    patient_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "description": self.description,
            "start_date": self.start_date,
            "stop_date": self.stop_date,
            "patient_id": self.patient_id,
        }

@dataclass
class MedicationRecord:
    """One medication / prior-therapy row."""

    code: str = ""
    description: str = ""
    start_date: Optional[str] = None
    stop_date: Optional[str] = None
    patient_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "description": self.description,
            "start_date": self.start_date,
            "stop_date": self.stop_date,
            "patient_id": self.patient_id,
        }

@dataclass
class CarePlanRecord:
    """One active care-plan row (Synthea careplans.csv)."""

    code: str = ""
    description: str = ""
    reason: str = ""
    start_date: Optional[str] = None
    stop_date: Optional[str] = None
    patient_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "description": self.description,
            "reason": self.reason,
            "start_date": self.start_date,
            "stop_date": self.stop_date,
            "patient_id": self.patient_id,
        }
