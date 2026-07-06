# tofix42 Phase 7 Fine-Tuning Decision

## Purpose

Decide whether fine-tuning is justified from evidence. This phase is a gate, not
a training workflow.

The default recommendation should be `defer_fine_tuning` until:

- deterministic Phase 6 evaluation passes
- a real localhost JSON model probe report passes
- the probe report is not from `phase2_stub_runtime.py`
- enough reviewed bad-answer corrections exist
- graph audit and draft-plan fixtures stay reproducible
- retrieval citations remain mandatory

## Commands

Emit the current fine-tuning readiness decision:

```powershell
python "docs/Data Studio/tofix42/phase7_finetune_decision.py" decide
```

Use a saved real-model probe report:

```powershell
python "docs/Data Studio/tofix42/phase7_finetune_decision.py" decide `
  --real-model-probe-report "$env:TEMP/tofix42_phase2_probe_suite.json"
```

Generate that report with the Phase 2 real-model check:

```powershell
python "docs/Data Studio/tofix42/phase2_real_model_check.py" run `
  --endpoint "http://127.0.0.1:8766/completion" `
  --output "$env:TEMP/tofix42_phase2_probe_suite.json" `
  --capture-failures
```

Require a different reviewed-example threshold:

```powershell
python "docs/Data Studio/tofix42/phase7_finetune_decision.py" decide `
  --min-reviewed-examples 50
```

Run the deterministic Phase 7 gate:

```powershell
python "docs/Data Studio/tofix42/phase7_finetune_decision.py" check
```

## Output

Decision schema: `cyxwiz.tofix42.phase7.finetune_decision.v1`

The decision includes:

- `recommendation`
- `approved`
- criteria and evidence
- blocking criteria
- next actions
- non-goals

## Boundary

This command does not train, download, or tune a model. It does not weaken the
answer contract. If fine-tuning is ever approved later, retrieval remains the
truth layer and citations remain mandatory.
