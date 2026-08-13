"""
EthiMatch — LLM baseline for evaluation comparison.

Provides a naive "prompt-style" eligibility classifier that mimics
asking a general LLM "Is this patient eligible?" without symbolic rules.

Modes:
  heuristic  — keyword/heuristic parser (default, no API key)
  openai     — GPT-4o-mini via OPENAI_API_KEY (optional)
"""

from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any

from data_simulator import build_trial_criteria

class BaselineClassifier(ABC):
    """Abstract baseline that returns binary eligibility per trial."""

    @abstractmethod
    def predict_patient(
        self,
        note: str,
        trials: list[dict[str, Any]],
    ) -> dict[str, bool]:
        """Return {trial_id: eligible_bool} for one patient note."""
        ...

    def predict_batch(
        self,
        notes: list[str],
        patient_ids: list[str],
        trials: list[dict[str, Any]] | None = None,
    ) -> dict[str, dict[str, bool]]:
        trials = trials or build_trial_criteria()
        results: dict[str, dict[str, bool]] = {}
        for pid, note in zip(patient_ids, notes):
            results[pid] = self.predict_patient(note, trials)
        return results

class HeuristicLLMBaseline(BaselineClassifier):
    """Simulates a naive LLM prompt using keyword heuristics.

    Known failure modes (by design, for thesis comparison):
      - No negation handling
      - No structured rule enforcement
      - Over-eligible on partial keyword matches
    """

    def predict_patient(
        self,
        note: str,
        trials: list[dict[str, Any]],
    ) -> dict[str, bool]:
        text = note.lower()
        extracted = self._quick_extract(text)
        verdicts: dict[str, bool] = {}

        for trial in trials:
            tid = trial["trial_id"]
            inc = trial.get("inclusion") or {}
            exc = trial.get("exclusion") or {}
            verdicts[tid] = self._evaluate_trial(extracted, text, inc, exc)

        return verdicts

    @staticmethod
    def _quick_extract(text: str) -> dict[str, Any]:
        age = None
        m = re.search(r"(\d{1,3})[-\s]?year[-\s]?old", text)
        if m:
            age = int(m.group(1))

        gender = None
        if re.search(r"\bfemale\b", text):
            gender = "female"
        elif re.search(r"\bmale\b", text):
            gender = "male"

        disease = None
        for d in ("nsclc", "breast cancer", "sclc", "lung cancer"):
            if d in text:
                disease = "NSCLC" if d == "nsclc" else d.title()
                if d == "lung cancer":
                    disease = "Lung Cancer"
                break

        stage = None
        sm = re.search(r"stage\s+(i{1,3}[ab]?|iv|v|\d+)", text)
        if sm:
            stage = sm.group(1).upper().replace(" ", "")

        ecog = None
        em = re.search(r"ecog\s*(?:ps|performance)?\s*[:=]?\s*(\d)", text)
        if em:
            ecog = int(em.group(1))

        bmi = None
        bm = re.search(r"bmi\s*[:=]?\s*(\d{2}(?:\.\d+)?)", text)
        if bm:
            bmi = float(bm.group(1))

        biomarkers: list[str] = []
        for bio in ("egfr+", "her2+", "alk+", "pd-l1", "kras"):
            if bio in text:
                biomarkers.append(bio.upper() if "+" in bio else bio)

        comorbidities: list[str] = []
        for c in ("diabetes", "chf", "copd", "hypertension"):
            if c in text:
                comorbidities.append(c)

        therapies: list[str] = []
        for t in ("nivolumab", "pembrolizumab", "cisplatin", "trastuzumab"):
            if t in text:
                therapies.append(t)

        return {
            "age": age, "gender": gender, "disease": disease,
            "stage": stage, "ecog_ps": ecog, "bmi": bmi,
            "biomarkers": biomarkers, "comorbidities": comorbidities,
            "prior_therapies": therapies,
        }

    def _evaluate_trial(
        self,
        ext: dict[str, Any],
        text: str,
        inc: dict[str, Any],
        exc: dict[str, Any],
    ) -> bool:
        """Naive eligibility — missing fields treated as pass (LLM hallucination risk)."""
        diseases = inc.get("diseases") or []
        if diseases:
            disease = ext.get("disease")
            if disease and disease not in diseases:
                if not any(d.lower() in text for d in diseases):
                    return False

        stages = inc.get("stages") or []
        if stages and ext.get("stage") and ext["stage"] not in stages:
            return False

        age = ext.get("age")
        if age is not None:
            if inc.get("age_min") and age < inc["age_min"]:
                return False
            if inc.get("age_max") and age > inc["age_max"]:
                return False

        if inc.get("gender") and ext.get("gender"):
            if ext["gender"].lower() not in [g.lower() for g in inc["gender"]]:
                return False

        req_bio = inc.get("required_biomarkers") or []
        if req_bio:
            patient_bio = ext.get("biomarkers") or []
            if patient_bio and not any(b in patient_bio for b in req_bio):
                if not any(b.lower() in text for b in req_bio):
                    return False

        ecog = ext.get("ecog_ps")
        if ecog is not None and inc.get("ecog_max") is not None:
            if ecog > inc["ecog_max"]:
                return False

        bmi = ext.get("bmi")
        if bmi is not None:
            if inc.get("bmi_max") and bmi > inc["bmi_max"]:
                return False
            if exc.get("bmi_min") and bmi < exc["bmi_min"]:
                return False

        for c in exc.get("excluded_comorbidities") or []:
            if c.lower() in text:
                return False

        for t in exc.get("excluded_prior_therapies") or []:
            if t.lower() in text:
                return False

        return True

class OpenAIBaseline(BaselineClassifier):
    """Optional GPT baseline — requires OPENAI_API_KEY."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise ImportError(
                    "Install openai: pip install openai"
                ) from exc
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise EnvironmentError("Set OPENAI_API_KEY for OpenAI baseline.")
            self._client = OpenAI(api_key=api_key)
        return self._client

    def predict_patient(
        self,
        note: str,
        trials: list[dict[str, Any]],
    ) -> dict[str, bool]:
        client = self._get_client()
        prompt = (
            "You are a clinical trial coordinator. Given the patient note and "
            "trial criteria JSON, respond ONLY with JSON mapping trial_id to "
            "true (eligible) or false (not eligible). Do not explain.\n\n"
            f"NOTE:\n{note[:4000]}\n\nTRIALS:\n{json.dumps(trials, indent=2)}"
        )
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        parsed = json.loads(content)
        return {
            t["trial_id"]: bool(parsed.get(t["trial_id"], False))
            for t in trials
        }

def get_baseline(mode: str = "heuristic", **kwargs) -> BaselineClassifier:
    if mode == "openai":
        return OpenAIBaseline(**kwargs)
    return HeuristicLLMBaseline(**kwargs)
