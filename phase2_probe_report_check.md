# tofix42 Phase 2 Probe Report Checker

## Purpose

Validate a saved Phase 2 probe-suite report without calling a model endpoint.

This is useful after running `phase2_probe_suite.py` against a real localhost
JSON model server. The checker reads the saved JSON report and verifies schema,
case coverage, expected citations, parsed sections, required terms, and
forbidden terms.

## Commands

Validate a saved report:

```powershell
python "docs/Data Studio/tofix42/phase2_probe_report_check.py" validate `
  --report "$env:TEMP/tofix42_phase2_probe_suite.json"
```

Emit validation JSON:

```powershell
python "docs/Data Studio/tofix42/phase2_probe_report_check.py" validate `
  --report "$env:TEMP/tofix42_phase2_probe_suite.json" `
  --json
```

Run the deterministic self-check:

```powershell
python "docs/Data Studio/tofix42/phase2_probe_report_check.py" check
```

## Output

Checker schema: `cyxwiz.tofix42.phase2.probe_report_check.v1`

The checker does not prove a model is good by itself. It only validates a saved
report produced by the Phase 2 probe suite.

Reports produced by `phase2_stub_runtime.py` are intentionally flagged with
`stub_runtime_detected`. They validate the JSON pipeline, but they do not count
as real-model evidence for Phase 7.
