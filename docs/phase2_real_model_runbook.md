# tofix42 Phase 2 Real Model Runbook

## Purpose

Validate a manually started localhost JSON model server against the strict
tofix42 answer contract.

This runbook does not use `llama-cli`. The current validation path is a JSON
HTTP endpoint on `localhost`, `127.0.0.1`, or `::1`.

If your local model server exposes an OpenAI-compatible
`/v1/chat/completions` endpoint instead of this `/completion` shape, use
`phase2_openai_compat_proxy.py` to bridge it.

## Required Endpoint Contract

Request:

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

## Run

After starting your local JSON model server, run:

```powershell
python "docs/Data Studio/tofix42/phase2_probe_suite.py" `
  --endpoint "http://127.0.0.1:8765/completion" `
  --output "$env:TEMP/tofix42_phase2_probe_suite.json" `
  --json
```

Or run the whole validation sequence in one command:

```powershell
python "docs/Data Studio/tofix42/phase2_real_model_check.py" run `
  --endpoint "http://127.0.0.1:8765/completion" `
  --output "$env:TEMP/tofix42_phase2_probe_suite.json" `
  --capture-failures
```

Then validate the saved report offline:

```powershell
python "docs/Data Studio/tofix42/phase2_probe_report_check.py" validate `
  --report "$env:TEMP/tofix42_phase2_probe_suite.json"
```

If the endpoint is `phase2_stub_runtime.py`, the checker will flag
`stub_runtime_detected`. That validates the JSON pipeline only; it does not
count as real-model evidence.

If the report passes, feed it into the Phase 7 decision gate:

```powershell
python "docs/Data Studio/tofix42/phase7_finetune_decision.py" decide `
  --real-model-probe-report "$env:TEMP/tofix42_phase2_probe_suite.json"
```

## OpenAI-Compatible Local Server Bridge

Start your local OpenAI-compatible model server first, then run:

```powershell
python "docs/Data Studio/tofix42/phase2_openai_compat_proxy.py" serve `
  --upstream "http://127.0.0.1:1234/v1/chat/completions" `
  --model "local-model" `
  --port 8766
```

In a second PowerShell window, run the probe suite through the proxy:

```powershell
python "docs/Data Studio/tofix42/phase2_probe_suite.py" `
  --endpoint "http://127.0.0.1:8766/completion" `
  --output "$env:TEMP/tofix42_phase2_probe_suite.json" `
  --json
```

Or run the whole validation sequence through the proxy:

```powershell
python "docs/Data Studio/tofix42/phase2_real_model_check.py" run `
  --endpoint "http://127.0.0.1:8766/completion" `
  --output "$env:TEMP/tofix42_phase2_probe_suite.json" `
  --capture-failures
```

If the report fails, capture failed cases into the Phase 6 bad-answer log:

```powershell
python "docs/Data Studio/tofix42/phase6_eval_capture.py" capture-probe-failures `
  --report "$env:TEMP/tofix42_phase2_probe_suite.json"
```

## Failure Handling

If validation fails:

- inspect the named failed case
- check `sections_missing`
- check whether the expected evidence path appears in model output
- check `required_terms_missing` and `forbidden_terms_present`
- capture reviewed corrections with Phase 6 before any fine-tuning discussion

## Boundary

Do not use a non-local endpoint. Do not broaden into Studio UI, embeddings,
fine-tuning, graph mutation, or source mutation until this validation path is
understood.
