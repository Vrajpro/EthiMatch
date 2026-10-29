# 2. Related work

**Target: ~700 words, three subsections. Keep tight — this is not a survey.**

## 2.1 Biomedical NLP for clinical information extraction

- BioBERT (Lee et al., 2020) and ClinicalBERT (Alsentzer et al., 2019) as the standard pre-trained backbones.
- Negation and hedging handling: NegEx (Chapman et al., 2001) and transformer-era successors.
- Position EthiMatch as a **consumer** of such models (we use `d4data/biomedical-ner-all` via Hugging Face), not a new NER architecture.

## 2.2 Automated clinical trial matching

- Rule-based lineage: EliXR, Criteria2Query (Yuan et al., 2019).
- LLM-based matchers: TrialGPT (Jin et al., 2023), DeepEnroll (Zhang et al., 2020).
- Framing: pure-neural matchers typically return a ranked score; few expose structured evidence per criterion and fewer still formalise an INCONCLUSIVE outcome.

## 2.3 Neuro-symbolic approaches in clinical AI

- Garcez & Lamb (2020) framing; applications in clinical decision support.
- Argument: in a safety-adjacent setting, the symbolic layer is not nostalgia — it is the mechanism that lets you refuse to decide when evidence is missing.

## 2.4 Gap statement (two sentences, closes the section)

Existing trial-matching systems either (a) hide the rule layer inside the model or (b) assume complete structured input. EthiMatch addresses both: an explicit rule layer, operating on partial NER output, with INCONCLUSIVE as a first-class return value.

---

<!-- Final prose below this line. -->
