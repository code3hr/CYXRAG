# tofix42 Phase 2 Handoff

## Status

Phase 2's local-runtime slice is functionally complete as an optional JSON HTTP
adapter plus validation harness. It is paused at the external boundary: a real
manually started localhost model server is still needed for accepted
real-model evidence.

It proves:

- Phase 1A packets and Phase 1B prompts can remain unchanged
- a local JSON runtime can be configured with `--runtime json-http`
- a manually started local JSON runtime can be validated with `probe`
- runtime answers still use `cyxwiz.tofix42.phase1b.answer.v1`
- runtime failures still use the structured `runtime_error` envelope
- `doctor` can report JSON endpoint configuration without probing it
- the adapter does not auto-start a server
- the adapter does not download models
- the adapter rejects non-local endpoints before any request is made
- deterministic checks cover JSON response parsing, HTTP success, HTTP failure,
  and endpoint rejection
- `phase2_stub_runtime.py` verifies the cross-process localhost adapter path
  without a real model
- `phase2_endpoint_doctor.py` checks reachability and stub detection
- `phase2_openai_compat_proxy.py` bridges local OpenAI-compatible chat servers
  to the tofix42 `/completion` contract
- `phase2_real_model_check.py` runs the endpoint doctor, probe suite, saved
  report validation, optional failure capture, and Phase 7 decision summary
- manual `llama-cli` validation did not produce a usable answer; it hung in the
  subprocess path and was interrupted

It intentionally does not include:

- starting or managing a model server
- downloading or installing a model
- calling a real model endpoint during checks
- embeddings
- vector database
- Studio UI
- graph mutation
- source mutation
- fine-tuning

## Artifacts

- `phase1b_answer.py`: now includes the optional `json-http` runtime path
- `phase1b_answer.md`: documents JSON runtime commands and response shapes
- `phase2_stub_runtime.py`: localhost-only stub server for end-to-end adapter
  testing without a model
- `phase2_model_validation.md`: real local model validation checklist and
  probe cases
- `phase2_probe_suite.py`: runs the Phase 2 model validation cases against a
  localhost JSON endpoint
- `phase2_probe_report_check.py`: validates saved probe-suite reports and
  rejects stub runtime evidence
- `phase2_endpoint_doctor.py`: probes local endpoint reachability and reports
  stub versus real-candidate runtime kind
- `phase2_local_endpoint_scan.py`: scans common local Phase 2 endpoint
  locations before running full validation
- `phase2_openai_compat_proxy.py`: localhost-only adapter from `/completion` to
  OpenAI-compatible `/v1/chat/completions`
- `phase2_real_model_check.py`: one-command real-model validation sequence with
  readiness and next-action summaries
- `phase2_runtime.md`: records the runtime boundary and acceptance criteria
- `usage.md`: rolling commands and current status

## Current Commands

Check a local endpoint configuration without probing it:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" doctor `
  --packet "docs/Data Studio/tofix42/phase1b_test_packet.json" `
  --runtime json-http `
  --endpoint "http://127.0.0.1:8080/completion" `
  --json
```

Call a running local endpoint:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" answer `
  --packet "docs/Data Studio/tofix42/phase1b_test_packet.json" `
  --runtime json-http `
  --endpoint "http://127.0.0.1:8080/completion" `
  --max-tokens 384 `
  --timeout-seconds 120 `
  --json
```

Run the deterministic adapter gate:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" check --packet "docs/Data Studio/tofix42/phase1b_test_packet.json"
```

Start the stub runtime manually:

```powershell
python "docs/Data Studio/tofix42/phase2_stub_runtime.py" --port 8765
```

Call the stub runtime from another shell:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" answer `
  --packet "docs/Data Studio/tofix42/phase1b_test_packet.json" `
  --runtime json-http `
  --endpoint "http://127.0.0.1:8765/completion" `
  --max-tokens 384 `
  --timeout-seconds 30 `
  --json
```

Probe whether the stub or a real local JSON model returns parseable answer
sections:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" probe `
  --packet "docs/Data Studio/tofix42/phase1b_test_packet.json" `
  --endpoint "http://127.0.0.1:8765/completion" `
  --max-tokens 384 `
  --timeout-seconds 30 `
  --json
```

Run the full Phase 2 probe suite:

```powershell
python "docs/Data Studio/tofix42/phase2_probe_suite.py" `
  --endpoint "http://127.0.0.1:8765/completion" `
  --output "$env:TEMP/tofix42_phase2_probe_suite.json" `
  --json
```

Run the full real-model validation sequence:

```powershell
python "docs/Data Studio/tofix42/phase2_real_model_check.py" run `
  --endpoint "http://127.0.0.1:8766/completion" `
  --output "$env:TEMP/tofix42_phase2_probe_suite.json" `
  --capture-failures
```

## Endpoint Rule

Allowed hosts:

- `localhost`
- `127.0.0.1`
- `::1`

All other hosts are rejected before the adapter opens a request.

## Current Request Contract

The adapter posts:

```json
{
  "prompt": "<strict Phase 1B prompt>",
  "n_predict": 384,
  "stream": false
}
```

Accepted response text fields:

- `content`
- `response`
- `completion`
- `generated_text`
- `text`
- `choices[0].message.content`
- `choices[0].text`

## Verification

Last verified gates:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" status
python "docs/Data Studio/tofix42/phase1a_retrieval.py" check
python "docs/Data Studio/tofix42/phase1b_answer.py" check --packet "docs/Data Studio/tofix42/phase1b_test_packet.json"
```

Expected results:

- Phase 1A index is fresh
- all Phase 1A retrieval checks pass
- all Phase 1B adapter checks pass
- Phase 2 probe suite passes against `phase2_stub_runtime.py`
- `phase2_real_model_check.py` rejects the stub as real-model evidence
- `phase2_real_model_check.py` reports `real_model_probe_accepted` separately
  from `fine_tuning_ready`
- manual stub runtime returns a `json-http` answer envelope with parsed model
  output sections
- `probe` returns `ok: true` when all expected answer sections are parseable

## Next Gate

Do not broaden into Studio UI, embeddings, vector search, graph generation, or
mutation yet.

The next useful gate is real local model validation:

- start a real local JSON-serving model or an OpenAI-compatible local server
- if using OpenAI-compatible `/v1/chat/completions`, start
  `phase2_openai_compat_proxy.py` on port `8766`
- run `phase2_real_model_check.py run` against the real endpoint or proxy
- inspect `readiness.real_model_probe_accepted`
- review captured failures with the Phase 6 bad-answer workflow
- do not use `llama-cli` for Phase 2 validation unless its process behavior is
  fixed outside the adapter

If no local JSON server is available, pause Phase 2 implementation and keep the
current command harness plus `phase2_stub_runtime.py` as the completed runtime
boundary.

`probe` only reports `ok: true` when all expected sections are present:

- `answer`
- `evidence`
- `unknowns`
- `unsupported_or_not_implemented`

Missing sections are reported in `sections_missing`.
