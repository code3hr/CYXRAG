# tofix42 Phase 2 Runtime Boundary

## Scope

Phase 2 follows `implementation/init_call_plan.md`: connect a small local answer model to
retrieved context while keeping retrieval as the truth layer.

The first Phase 2 slice should add one local JSON runtime boundary without
changing Phase 1A packets or Phase 1B answer envelopes.

Status: first slice complete; see `phase2_handoff.md`.

Real local model validation cases are listed in `phase2_model_validation.md`.

## Current Starting Point

Available now:

- Phase 1A lexical retrieval and answer packets
- Phase 1A freshness and success checks
- Phase 1B strict prompt builder
- Phase 1B runtime-unavailable answer envelope
- Phase 1B optional `llama-cli` smoke adapter
- Phase 2 optional `json-http` local runtime adapter
- Phase 1B structured runner error envelope
- Phase 1B output sentinel stripping

Not available in the checked local llama.cpp release directory:

- `llama-server.exe`

The observed local release directory contains `llama-cli.exe` only. Do not build
Phase 2 around `llama-server` until the executable or an equivalent local JSON
server is present.

## Runtime Interface

Keep the boundary small:

Input:

- prompt text from `phase1b_answer.py`
- max output tokens
- timeout seconds
- local endpoint or executable path

Output:

- raw model text
- structured runtime error on failure
- no graph edits
- no source edits
- no training side effects

The answer envelope stays:

```text
cyxwiz.tofix42.phase1b.answer.v1
```

Phase 2 should add a runtime backend, not a new answer schema unless a real
contract gap appears.

## Preferred JSON Runtime

Prefer a local JSON-serving runtime over more stdout parsing.

Candidate shape:

```text
Phase 1A packet -> Phase 1B prompt -> local JSON runtime -> Phase 1B answer
```

Implementation constraints:

- use stdlib client code first if possible
- keep endpoint, max tokens, and timeout configurable
- do not auto-start a server in the first slice
- do not download a model
- do not send code, traces, graphs, or docs to network services
- treat runtime unavailable as a normal result
- add deterministic tests with stubbed JSON responses before real model tests

Implemented first slice:

- `--runtime json-http`
- configurable `--endpoint`
- no endpoint probe in `doctor`
- no server auto-start
- no model download
- localhost-only endpoint enforcement
- stdlib-only HTTP client
- deterministic checks with stubbed success and failure payloads
- deterministic localhost fixture check for actual HTTP success and failure
- deterministic check that non-local endpoints are rejected before request
- `phase2_stub_runtime.py` for cross-process localhost adapter testing without
  a model
- manual stub run verified `json-http` answer envelopes and parsed sections
- `probe` command validates manually started JSON runtime answer sections
- `probe` reports `ok: true` only when all expected answer sections are present

Current request body:

```json
{
  "prompt": "<strict Phase 1B prompt>",
  "n_predict": 384,
  "stream": false
}
```

Accepted text fields:

- `content`
- `response`
- `completion`
- `generated_text`
- `text`
- `choices[0].message.content`
- `choices[0].text`

Endpoint rule:

- allowed: `localhost`, `127.0.0.1`, `::1`
- rejected: any non-local host

Manual stub endpoint:

```powershell
python "docs/Data Studio/tofix42/phase2_stub_runtime.py" --port 8765
```

Manual probe:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" probe `
  --packet "docs/Data Studio/tofix42/phase1b_test_packet.json" `
  --endpoint "http://127.0.0.1:8765/completion" `
  --json
```

Probe reports missing answer sections in `sections_missing`.

## llama-cli Role

`llama-cli` remains a fallback smoke path only.

It is acceptable for manual local checks because Phase 1B now disables logs,
closes stdin, and strips echoed prompt text with a sentinel. It should not be
the long-term automation path because stdout can include UI/banner/help text.

Manual Phase 2 validation with `llama-cli` failed to produce a usable answer.
The process hung in the subprocess path and was interrupted. Treat `llama-cli`
as not validated for Phase 2 until its process behavior is fixed outside the
adapter.

## Acceptance Criteria

The first Phase 2 implementation is acceptable when:

- Phase 1A `status` is fresh
- Phase 1A `check` passes
- Phase 1B `check` passes
- runtime-unavailable behavior still works
- stubbed JSON runtime success returns parsed answer sections
- stubbed JSON runtime failure returns a structured runtime error
- local fixture HTTP success and HTTP failure are covered by `check`
- non-local JSON endpoints are rejected before any request is made
- no Studio UI is introduced
- no embeddings or vector database are introduced
- no graph/source mutation is introduced
- no model download or install automation is introduced

## Do Not Start Yet

Do not start these until the JSON runtime boundary is proven:

- Studio Debugger integration
- embeddings
- vector database
- graph generation
- graph mutation
- source mutation
- fine-tuning
