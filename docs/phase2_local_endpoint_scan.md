# tofix42 Phase 2 Local Endpoint Scan

## Purpose

Check common local model endpoint locations before running the full real-model
validation sequence.

This command is read-only and local. It does not start servers, download
models, train, or call non-local endpoints.

## Command

```powershell
python "docs/Data Studio/tofix42/phase2_local_endpoint_scan.py" scan
```

It checks:

- `http://127.0.0.1:8765/completion`
- `http://127.0.0.1:8766/completion`
- `http://127.0.0.1:1234/v1/chat/completions`

The `/completion` endpoints use the Phase 2 endpoint doctor. The
OpenAI-compatible upstream uses a TCP reachability check only.

## Expected Interpretation

- `8765` as `stub`: JSON pipeline only; do not use as real-model evidence.
- `8766` as `real_candidate_or_unknown`: run `phase2_real_model_check.py`.
- `1234` reachable and `8766` not reachable: start
  `phase2_openai_compat_proxy.py`.
- `1234` not reachable: start your real local model server first.
