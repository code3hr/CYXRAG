# tofix42 Phase 7 Fine-Tuning Experiment Plan

## Purpose

Define the first approved fine-tuning experiment without weakening the current
RAG contract.

This is an experiment plan only. It does not launch training.

## Current Gate Status

Approved inputs already exist:

- deterministic Phase 6 evaluation passes
- real localhost model probe passes through the accepted proxy path
- reviewed correction threshold is met
- graph audit and draft-plan fixtures are reproducible
- retrieval remains mandatory

Current approved runtime proof:

- model server: `http://127.0.0.1:1235/v1/chat/completions`
- proxy: `http://127.0.0.1:8768/completion`
- probe report:
  `$env:TEMP\tofix42_phase2_real_model_check_qwen3b_8768.json`

Current reviewed correction export:

- [phase6_reviewed_corrections.jsonl](</D:/Dev/CyxWiz_Claude/docs/Data Studio/tofix42/phase6_reviewed_corrections.jsonl>)

## Objective

Test whether a small fine-tuning run improves:

- section-format compliance
- citation-path inclusion
- refusal/qualification behavior for unsupported claims
- short answer accuracy on CyxWiz-specific retrieval-grounded prompts

without degrading:

- retrieval-first behavior
- citation discipline
- unsupported-feature refusal
- deterministic evaluation fixtures

## Non-Goals

- do not replace retrieval with model memory
- do not train on raw repository text alone
- do not train on unreviewed corrections
- do not tune the model to invent unsupported engine behavior
- do not broaden into Studio UI, graph mutation, or source mutation

## Dataset Provenance

Use only reviewed local artifacts already produced by tofix42:

Primary supervised source:

- [phase6_reviewed_corrections.jsonl](</D:/Dev/CyxWiz_Claude/docs/Data Studio/tofix42/phase6_reviewed_corrections.jsonl>)

Source lineage:

- original failure captures:
  [phase6_bad_answers.jsonl](</D:/Dev/CyxWiz_Claude/docs/Data Studio/tofix42/phase6_bad_answers.jsonl>)
- accepted retrieval source:
  [phase1a_index.json](</D:/Dev/CyxWiz_Claude/docs/Data Studio/tofix42/phase1a_index.json>)
- accepted runtime validation:
  `C:\Users\chick\AppData\Local\Temp\tofix42_phase2_real_model_check_qwen3b_8768.json`

Allowed example classes:

- probe questions over source file definitions
- probe questions over training trace facts
- probe questions over graph example files
- probe questions over explicit unsupported/compatibility behavior
- reviewed timeout or malformed-output corrections tied to a known answer packet

Disallowed example classes:

- free-form answers without expected citations
- answers produced without retrieval evidence
- speculative graph/source edits
- anything from non-local services

## Training Record Shape

Each training example should preserve three things:

1. the user query
2. the expected citation path
3. the reviewed corrected output with the required sections

Recommended target output format:

```text
Answer: ...
Evidence: ...
Unknowns: ...
Unsupported or not implemented: ...
```

The model should be trained to emit that format, not to skip retrieval.

## Split Strategy

Do not randomize blindly.

Split by case family so leakage stays low.

Recommended split:

- train:
  - most reviewed correction records
  - mixed source / trace / graph / unsupported-behavior examples
- validation:
  - at least one example from each family
  - hold out all records for 2 to 4 full case IDs
- test:
  - do not use reviewed correction records as the final acceptance test
  - use the live Phase 2 probe suite and deterministic Phase 6 / Phase 7 gates

Minimum holdout rule:

- no exact `case_id` may appear in both train and validation

## Baseline

Baseline model:

- `D:\tmp\models\qwen2.5-coder-3b-instruct-q4_k_m.gguf`

Baseline runtime path:

- `1235 -> 8768`

Baseline acceptance state:

- Phase 2 real-model probe accepted
- Phase 6 threshold met
- Phase 7 experiment approved

## Fine-Tuning Scope

Keep the first run small and reversible.

Recommended first experiment:

- one base model only
- one training corpus only
- one answer format only
- no multi-task objective
- no retrieval changes during the experiment

Train only for:

- better formatting compliance
- better citation-path copying
- better concise grounded answers

Do not optimize for:

- longer prose
- broader general knowledge
- graph mutation suggestions beyond current retrieval evidence

## Evaluation Criteria

A tuned model is only acceptable if all of these remain true:

1. `phase2_real_model_check.py` still passes against the tuned runtime.
2. `phase6_eval_capture.py check` still passes.
3. `phase7_finetune_decision.py check` still passes.
4. citation paths still appear when expected.
5. unsupported claims are still refused or qualified.
6. retrieval is still required in the inference path.

Required live checks after tuning:

```powershell
python "docs/Data Studio/tofix42/phase2_real_model_check.py" run `
  --endpoint "http://127.0.0.1:8768/completion" `
  --output "$env:TEMP\tofix42_phase2_real_model_check_post_tune.json" `
  --timeout-seconds 120 `
  --capture-failures `
  --json

python "docs/Data Studio/tofix42/phase6_eval_capture.py" check
python "docs/Data Studio/tofix42/phase7_finetune_decision.py" check
```

## Rejection Rules

Reject the tuned model immediately if any of these happen:

- Phase 2 probe acceptance drops
- expected citation paths disappear more often
- unsupported-feature refusal weakens
- answers become more verbose but less grounded
- direct retrieval relevance gets masked by memorized but uncited output
- the tuned model requires removing the proxy prompt contract to look good

## Rollback Criteria

Rollback is mandatory if the tuned model:

- fails any deterministic gate
- fails the accepted live Phase 2 probe suite
- lowers citation compliance
- raises unsupported-claim hallucination risk
- needs prompt hacks that the baseline model does not need

Rollback action:

- restore the baseline Qwen 3B model path
- keep the accepted `1235 -> 8768` runtime path
- retain the reviewed-correction corpus for a later, better experiment

## Operational Rules

- keep retrieval packets unchanged during the first tuning experiment
- keep the proxy answer contract unchanged during the first comparison
- compare tuned versus baseline on the same prompts
- save every post-tune report beside the baseline report

## Recommended Next Artifact

Create a small dataset-prep script that converts
[phase6_reviewed_corrections.jsonl](</D:/Dev/CyxWiz_Claude/docs/Data Studio/tofix42/phase6_reviewed_corrections.jsonl>)
into the exact training format required by the chosen tuning stack.
