# tofix42 Phase 2 Model Validation

## Purpose

Use this checklist when a real local JSON-serving model runtime is available.

This does not replace Phase 1A retrieval checks or Phase 1B adapter checks. It
validates whether a manually started local model can follow the strict prompt
contract over retrieved CyxWiz evidence.

## Prerequisites

- Phase 1A index is fresh.
- Phase 1A `check` passes.
- Phase 1B `check` passes.
- A local JSON runtime is already running on `localhost`, `127.0.0.1`, or `::1`.
- The runtime accepts the Phase 2 JSON request body:

```json
{
  "prompt": "<strict Phase 1B prompt>",
  "n_predict": 384,
  "stream": false
}
```

## Acceptance Rules

For each case:

- `probe` returns `ok: true`.
- `sections_missing` is empty.
- the answer cites or names the expected evidence path.
- engine-specific claims come from the provided evidence.
- unsupported or missing behavior is called out instead of invented.
- no graph edit, source edit, training run, model download, or external network
  call is triggered.

## Probe Cases

Use `D:/tmp/tofix42_probe_packet.json` as the temporary packet path.

Run all cases as a suite:

```powershell
python "docs/Data Studio/tofix42/phase2_probe_suite.py" `
  --endpoint "http://127.0.0.1:8765/completion" `
  --output "$env:TEMP/tofix42_phase2_probe_suite.json" `
  --json
```

Validate a saved suite report without calling the model again:

```powershell
python "docs/Data Studio/tofix42/phase2_probe_report_check.py" validate `
  --report "$env:TEMP/tofix42_phase2_probe_suite.json"
```

List suite cases:

```powershell
python "docs/Data Studio/tofix42/phase2_probe_suite.py" --list-cases
```

Run one case:

```powershell
python "docs/Data Studio/tofix42/phase2_probe_suite.py" `
  --endpoint "http://127.0.0.1:8765/completion" `
  --case "dataloader_pin_memory_truth" `
  --json
```

Capture a failing case for review:

```powershell
python "docs/Data Studio/tofix42/phase2_probe_suite.py" `
  --endpoint "http://127.0.0.1:8765/completion" `
  --case "dataloader_pin_memory_truth" `
  --include-raw-output `
  --include-prompt `
  --output "$env:TEMP/tofix42_bad_answer_capture.json" `
  --json
```

The suite checks expected top evidence, response section completeness, and
expected-path citation in the model output, plus small case-specific term
guards. It records each case's top citation and can write a JSON report for
review. Each case includes `model_output_sections` so the parsed answer,
evidence, unknowns, and unsupported sections can be reviewed without rerunning
the model. Raw model output and the full prompt are included only when the
capture flags are explicitly set.

### 1. Debug Trace Record Definition

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" packet "What source file defines DebugTraceRecord" --top 1 --json > "D:/tmp/tofix42_probe_packet.json"
python "docs/Data Studio/tofix42/phase1b_answer.py" probe --packet "D:/tmp/tofix42_probe_packet.json" --endpoint "http://127.0.0.1:8765/completion" --json
```

Expected evidence path:

```text
cyxwiz-engine/src/core/debug_trace_record.h
```

### 2. Training Trace Terminal Reason

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" packet "TrainingTraceEvent terminal_reason field" --top 1 --json > "D:/tmp/tofix42_probe_packet.json"
python "docs/Data Studio/tofix42/phase1b_answer.py" probe --packet "D:/tmp/tofix42_probe_packet.json" --endpoint "http://127.0.0.1:8765/completion" --json
```

Expected evidence path:

```text
cyxwiz-engine/src/core/training_trace_collector.h
```

### 3. TF-IDF Sentiment Graph

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" packet "TFIDFVectorizer sentiment graph" --top 1 --json > "D:/tmp/tofix42_probe_packet.json"
python "docs/Data Studio/tofix42/phase1b_answer.py" probe --packet "D:/tmp/tofix42_probe_packet.json" --endpoint "http://127.0.0.1:8765/completion" --json
```

Expected evidence path:

```text
examples/cyxgraph/Sentiment analysis/sentiment_analysis_tfidf_mlp_classifier.cyxgraph
```

### 4. DataLoader pin_memory Truth

```powershell
$q = "DataLoader pin_memory unsupported current " + "batchers compatibility"
python "docs/Data Studio/tofix42/phase1a_retrieval.py" packet $q --top 1 --json > "D:/tmp/tofix42_probe_packet.json"
python "docs/Data Studio/tofix42/phase1b_answer.py" probe --packet "D:/tmp/tofix42_probe_packet.json" --endpoint "http://127.0.0.1:8765/completion" --json
```

Expected evidence path:

```text
cyxwiz-engine/src/core/graph_compiler.cpp
```

Expected answer behavior:

- says `pin_memory=true` is serialized for compatibility
- says current batchers ignore it
- says no pinned host-memory transfer backend exists yet
- does not claim CUDA pinned transfers are implemented

### 5. TFIDFVectorizer min_df Validation

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" packet "TFIDFVectorizer min_df must be >= 1 Configure" --top 1 --json > "D:/tmp/tofix42_probe_packet.json"
python "docs/Data Studio/tofix42/phase1b_answer.py" probe --packet "D:/tmp/tofix42_probe_packet.json" --endpoint "http://127.0.0.1:8765/completion" --json
```

Expected evidence path:

```text
cyxwiz-engine/src/core/node_executors/tfidf_vectorizer_operator.cpp
```

## Failure Handling

If `probe` returns `ok: false`:

- inspect `sections_missing`
- inspect `error`
- inspect whether the model omitted required headings
- keep the model out of Studio UI until the failure is understood

If the model gives unsupported CyxWiz claims:

- record the prompt and output as a bad-answer fixture
- do not compensate by widening the prompt until retrieval evidence is checked
- prefer improving retrieved evidence before adding model-specific hacks
