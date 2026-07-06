# tofix42 Phase 2 Endpoint Doctor

## Purpose

Check whether a local JSON runtime endpoint is reachable and whether it looks
like the tofix42 stub runtime.

This is a shape/reachability check only. It does not run the full probe suite
and does not prove model answer quality.

## Commands

Probe the default endpoint:

```powershell
python "docs/Data Studio/tofix42/phase2_endpoint_doctor.py" check
```

Probe a custom local endpoint:

```powershell
python "docs/Data Studio/tofix42/phase2_endpoint_doctor.py" check `
  --endpoint "http://127.0.0.1:8765/completion"
```

Run the deterministic self-check:

```powershell
python "docs/Data Studio/tofix42/phase2_endpoint_doctor.py" self-check
```

## Output

Doctor schema: `cyxwiz.tofix42.phase2.endpoint_doctor.v1`

`runtime_kind` is one of:

- `stub`
- `real_candidate_or_unknown`
- `unreachable_or_error`
- `rejected_non_local_endpoint`

If the endpoint is classified as `stub`, it can validate the JSON pipeline but
does not count as real-model evidence.
