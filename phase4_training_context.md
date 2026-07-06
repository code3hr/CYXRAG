# tofix42 Phase 4 Training Trace Context

## Purpose

Explain the latest training terminal state from local training trace JSON before
adding UI or relying on a real model server.

This slice is deterministic. It reads persisted `TrainingTraceCollector` JSON,
support-bundle `training_trace` JSON, or stdin, then reports what happened,
where it happened, the terminal reason, and what to inspect next.

## Commands

Run from the repository root.

Build context:

```powershell
python "docs/Data Studio/tofix42/phase4_training_context.py" context `
  --trace ".cyxwiz/debug_runs/current_training_trace.json" `
  --pretty
```

Explain the terminal state:

```powershell
python "docs/Data Studio/tofix42/phase4_training_context.py" explain `
  --trace ".cyxwiz/debug_runs/current_training_trace.json"
```

Build a retrieval-backed answer packet:

```powershell
python "docs/Data Studio/tofix42/phase4_training_context.py" packet `
  --trace ".cyxwiz/debug_runs/current_training_trace.json" `
  --top 5 `
  --pretty
```

Pipe that packet into the Phase 1B prompt builder:

```powershell
python "docs/Data Studio/tofix42/phase4_training_context.py" packet `
  --trace ".cyxwiz/debug_runs/current_training_trace.json" `
  --top 5 |
  python "docs/Data Studio/tofix42/phase1b_answer.py" prompt --packet -
```

Emit explanation JSON:

```powershell
python "docs/Data Studio/tofix42/phase4_training_context.py" explain `
  --trace ".cyxwiz/debug_runs/current_training_trace.json" `
  --json `
  --pretty
```

Run the deterministic gate:

```powershell
python "docs/Data Studio/tofix42/phase4_training_context.py" check
```

## Input

The command accepts the persisted training trace shape:

- `run_id`
- `status`
- `events`
- `materialization_events`
- `warnings`

It also accepts support-bundle `training_trace` JSON using `recent_events`.

## Output

Context schema: `cyxwiz.tofix42.phase4.training_trace_context.v1`

Explanation schema: `cyxwiz.tofix42.phase4.training_trace_explanation.v1`

The `packet` command emits the existing
`cyxwiz.tofix42.phase1a.answer_packet.v1` shape, with `training_context`
preserved for downstream callers. Phase 1B can consume it because the standard
`question`, `evidence`, and `missing_evidence_notes` fields remain unchanged.

The explanation includes:

- `answer`
- `where`
- `likely_why`
- `inspect_next`
- `trace_evidence`
- `source_evidence`
- `unknowns`
- `unsupported_or_not_implemented`

`trace_evidence` cites fields such as
`terminal_event.terminal_reason`, `terminal_event.status`, and
`run_summary.latest_stage`. `source_evidence` cites retrieved source lines from
the Phase 1A index.

## Boundary

This slice does not diagnose curves, mutate graphs, restart training, open
checkpoints, or treat warnings as proven root causes without terminal-event
support.
