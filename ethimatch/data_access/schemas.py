"""Raw-row schemas for MIMIC-IV Demo and Synthea CSV ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional

def _as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if text.lower() in ("nan", "none", "nat", "null"):
        return default
    return text

def _as_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    text = _as_str(value)
    if not text:
        return default
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return default

def _as_datetime(value: Any) -> Optional[datetime]:
    """Parse common MIMIC / Synthea timestamp formats; return None on miss."""
    text = _as_str(value)
    if not text:
        return None

    if text.endswith("Z"):
        text = text[:-1]

    candidates = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
    )
    for fmt in candidates:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None

@dataclass
class MIMICPatient:
    """Row from ``patients.csv`` (MIMIC-IV Demo)."""

    subject_id: int
    gender: str
    anchor_age: int
    anchor_year: int
    dod: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Optional["MIMICPatient"]:
        sid = _as_int(row.get("subject_id"))
        if sid is None:
            return None
        return cls(
            subject_id=sid,
            gender=_as_str(row.get("gender"), default="unknown"),
            anchor_age=_as_int(row.get("anchor_age"), default=0) or 0,
            anchor_year=_as_int(row.get("anchor_year"), default=0) or 0,
            dod=_as_datetime(row.get("dod")),
        )

@dataclass
class MIMICAdmission:
    """Row from ``admissions.csv``."""

    subject_id: int
    hadm_id: int
    admittime: Optional[datetime]
    dischtime: Optional[datetime]
    admission_type: str

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Optional["MIMICAdmission"]:
        sid = _as_int(row.get("subject_id"))
        hadm = _as_int(row.get("hadm_id"))
        if sid is None or hadm is None:
            return None
        return cls(
            subject_id=sid,
            hadm_id=hadm,
            admittime=_as_datetime(row.get("admittime")),
            dischtime=_as_datetime(row.get("dischtime")),
            admission_type=_as_str(row.get("admission_type")),
        )

@dataclass
class MIMICDiagnosis:
    """Row from ``diagnoses_icd.csv`` (per-admission diagnosis assignment)."""

    subject_id: int
    hadm_id: int
    seq_num: int
    icd_code: str
    icd_version: str = ""

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Optional["MIMICDiagnosis"]:
        sid = _as_int(row.get("subject_id"))
        hadm = _as_int(row.get("hadm_id"))
        code = _as_str(row.get("icd_code"))
        if sid is None or hadm is None or not code:
            return None
        return cls(
            subject_id=sid,
            hadm_id=hadm,
            seq_num=_as_int(row.get("seq_num"), default=0) or 0,
            icd_code=code,
            icd_version=_as_str(row.get("icd_version")),
        )

@dataclass
class MIMICDiagnosisDict:
    """Row from ``d_icd_diagnoses.csv`` — ICD code → long_title dictionary."""

    icd_code: str
    long_title: str
    icd_version: str = ""

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Optional["MIMICDiagnosisDict"]:
        code = _as_str(row.get("icd_code"))
        title = _as_str(row.get("long_title"))
        if not code or not title:
            return None
        return cls(
            icd_code=code,
            long_title=title,
            icd_version=_as_str(row.get("icd_version")),
        )

@dataclass
class MIMICProcedureDict:
    """Row from ``d_icd_procedures.csv``."""

    icd_code: str
    long_title: str
    icd_version: str = ""

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Optional["MIMICProcedureDict"]:
        code = _as_str(row.get("icd_code"))
        title = _as_str(row.get("long_title"))
        if not code or not title:
            return None
        return cls(
            icd_code=code,
            long_title=title,
            icd_version=_as_str(row.get("icd_version")),
        )

@dataclass
class MIMICPrescription:
    """Row from ``prescriptions.csv``."""

    subject_id: int
    hadm_id: int
    drug: str
    route: str = ""
    starttime: Optional[datetime] = None
    stoptime: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Optional["MIMICPrescription"]:
        sid = _as_int(row.get("subject_id"))
        hadm = _as_int(row.get("hadm_id"))
        drug = _as_str(row.get("drug"))
        if sid is None or hadm is None or not drug:
            return None
        return cls(
            subject_id=sid,
            hadm_id=hadm,
            drug=drug,
            route=_as_str(row.get("route")),
            starttime=_as_datetime(row.get("starttime")),
            stoptime=_as_datetime(row.get("stoptime")),
        )

@dataclass
class SyntheaPatient:
    """Row from Synthea ``patients.csv``."""

    Id: str
    BIRTHDATE: Optional[datetime]
    GENDER: str
    DEATHDATE: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Optional["SyntheaPatient"]:
        pid = _as_str(row.get("Id") or row.get("ID") or row.get("id"))
        if not pid:
            return None
        return cls(
            Id=pid,
            BIRTHDATE=_as_datetime(row.get("BIRTHDATE")),
            DEATHDATE=_as_datetime(row.get("DEATHDATE")),
            GENDER=_as_str(row.get("GENDER"), default="unknown"),
        )

@dataclass
class SyntheaCondition:
    """Row from Synthea ``conditions.csv``."""

    START: Optional[datetime]
    PATIENT: str
    CODE: str
    DESCRIPTION: str
    STOP: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        return self.STOP is None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Optional["SyntheaCondition"]:
        pid = _as_str(row.get("PATIENT"))
        desc = _as_str(row.get("DESCRIPTION"))
        if not pid or not desc:
            return None
        return cls(
            START=_as_datetime(row.get("START")),
            STOP=_as_datetime(row.get("STOP")),
            PATIENT=pid,
            CODE=_as_str(row.get("CODE")),
            DESCRIPTION=desc,
        )

@dataclass
class SyntheaMedication:
    """Row from Synthea ``medications.csv``."""

    START: Optional[datetime]
    PATIENT: str
    CODE: str
    DESCRIPTION: str
    STOP: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        return self.STOP is None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Optional["SyntheaMedication"]:
        pid = _as_str(row.get("PATIENT"))
        desc = _as_str(row.get("DESCRIPTION"))
        if not pid or not desc:
            return None
        return cls(
            START=_as_datetime(row.get("START")),
            STOP=_as_datetime(row.get("STOP")),
            PATIENT=pid,
            CODE=_as_str(row.get("CODE")),
            DESCRIPTION=desc,
        )

@dataclass
class SyntheaCarePlan:
    """Row from Synthea ``careplans.csv``."""

    Id: str
    START: Optional[datetime]
    PATIENT: str
    DESCRIPTION: str
    STOP: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Optional["SyntheaCarePlan"]:
        cp_id = _as_str(row.get("Id") or row.get("ID") or row.get("id"))
        pid = _as_str(row.get("PATIENT"))
        desc = _as_str(row.get("DESCRIPTION"))
        if not cp_id or not pid or not desc:
            return None
        return cls(
            Id=cp_id,
            START=_as_datetime(row.get("START")),
            STOP=_as_datetime(row.get("STOP")),
            PATIENT=pid,
            DESCRIPTION=desc,
        )

__all__ = [
    "MIMICPatient",
    "MIMICAdmission",
    "MIMICDiagnosis",
    "MIMICDiagnosisDict",
    "MIMICProcedureDict",
    "MIMICPrescription",
    "SyntheaPatient",
    "SyntheaCondition",
    "SyntheaMedication",
    "SyntheaCarePlan",
]
