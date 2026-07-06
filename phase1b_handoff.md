# tofix42 Phase 1B Handoff

## Status

Phase 1B is functionally complete as a minimal answer adapter over Phase 1A
retrieval packets.

It proves:

- Phase 1A answer packets can be consumed without reimplementing retrieval
- strict evidence-grounded prompts can be generated from cited chunks
- runtime-unavailable answers return a stable envelope with citations
- local runner readiness can be checked without loading a model
- explicit `llama-cli` calls can be wrapped behind one adapter path
- local runner failures and timeouts return structured diagnostics
- successful runner output can be parsed into answer sections
- echoed `llama-cli` prompt output can be stripped with a sentinel

It intentionally does not include:

- embeddings
- vector database
- automatic model download
- background service or file watcher
- Studio UI
- graph mutation
- source mutation
- fine-tuning

## Artifacts

- `phase1b_answer.py`: stdlib-only prompt, answer, doctor, and check helper
- `phase1b_answer.md`: Phase 1B behavior and command notes
- `phase1b_test_packet.json`: saved Phase 1A packet fixture for checks
- `usage.md`: rolling usage notes for tofix42

## Current Commands

Build a strict prompt:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" prompt --packet "docs/Data Studio/tofix42/phase1b_test_packet.json"
```

Return a runtime-unavailable answer:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" answer --packet "docs/Data Studio/tofix42/phase1b_test_packet.json" --runtime none --json
```

Check adapter readiness and packet validity:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" doctor --packet "docs/Data Studio/tofix42/phase1b_test_packet.json" --runtime none --json
```

Run the deterministic Phase 1B gate:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" check --packet "docs/Data Studio/tofix42/phase1b_test_packet.json"
```

## Current Answer Contract

Answer schema:

```text
cyxwiz.tofix42.phase1b.answer.v1
```

Important fields:

- `mode`
- `question`
- `answer`
- `citations`
- `unknowns`
- `unsupported_or_not_implemented`
- `raw_model_output` when a model succeeds
- `model_output_sections` when a model succeeds
- `runner` when local inference fails

The prompt requires the model to answer only from cited evidence, separate
facts from inference, state missing evidence, and avoid unsupported CyxWiz
claims.

## llama-cli Boundary

`llama-cli` remains an optional explicit runtime path. The adapter now:

- disables conversation mode
- hides prompt display
- uses simple IO
- disables warmup
- disables runner logs
- closes stdin
- strips stdout before the final Phase 1B output sentinel

This makes `llama-cli` acceptable for local smoke testing. If runtime work
continues, prefer a JSON-serving path such as `llama-server` for the next
runtime slice instead of expanding stdout parsing.

## Verification

Last verified command:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" check --packet "docs/Data Studio/tofix42/phase1b_test_packet.json"
```

Expected result:

```text
All Phase 1B adapter checks passed.
```

## Init Call Plan Alignment

This closes the thin answer-adapter slice while preserving the init call plan:

- retrieval remains the truth layer
- the assistant is optional and read-only
- no network service is used
- no graph or source mutation is introduced
- no embeddings are added before the lexical slice proves insufficient
- no Studio UI is added until the command/internal harness is reliable

## Recommended Next Phase

Proceed with the init call plan's `Phase 2: Local Model Runtime`.

Recommended first Phase 2 slice:

- keep Phase 1A retrieval and Phase 1B answer packets unchanged
- add one JSON local runtime adapter, preferably `llama-server`
- define a small request/response boundary for local runtime calls
- keep `llama-cli` as a smoke-test fallback only
- add deterministic tests using stubbed runtime responses
- do not add embeddings, UI, graph edits, source edits, or model download
  automation in the first Phase 2 slice

