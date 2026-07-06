# tofix42 Phase 3 Debug Context

## Purpose

Build the first Studio Debugger explanation slice without adding UI or requiring
a real model server.

This phase only creates a deterministic context packet for a selected debugger
trace. A later model/runtime call can use the packet, but this command does not
start a model, edit graphs, mutate source, or depend on Studio UI.

## Command

Run from the repository root:

```powershell
python "docs/Data Studio/tofix42/phase3_debug_context.py" context `
  --run ".cyxwiz/debug_runs/studio/<run-id>/session.json" `
  --pretty
```

Select a trace explicitly:

```powershell
python "docs/Data Studio/tofix42/phase3_debug_context.py" context `
  --run ".cyxwiz/debug_runs/studio/<run-id>/session.json" `
  --node-id 5 `
  --role "PreprocessingOutput" `
  --pretty
```

Run the deterministic gate:

```powershell
python "docs/Data Studio/tofix42/phase3_debug_context.py" check
```

Build a retrieval-backed answer packet for the selected trace:

```powershell
python "docs/Data Studio/tofix42/phase3_debug_context.py" packet `
  --run ".cyxwiz/debug_runs/studio/<run-id>/session.json" `
  --top 5 `
  --pretty
```

Pipe that packet into the existing Phase 1B prompt builder:

```powershell
python "docs/Data Studio/tofix42/phase3_debug_context.py" packet `
  --run ".cyxwiz/debug_runs/studio/<run-id>/session.json" `
  --top 5 |
  python "docs/Data Studio/tofix42/phase1b_answer.py" prompt --packet -
```

Generate a deterministic explanation without a model server:

```powershell
python "docs/Data Studio/tofix42/phase3_debug_context.py" explain `
  --run ".cyxwiz/debug_runs/studio/<run-id>/session.json"
```

Emit the same explanation as JSON:

```powershell
python "docs/Data Studio/tofix42/phase3_debug_context.py" explain `
  --run ".cyxwiz/debug_runs/studio/<run-id>/session.json" `
  --json `
  --pretty
```

## Input

The command accepts:

- `DebugRunStore` session JSON from `.cyxwiz/debug_runs/studio/<run-id>/session.json`
- support-bundle `debug_run` JSON
- a single `DebugTraceRecord` JSON object

It follows the engine field names serialized by `debug_run_store.cpp`:

- `run_id`
- `node_id`
- `node_name`
- `node_type`
- `phase`
- `role`
- `input_shape`
- `output_shape`
- `dtype`
- `duration_ms`
- `status`
- `issues`
- `payload`

## Output

Schema: `cyxwiz.tofix42.phase3.debug_trace_context.v1`

The packet includes:

- selected trace identity
- run summary
- selected trace fields
- same-node related traces
- related issues
- related Studio events
- related recommendations
- deterministic facts
- retrieval query hints
- answer contract rules

The `packet` command wraps this context into the existing
`cyxwiz.tofix42.phase1a.answer_packet.v1` shape. The extra `debug_context`
field is preserved for downstream callers, while Phase 1B can still consume the
packet because it already reads the standard `question`, `evidence`, and
`missing_evidence_notes` fields.

The `explain` command emits schema
`cyxwiz.tofix42.phase3.debug_trace_explanation.v1`. It is deterministic and
uses only selected trace facts, related debugger items, and retrieved source
citations. It is useful for validating the Studio Debugger explanation workflow
before a real localhost JSON model server is available.

The explanation contains:

- `answer`
- `where`
- `likely_why`
- `inspect_next`
- `trace_evidence`
- `source_evidence`
- `evidence`
- `unknowns`
- `unsupported_or_not_implemented`

`trace_evidence` cites selected trace fields such as
`selected_trace.status`, `selected_trace.role`, and
`selected_trace.issues[0].message`. `source_evidence` cites retrieved files and
line ranges from the Phase 1A index. The combined `evidence` list preserves both
for simple callers.

## Privacy Boundary

The packet redacts payload keys that may contain private local data:

- paths and files
- dataset names
- raw values and previews
- tokens, passwords, secrets, and credentials

This keeps the first debugger slice local and conservative while still passing
enough structured context to explain what happened.

## Phase Gate

This is not the Studio UI integration yet.

The context packet is now connected to the existing retrieval/answer harness,
and a deterministic explanation fallback exists. The next useful Phase 3 step
is validating real answer quality once a real localhost JSON model server is
available.
