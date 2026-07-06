# tofix42 Phase 2 OpenAI-Compatible Proxy

## Purpose

Bridge the tofix42 local `/completion` contract to a manually started local
OpenAI-compatible chat endpoint.

This is useful when a local model server exposes `/v1/chat/completions` instead
of the simpler tofix42 Phase 2 JSON shape.

The proxy does not start a model, download a model, call non-local endpoints, or
validate answer quality by itself.

## Start

Start your local model server first. Common local upstream shape:

```text
http://127.0.0.1:1234/v1/chat/completions
```

Then start the proxy:

```powershell
python "docs/Data Studio/tofix42/phase2_openai_compat_proxy.py" serve `
  --upstream "http://127.0.0.1:1234/v1/chat/completions" `
  --model "local-model" `
  --port 8766
```

Run the deterministic proxy self-check without a real model:

```powershell
python "docs/Data Studio/tofix42/phase2_openai_compat_proxy.py" self-check
```

Probe through the proxy:

```powershell
python "docs/Data Studio/tofix42/phase2_probe_suite.py" `
  --endpoint "http://127.0.0.1:8766/completion" `
  --output "$env:TEMP/tofix42_phase2_probe_suite.json" `
  --json
```

Validate the saved report:

```powershell
python "docs/Data Studio/tofix42/phase2_probe_report_check.py" validate `
  --report "$env:TEMP/tofix42_phase2_probe_suite.json"
```

## Request Translation

Incoming tofix42 request:

```json
{
  "prompt": "<strict Phase 1B prompt>",
  "n_predict": 384,
  "stream": false
}
```

Forwarded OpenAI-compatible request:

```json
{
  "model": "local-model",
  "messages": [
    {
      "role": "user",
      "content": "<strict Phase 1B prompt>"
    }
  ],
  "max_tokens": 384,
  "stream": false,
  "temperature": 0
}
```

## Boundary

Both proxy bind host and upstream endpoint must be local:

- `localhost`
- `127.0.0.1`
- `::1`

The proxy is an adapter only. A passing proxy self-check does not count as a
real-model probe. Phase 7 still requires a saved probe-suite report from a real
local model and reviewed correction examples.

The self-check starts a temporary fake local OpenAI-compatible upstream,
forwards one prompt, verifies the translated request shape, and shuts the fake
server down.
