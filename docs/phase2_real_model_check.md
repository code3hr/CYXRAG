# tofix42 Phase 2 Real-Model Check

## Purpose

Run the real-model validation sequence against a localhost JSON endpoint in one
command.

This command orchestrates existing tools:

- endpoint doctor
- Phase 2 probe suite
- offline probe report validation
- optional Phase 6 bad-answer capture
- Phase 7 decision summary

It does not start a model server, download a model, call non-local endpoints,
train a model, or weaken the cited-answer contract.

## Run

Direct `/completion` endpoint:

```powershell
python "docs/Data Studio/tofix42/phase2_real_model_check.py" run `
  --endpoint "http://127.0.0.1:8765/completion" `
  --output "$env:TEMP/tofix42_phase2_probe_suite.json"
```

OpenAI-compatible proxy endpoint:

```powershell
python "docs/Data Studio/tofix42/phase2_real_model_check.py" run `
  --endpoint "http://127.0.0.1:8766/completion" `
  --output "$env:TEMP/tofix42_phase2_probe_suite.json"
```

Capture failed probe cases into the Phase 6 bad-answer log:

```powershell
python "docs/Data Studio/tofix42/phase2_real_model_check.py" run `
  --endpoint "http://127.0.0.1:8766/completion" `
  --output "$env:TEMP/tofix42_phase2_probe_suite.json" `
  --capture-failures
```

Include raw model output and prompts in the saved probe report:

```powershell
python "docs/Data Studio/tofix42/phase2_real_model_check.py" run `
  --endpoint "http://127.0.0.1:8766/completion" `
  --output "$env:TEMP/tofix42_phase2_probe_suite.json" `
  --include-raw-output `
  --include-prompt `
  --capture-failures
```

## Exit Code

Exit code `0` means the saved probe-suite report validated as a real-model
candidate report.

Exit code `1` means the endpoint, probe suite, report validation, or write path
failed. Stub reports fail validation and do not count as real-model evidence.

When validation fails, text output includes failed case names, failure tags,
expected evidence paths, top retrieved paths, and runtime errors when present.
The full prompt and raw model output are only saved when requested with
`--include-prompt` and `--include-raw-output`.

The report also includes `next_actions`, derived from endpoint doctor,
validation, capture, and Phase 7 decision results.

The `readiness` block separates two states:

- `real_model_probe_accepted`: the saved probe report passed as real-model evidence
- `fine_tuning_ready`: Phase 7 approved the fine-tuning experiment gate

Phase 7 can still defer fine-tuning even when this command passes, because it
also requires enough reviewed correction examples.
