# tofix42 Phase 6 Evaluation and QA Capture

## Purpose

Measure the deterministic parts of the local assistant before any fine-tuning
discussion. This harness reuses existing fixtures from retrieval, debugger trace
explanation, training trace explanation, graph audit, and graph draft planning.

It does not call a model server, launch Studio, mutate graphs, or grade
subjective answer quality.

## Commands

Run the deterministic evaluation report:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" run
```

Write the report to a JSON file:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" run `
  --output "docs/Data Studio/tofix42/phase6_eval_report.json" `
  --json
```

List evaluation cases:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" list-cases
```

Capture a bad model answer for later review:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" capture-bad-answer `
  --case-id "phase2.manual.localhost.answer" `
  --query "What does DataLoader pin_memory guarantee today?" `
  --expected-citation "cyxwiz-engine/src/core/graph_compiler.cpp" `
  --actual-output "<paste model output>" `
  --failure-mode "missed_required_citation" `
  --reviewed-correction "pin_memory=true is unsupported by current batchers and may be ignored"
```

Capture failed cases from a saved Phase 2 probe-suite report:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" capture-probe-failures `
  --report "$env:TEMP/tofix42_phase2_probe_suite.json"
```

Summarize reviewed bad-answer corrections:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" review-status
```

List captured bad-answer records:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" list-bad-answers `
  --unreviewed
```

Show a review queue with command templates:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" review-queue
```

Show one captured bad-answer record in detail:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" show-bad-answer `
  --record-number 1
```

Mark a captured bad answer as reviewed by record number:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" review-bad-answer `
  --record-number 1 `
  --reviewed-correction "pin_memory=true is unsupported by current batchers and may be ignored; cite cyxwiz-engine/src/core/graph_compiler.cpp."
```

Mark a captured bad answer as reviewed by case filters:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" review-bad-answer `
  --case-id "phase2.probe.dataloader_pin_memory_truth" `
  --failure-mode "expected_path_missing_from_output,required_terms_missing" `
  --reviewed-correction "pin_memory=true is unsupported by current batchers and may be ignored; cite cyxwiz-engine/src/core/graph_compiler.cpp."
```

Require the reviewed-correction threshold:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" review-status `
  --require-threshold
```

Export reviewed corrections as JSONL training candidates:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" export-reviewed `
  --output "docs/Data Studio/tofix42/phase6_reviewed_corrections.jsonl"
```

Run the deterministic Phase 6 gate:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" check
```

## Output

Evaluation report schema: `cyxwiz.tofix42.phase6.eval_report.v1`

Bad-answer record schema: `cyxwiz.tofix42.phase6.bad_answer.v1`

Bad-answer review schema: `cyxwiz.tofix42.phase6.bad_answer_review.v1`

Bad-answer review queue schema:
`cyxwiz.tofix42.phase6.bad_answer_review_queue.v1`

Probe failure capture schema:
`cyxwiz.tofix42.phase6.probe_failure_capture.v1`

Reviewed correction example schema:
`cyxwiz.tofix42.phase6.reviewed_correction_example.v1`

The default bad-answer log path is
`docs/Data Studio/tofix42/phase6_bad_answers.jsonl`.

## Boundary

This phase captures reproducible QA facts and reviewed corrections. It does not
decide that fine-tuning is useful, does not train a model, and does not replace
retrieval citations as the source of truth.
