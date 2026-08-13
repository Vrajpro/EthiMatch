"""Biomedical NER and regex extraction into structured entities."""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from typing import Any, Optional

from config import ALLOWED_DISEASES, normalize_disease
from console import safe_print, to_json_safe
from device_utils import resolve_torch_device

warnings.filterwarnings("ignore", category=FutureWarning)

@dataclass
class ExtractedEntities:
    """Entities extracted from one clinical note."""
    age:                Optional[int]          = None
    gender:             Optional[str]          = None
    disease:            Optional[str]          = None
    stage:              Optional[str]          = None
    biomarkers:         list[str]              = field(default_factory=list)
    bmi:                Optional[float]        = None
    ecog_ps:            Optional[int]          = None
    comorbidities:      list[str]              = field(default_factory=list)
    prior_therapies:    list[str]              = field(default_factory=list)
    negated_fields:     list[str]              = field(default_factory=list)
    raw_ner_entities:   list[dict[str, Any]]   = field(default_factory=list)
    confidence_scores:  dict[str, float]       = field(default_factory=dict)
    extraction_sources: dict[str, str]         = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict for downstream consumers."""
        return to_json_safe({
            "age":               self.age,
            "gender":            self.gender,
            "disease":           self.disease,
            "stage":             self.stage,
            "biomarkers":        self.biomarkers,
            "bmi":               self.bmi,
            "ecog_ps":           self.ecog_ps,
            "comorbidities":     self.comorbidities,
            "prior_therapies":   self.prior_therapies,
            "negated_fields":    self.negated_fields,
            "confidence_scores": self.confidence_scores,
            "extraction_sources": self.extraction_sources,
        })

class NeuralExtractor:
    """Wraps a HuggingFace token-classification pipeline and a set
    of deterministic regex patterns to extract structured entities
    from unstructured oncology notes.

    Architecture
    ────────────
    1. **BioBERT NER pass** → catches biomedical named entities
       (diseases, genes, chemicals/drugs) that are beyond simple
       pattern matching.
    2. **Regex fallback pass** → catches numeric/formatted fields
       (age, BMI, ECOG, stage) that NER models typically ignore
       because they look like numbers, not named entities.
    3. **Merge & deduplicate** → unifies both extraction channels
       into a single `ExtractedEntities` object.

    Parameters
    ──────────
    model_name : str
        HuggingFace model identifier.
        Default = ``"d4data/biomedical-ner-all"``
    device : int
        -1 = CPU (safe default), 0 = first GPU.
    confidence_threshold : float
        Minimum softmax score to accept an NER entity.
    """

    _RE_AGE   = re.compile(
        r"(?:(?:age[d ]?\s*|,\s*age\s+)(\d{1,3}))|"
        r"(\d{1,3})\s*[-–]?\s*(?:year[- ]?old|y/?o\b|yr[- ]?old|y\.o\.)",
        re.IGNORECASE,
    )
    _RE_GENDER = re.compile(
        r"\b(male|female|man|woman)\b", re.IGNORECASE,
    )
    _RE_STAGE = re.compile(
        r"\bstage\s+(IV|III[AB]?|II[AB]?|I[AB]?|[1234])\b", re.IGNORECASE,
    )
    _RE_BMI   = re.compile(
        r"\bBMI\s*(?:is|of|recorded at|:)?\s*(\d{2,3}(?:\.\d{1,2})?)",
        re.IGNORECASE,
    )
    _RE_ECOG  = re.compile(
        r"ECOG\s*(?:PS|performance\s*status)?\s*(?::|\()?\s*(\d)",
        re.IGNORECASE,
    )
    _RE_DISEASE = re.compile(
        r"\b("
        + "|".join(
            re.escape(d).replace(r"\ ", r"\s+")
            for d in (
                *ALLOWED_DISEASES,
                "Non-?Small\\s+Cell\\s+Lung\\s+Cancer",
            )
        )
        + r")\b",
        re.IGNORECASE,
    )
    _RE_BIOMARKER = re.compile(
        r"\b(EGFR[+\-]?|ALK[+\-]?|HER2[+\-]?|ER[+\-]|PR[+\-]|"
        r"PD-?L1\s*\d{1,3}%?|KRAS\s*[A-Z]\d+[A-Z]?|BRAF\s*V\d+[A-Z]?)\b",
        re.IGNORECASE,
    )
    _RE_COMORBIDITY = re.compile(
        r"\b(type [12] diabetes|diabetes|"
        r"congestive heart failure|"
        r"hypertension|COPD|CHF|"
        r"atrial fibrillation|osteoporosis|CKD|asthma|"
        r"coronary artery disease)\b",
        re.IGNORECASE,
    )
    _RE_THERAPY = re.compile(
        r"\b(carboplatin|cisplatin|pembrolizumab|nivolumab|"
        r"atezolizumab|docetaxel|paclitaxel|etoposide|"
        r"tamoxifen|letrozole|trastuzumab|doxorubicin|"
        r"bevacizumab|pemetrexed|gemcitabine|fentanyl)\b",
        re.IGNORECASE,
    )

    _RE_NEGATION = re.compile(
        r"(?:denies?|denied|no history of|negative for|rules? out|"
        r"without|free of|absence of|not on|never received|"
        r"no evidence of|patient denies)\s+([^.;,\n]{3,40})",
        re.IGNORECASE,
    )

    @classmethod
    def _normalise_disease(cls, raw: str) -> Optional[str]:
        """Map free-text disease mentions to canonical config disease codes."""
        return normalize_disease(raw)

    def __init__(
        self,
        model_name: str = "d4data/biomedical-ner-all",
        device: int = -1,
        confidence_threshold: float = 0.60,
        verbose: bool = True,
    ) -> None:
        self.model_name = model_name
        self.device = resolve_torch_device(None if device == -1 else device)
        self.confidence_threshold = confidence_threshold
        self.verbose = verbose
        self._pipeline = None   # lazy-loaded

        if verbose:
            dev_label = "CPU" if self.device == -1 else f"GPU:{self.device}"
            safe_print(f"[NeuralExtractor] Initialised (model={model_name}, "
                       f"device={dev_label}, "
                       f"threshold={confidence_threshold})")

    def _load_pipeline(self, silent: bool = False):
        """Load the HuggingFace NER pipeline on first call."""
        if self._pipeline is not None:
            return

        if not silent:
            safe_print("[NeuralExtractor] Loading BioBERT NER pipeline ...")
        from transformers import pipeline as hf_pipeline

        self._pipeline = hf_pipeline(
            task="token-classification",
            model=self.model_name,
            aggregation_strategy="simple",
            device=self.device,
        )
        if not silent:
            safe_print("[NeuralExtractor] Pipeline ready.")

    def extract(self, note: str, silent: bool = False) -> ExtractedEntities:
        
        if not silent:
            safe_print(f"\n[NeuralExtractor] Extracting from note ({len(note)} chars)")

        entities = ExtractedEntities()

        ner_results = self._run_ner(note, silent=silent)
        entities.raw_ner_entities = ner_results
        self._apply_ner_results(entities, ner_results)

        self._apply_regex_fallback(entities, note, silent=silent)
        self._apply_negation_filter(entities, note, silent=silent)

        if not silent:
            safe_print("[NeuralExtractor] Extraction summary:")
            for key, val in entities.to_dict().items():
                status = "OK" if val not in (None, []) else "MISSING"
                safe_print(f"   {key:20s}: {val!s:40s}  {status}")

        return entities

\

    def _run_ner(self, text: str, silent: bool = False) -> list[dict[str, Any]]:
        """Run the HuggingFace NER pipeline and filter by confidence."""
        self._load_pipeline(silent=silent)

        raw = self._pipeline(text)
        filtered = [
            ent for ent in raw
            if ent["score"] >= self.confidence_threshold
        ]
        if not silent:
            safe_print(
                f"[NeuralExtractor] BioBERT found {len(raw)} raw entities, "
                f"{len(filtered)} above threshold ({self.confidence_threshold})"
            )
            for ent in filtered:
                safe_print(
                    f"   -> {ent['entity_group']:20s} | "
                    f"{ent['word']:25s} | score={ent['score']:.3f}"
                )
        return filtered

    def _apply_ner_results(
        self, entities: ExtractedEntities, ner_results: list[dict]
    ) -> None:
        
        for ent in ner_results:
            group = ent["entity_group"]
            word  = ent["word"].strip()
            score = float(ent.get("score", 0.0))

            if group in ("Disease_disorder", "Diagnostic_procedure"):
                # Try to normalise to known disease names
                normalised = self._normalise_disease(word)
                if normalised and entities.disease is None:
                    entities.disease = normalised
                    entities.confidence_scores["disease"] = score
                    entities.extraction_sources["disease"] = "ner"

            elif group == "Medication":
                therapy = word.lower()
                if therapy not in entities.prior_therapies:
                    entities.prior_therapies.append(therapy)
                    # Track best confidence across all therapies
                    prev = entities.confidence_scores.get("prior_therapies", 0.0)
                    entities.confidence_scores["prior_therapies"] = max(prev, score)
                    entities.extraction_sources["prior_therapies"] = "ner"

            elif group in ("Lab_value", "Detailed_description"):
                # Could be a biomarker
                biomarker = self._normalise_biomarker(word)
                if biomarker and biomarker not in entities.biomarkers:
                    entities.biomarkers.append(biomarker)
                    prev = entities.confidence_scores.get("biomarkers", 0.0)
                    entities.confidence_scores["biomarkers"] = max(prev, score)
                    entities.extraction_sources["biomarkers"] = "ner"

            elif group == "Sign_symptom":
                # Might indicate comorbidities
                comorb = word.lower()
                if comorb not in entities.comorbidities:
                    entities.comorbidities.append(comorb)
                    prev = entities.confidence_scores.get("comorbidities", 0.0)
                    entities.confidence_scores["comorbidities"] = max(prev, score)
                    entities.extraction_sources["comorbidities"] = "ner"

    def _apply_regex_fallback(
        self, entities: ExtractedEntities, text: str, silent: bool = False,
    ) -> None:
        """Fill any gaps left by the NER model using regex patterns.

        This is crucial for numeric / formatted fields that BioBERT
        often doesn't recognise as named entities.
        """
        def _log(msg: str) -> None:
            if not silent:
                safe_print(msg)

        _log("[NeuralExtractor] Running regex fallback ...")

        # Age
        if entities.age is None:
            m = self._RE_AGE.search(text)
            if m:
                age_str = m.group(1) or m.group(2)
                entities.age = int(age_str)
                entities.confidence_scores["age"] = 1.0
                entities.extraction_sources["age"] = "regex"
                _log(f"   [regex] age -> {entities.age}")

        # Gender
        if entities.gender is None:
            m = self._RE_GENDER.search(text)
            if m:
                raw = m.group(1).lower()
                entities.gender = "male" if raw in ("male", "man") else "female"
                entities.confidence_scores["gender"] = 1.0
                entities.extraction_sources["gender"] = "regex"
                _log(f"   [regex] gender -> {entities.gender}")

        # Stage
        if entities.stage is None:
            m = self._RE_STAGE.search(text)
            if m:
                entities.stage = m.group(1).upper()
                entities.confidence_scores["stage"] = 1.0
                entities.extraction_sources["stage"] = "regex"
                _log(f"   [regex] stage -> {entities.stage}")

        # Disease (if NER missed it)
        if entities.disease is None:
            m = self._RE_DISEASE.search(text)
            if m:
                entities.disease = self._normalise_disease(m.group(1))
                entities.confidence_scores["disease"] = 1.0
                entities.extraction_sources["disease"] = "regex"
                _log(f"   [regex] disease -> {entities.disease}")

        # BMI
        if entities.bmi is None:
            m = self._RE_BMI.search(text)
            if m:
                entities.bmi = float(m.group(1))
                entities.confidence_scores["bmi"] = 1.0
                entities.extraction_sources["bmi"] = "regex"
                _log(f"   [regex] bmi -> {entities.bmi}")

        # ECOG
        if entities.ecog_ps is None:
            m = self._RE_ECOG.search(text)
            if m:
                entities.ecog_ps = int(m.group(1))
                entities.confidence_scores["ecog_ps"] = 1.0
                entities.extraction_sources["ecog_ps"] = "regex"
                _log(f"   [regex] ecog_ps -> {entities.ecog_ps}")

        # Biomarkers
        for m in self._RE_BIOMARKER.finditer(text):
            bm = self._normalise_biomarker(m.group(1))
            if bm and bm not in entities.biomarkers:
                entities.biomarkers.append(bm)
                # Regex biomarkers get 1.0; upgrade source if NER also found some
                entities.confidence_scores.setdefault("biomarkers", 1.0)
                src = entities.extraction_sources.get("biomarkers", "regex")
                entities.extraction_sources["biomarkers"] = (
                    "ner+regex" if src == "ner" else "regex"
                )
                _log(f"   [regex] biomarker -> {bm}")

        # Comorbidities
        for m in self._RE_COMORBIDITY.finditer(text):
            comorb = m.group(1).lower()
            if comorb not in entities.comorbidities:
                entities.comorbidities.append(comorb)
                entities.confidence_scores.setdefault("comorbidities", 1.0)
                src = entities.extraction_sources.get("comorbidities", "regex")
                entities.extraction_sources["comorbidities"] = (
                    "ner+regex" if src == "ner" else "regex"
                )
                _log(f"   [regex] comorbidity -> {comorb}")

        # Prior therapies
        for m in self._RE_THERAPY.finditer(text):
            therapy = m.group(1).lower()
            if therapy not in entities.prior_therapies:
                entities.prior_therapies.append(therapy)
                entities.confidence_scores.setdefault("prior_therapies", 1.0)
                src = entities.extraction_sources.get("prior_therapies", "regex")
                entities.extraction_sources["prior_therapies"] = (
                    "ner+regex" if src == "ner" else "regex"
                )
                _log(f"   [regex] prior_therapy -> {therapy}")

    def _apply_negation_filter(
        self, entities: ExtractedEntities, text: str, silent: bool = False,
    ) -> None:
        """Remove entities mentioned in negated clinical contexts.

        Handles phrases like 'patient denies diabetes' or
        'no history of pembrolizumab' that would otherwise
        cause dangerous false-positive extractions.
        """
        negated_terms: list[str] = []
        for m in self._RE_NEGATION.finditer(text):
            negated_terms.append(m.group(1).strip().lower())

        if not negated_terms:
            return

        def _log(msg: str) -> None:
            if not silent:
                safe_print(msg)

        _log(f"[NeuralExtractor] Negation scan: {len(negated_terms)} cue(s)")

        def _is_negated(term: str) -> bool:
            t = term.lower()
            return any(t in neg or neg in t for neg in negated_terms)

        # Comorbidities
        kept_comorb: list[str] = []
        for c in entities.comorbidities:
            if _is_negated(c):
                entities.negated_fields.append(f"comorbidity:{c}")
                _log(f"   [negation] removed comorbidity -> {c}")
            else:
                kept_comorb.append(c)
        entities.comorbidities = kept_comorb

        # Prior therapies
        kept_rx: list[str] = []
        for rx in entities.prior_therapies:
            if _is_negated(rx):
                entities.negated_fields.append(f"therapy:{rx}")
                _log(f"   [negation] removed therapy -> {rx}")
            else:
                kept_rx.append(rx)
        entities.prior_therapies = kept_rx

        # Disease (only remove if explicitly negated, not primary dx)
        if entities.disease and _is_negated(entities.disease):
            entities.negated_fields.append(f"disease:{entities.disease}")
            _log(f"   [negation] flagged disease -> {entities.disease}")
            entities.disease = None
            entities.confidence_scores.pop("disease", None)
            entities.extraction_sources.pop("disease", None)

        # Biomarkers
        kept_bio: list[str] = []
        for bm in entities.biomarkers:
            if _is_negated(bm):
                entities.negated_fields.append(f"biomarker:{bm}")
                _log(f"   [negation] removed biomarker -> {bm}")
            else:
                kept_bio.append(bm)
        entities.biomarkers = kept_bio

    @staticmethod
    def _normalise_biomarker(raw: str) -> Optional[str]:
        """Light normalisation of biomarker strings."""
        text = raw.strip()
        if not text:
            return None
        # Capitalise gene names, keep +/- suffixes
        # e.g., "egfr+" → "EGFR+", "pd-l1 60%" → "PD-L1 60%"
        return text.upper().replace("PD-L1", "PD-L1").replace("PDL1", "PD-L1")

def main() -> None:
    """Quick smoke test with a single synthetic note."""
    sample_note = (
        "Patient is a 58-year-old male diagnosed with Stage IIIA NSCLC. "
        "Molecular testing shows EGFR+, PD-L1 60%. BMI is 24.5. "
        "ECOG performance status 1. No significant comorbidities. "
        "Prior therapies include carboplatin."
    )

    print("=" * 64)
    print("  EthiMatch — Neural Extractor Demo")
    print("=" * 64)
    print(f"\n📝 Input note:\n   \"{sample_note}\"\n")

    extractor = NeuralExtractor()
    result = extractor.extract(sample_note)

    print("\n" + "=" * 64)
    print("  Final Extracted Entities")
    print("=" * 64)
    for k, v in result.to_dict().items():
        print(f"  {k:20s}: {v}")

if __name__ == "__main__":
    main()
