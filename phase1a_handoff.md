# tofix42 Phase 1A Handoff

## Status

Phase 1A is functionally complete as a lean retrieval prototype.

It proves:

- local text files can be indexed into a simple JSON corpus
- source, docs, graph files, and selected implementation files can be chunked
- lexical retrieval can return cited evidence for known CyxWiz questions
- deterministic checks can guard retrieval quality
- index freshness can detect changed files and changed config
- retrieval-only answer packets can feed a later model runtime

It intentionally does not include:

- local LLM runtime
- embeddings
- vector database
- background file watcher
- Studio UI
- graph mutation
- source mutation
- fine-tuning

## Artifacts

- `phase1a_config.json`: source patterns and success checks
- `phase1a_retrieval.py`: stdlib-only build/search/status/check/packet helper
- `phase1a_index.json`: generated local JSON index
- `phase1a_retrieval.md`: Phase 1A command and verification notes
- `usage.md`: rolling usage notes for tofix42

## Current Commands

Build:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" build
```

Check freshness:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" status
```

Run deterministic retrieval gate:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" check
```

Create a retrieval-only answer packet:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" packet "What source file defines DebugTraceRecord" --json
```

## Current Index

Current verified index:

```text
31 files / 447 chunks
```

The exact count can change when indexed source/docs change. `status` is the
source of truth for freshness.

## Current Success Gate

`check` currently verifies:

- `DebugTraceRecord` definition resolves to `debug_trace_record.h`
- `TrainingTraceEvent.terminal_reason` resolves to `training_trace_collector.h`
- TF-IDF sentiment graph resolves to the TF-IDF sentiment `.cyxgraph`
- `RecordTerminalEvent` resolves to `training_trace_collector.cpp`
- `completed_all_epochs` / `user_cancelled` resolves to `TrainingExecutor::Train`
- `pin_memory` design truth resolves to `tofix41.md`
- unsupported `pin_memory` compiler warning resolves to `graph_compiler.cpp`
- TF-IDF `min_df` validation resolves to `tfidf_vectorizer_operator.cpp`

## Phase 1B Input Contract

Phase 1B should consume the retrieval packet, not reimplement retrieval.

Packet schema:

```text
cyxwiz.tofix42.phase1a.answer_packet.v1
```

Important packet fields:

- `question`
- `answer_contract`
- `evidence`
- `evidence[].citation.path`
- `evidence[].citation.line_start`
- `evidence[].citation.line_end`
- `evidence[].citation.title`
- `evidence[].citation.source_type`
- `evidence[].text`
- `missing_evidence_notes`

Phase 1B should treat the packet as read-only evidence and produce a cited
answer from it.

## Phase 1B Guardrails

Start Phase 1B with a minimal model/runtime adapter.

Do:

- accept a Phase 1A answer packet
- build a strict prompt from cited evidence
- run one local model backend if available
- emit answer, citations, unknowns, and unsupported notes
- fail cleanly if no runtime is configured

Do not:

- add embeddings yet
- add Studio UI yet
- add background services
- add graph/source mutation
- add automatic model download
- send evidence to network services
- fine-tune

## Recommended First Phase 1B Test

Input:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" packet "DataLoader pin_memory unsupported current batchers compatibility" --json
```

Expected answer behavior:

- cite `graph_compiler.cpp`
- explain that `pin_memory=true` is accepted as serialized compatibility
- explain that current batchers ignore it
- say no pinned host-memory transfer backend exists yet
- avoid claiming CUDA pinned transfers are implemented
