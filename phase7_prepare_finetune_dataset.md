# tofix42 Phase 7 Dataset Prep

## Purpose

Convert reviewed correction records into a training-ready chat JSONL dataset for
the first fine-tuning experiment.

This step is local and read-only. It does not launch training.

## Input

Default input:

- [phase6_reviewed_corrections.jsonl](</D:/Dev/CyxWiz_Claude/docs/Data Studio/tofix42/phase6_reviewed_corrections.jsonl>)

Each input record must already include:

- `case_id`
- `query`
- `expected_citation`
- `failure_mode`
- `corrected_output`

The script validates that `corrected_output` parses into:

- `Answer`
- `Evidence`
- `Unknowns`
- `Unsupported or not implemented`

## Output

Default output directory:

- `docs/Data Studio/tofix42/phase7_dataset/`

Generated files:

- `train.chat.jsonl`
- `validation.chat.jsonl`
- `manifest.json`
- optional exported trainer variants such as:
  - `train.messages.jsonl`
  - `validation.messages.jsonl`
  - `train.instruction.jsonl`
  - `validation.instruction.jsonl`

Format:

- OpenAI-style chat training JSONL
- each record contains `messages`
- assistant target is the reviewed corrected output

## Command

```powershell
python "docs/Data Studio/tofix42/phase7_prepare_finetune_dataset.py" prepare `
  --json
```

Write to a different directory:

```powershell
python "docs/Data Studio/tofix42/phase7_prepare_finetune_dataset.py" prepare `
  --output-dir "docs/Data Studio/tofix42/phase7_dataset_alt" `
  --json
```

Change validation holdout groups per family:

```powershell
python "docs/Data Studio/tofix42/phase7_prepare_finetune_dataset.py" prepare `
  --validation-groups-per-family 2 `
  --json
```

Export the canonical dataset to plain `messages` JSONL:

```powershell
python "docs/Data Studio/tofix42/phase7_prepare_finetune_dataset.py" export-format `
  --format messages `
  --json
```

Export the canonical dataset to `instruction/input/output` JSONL:

```powershell
python "docs/Data Studio/tofix42/phase7_prepare_finetune_dataset.py" export-format `
  --format instruction `
  --json
```

## Split Rule

The script groups records by exact `case_id` and keeps all records for one
`case_id` on the same side of the split.

Default behavior:

- hold out one case-id group per family when the family has more than one group
- keep singleton families in train

This avoids exact case-id leakage across train and validation.

## Boundary

This script does not:

- tune a model
- modify retrieval packets
- weaken citation requirements
- use unreviewed records
