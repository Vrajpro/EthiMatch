# MIMIC-IV Access Guide for EthiMatch

EthiMatch requires **MIMIC-IV-Note** (de-identified discharge summaries) for thesis-grade evaluation on real clinical text.

## Step 1: Create a PhysioNet Account

1. Go to [https://physionet.org/register/](https://physionet.org/register/)
2. Complete registration with your institutional email if possible.

## Step 2: Complete Credentialing (CITI Training)

1. Visit [https://physionet.org/settings/credentialing/](https://physionet.org/settings/credentialing/)
2. Complete the **CITI "Data or Specimens Only Research"** course (or approved equivalent).
3. Upload your completion certificate to PhysioNet.
4. Approval typically takes **1–4 weeks** — apply as early as possible.

## Step 3: Sign the MIMIC-IV Data Use Agreement

1. Go to [https://physionet.org/content/mimiciv/2.2/](https://physionet.org/content/mimiciv/2.2/)
2. Click **Request Access** and sign the DUA with your supervisor as co-signer if required by your institution.
3. Also request access to **MIMIC-IV-Note**:
   [https://physionet.org/content/mimic-iv-note/2.2/](https://physionet.org/content/mimic-iv-note/2.2/)

## Step 4: Download Discharge Summaries

After approval, download discharge note files and place them here:

```
ethimatch/data/mimic/discharge.csv.gz
```

Supported filenames:
- `discharge.csv.gz`
- `discharge.csv`
- `note/discharge.csv.gz`

Required CSV columns: `note_id` (or `id`) and `text` (or similar note body column).

## Step 5: Use in EthiMatch

```python
from mock_database import get_data_source

# Loads up to 200 MIMIC notes (falls back to synthetic if files missing)
ds = get_data_source("mimic", limit=200)
print(ds.source_name())
print(ds.get_patient_note(ds.get_all_patients()[0].patient_id)[:200])
```

Evaluation on MIMIC notes (pipeline only, no gold labels until you annotate):

```bash
python evaluation.py --source mimic --limit 100 --skip-gold
```

## Step 6: Annotation for Gold Standard (Thesis)

For distinction-level evaluation:

1. Randomly sample 100–200 MIMIC notes.
2. Have a clinician (or you, with protocol) label eligibility per trial.
3. Save labels to `data/mimic/gold_standard.json`:

```json
{
  "MIMIC-12345": {"NCT-FAKE-001": false, "NCT-FAKE-002": false}
}
```

4. Run: `python evaluation.py --source mimic --gold-file data/mimic/gold_standard.json`

## Institutional Ethics

Confirm with your university ethics board whether MIMIC-only evaluation requires separate IRB approval (often exempt as secondary use of de-identified data).
