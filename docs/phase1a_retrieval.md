# tofix42 Phase 1A Retrieval Prototype

## Scope

This is the smallest useful retrieval slice for tofix42.

It is intentionally limited:

- local text files only
- stdlib Python only
- manual rebuild
- JSON index
- lexical scoring only
- no local LLM
- no embeddings
- no database
- no background watcher
- no Studio UI
- no graph/source mutation
- no fine-tuning

## Files

- `phase1a_config.json`: source patterns and deterministic success checks
- `phase1a_retrieval.py`: build/search helper
- `phase1a_index.json`: generated local index, rebuilt on demand
- file hashes stored in `phase1a_index.json` for freshness checks

## Build

From the repository root:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" build
```

## Search

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" search "DebugTraceRecord"
python "docs/Data Studio/tofix42/phase1a_retrieval.py" search "TrainingTraceEvent terminal_reason field"
python "docs/Data Studio/tofix42/phase1a_retrieval.py" search "TFIDFVectorizer sentiment graph"
python "docs/Data Studio/tofix42/phase1a_retrieval.py" search "completed_all_epochs terminal_reason user_cancelled"
```

Search uses simple lexical scoring plus small source-type trust boosts so source
and graph evidence can outrank documentation echoes when scores are close.
Oversized C++ declaration chunks are split into bounded symbol-preserving
windows with overlap so boundary-adjacent logic remains retrievable.
Search now emits a small query report with:

- normalized query terms
- top matching files
- top matching chunks
- compact previews

Search and packet previews show context around matching query terms when a
chunk is longer than the preview limit.

Emit a machine-readable search report:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" search "DataLoader pin_memory unsupported current batchers compatibility" --top 8 --json
```

Include full chunk text in the report:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" search "TrainingTraceEvent terminal_reason field" --top 3 --include-full-text
```

Narrow broad queries with metadata filters:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" search "terminal_reason" --source-type source --path-contains training
python "docs/Data Studio/tofix42/phase1a_retrieval.py" search "sentiment" --source-type cyxgraph --path-contains examples/cyxgraph --json
python "docs/Data Studio/tofix42/phase1a_retrieval.py" packet "terminal_reason" --source-type source --path-contains training --top 2 --json
```

Run a saved preset:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" presets
python "docs/Data Studio/tofix42/phase1a_retrieval.py" search --preset training_terminal --top 3
python "docs/Data Studio/tofix42/phase1a_retrieval.py" packet --preset sentiment_graphs --top 2 --json
```

## Check

Run the Phase 1A success gate:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" check
```

## Status

Check whether indexed inputs changed since the last rebuild:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" status
```

The command compares file-level content hashes stored in
`phase1a_index.json` against the current files matched by the Phase 1A input
patterns. It also reports stale status when `phase1a_config.json` changes.

## Config

The default config is:

```text
docs/Data Studio/tofix42/phase1a_config.json
```

Use a different config:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" --config "D:/tmp/tofix42_config.json" build
python "docs/Data Studio/tofix42/phase1a_retrieval.py" --config "D:/tmp/tofix42_config.json" check
```

List saved presets from the current config:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" presets --json
```

## Answer Packet

Build a retrieval-only answer packet:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" packet "What source file defines DebugTraceRecord"
```

Emit JSON for a later model/runtime caller:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" packet "terminal_reason training trace" --json
```

Current packet contract:

- schema: `cyxwiz.tofix42.phase1a.answer_packet.v1`
- mode: `retrieval_only`
- model runtime: `not_used`
- evidence: ranked chunks with path, line range, title, source type, score, and
  text
- missing evidence notes: explicit notes when retrieval cannot satisfy the
  request

## Indexed Inputs

Defined by `phase1a_config.json`:

- `docs/Data Studio/*.md`
- `docs/usage/*.md`
- `examples/cyxgraph/**/*.md`
- `examples/cyxgraph/**/*.cyxgraph`
- `cyxwiz-engine/src/core/**/*.h`
- `cyxwiz-engine/src/core/**/*.hpp`
- `cyxwiz-engine/src/core/**/*.cpp`
- `cyxwiz-engine/src/core/**/*.cc`
- `cyxwiz-engine/src/core/**/*.cxx`

## Phase 1A Success Questions

- What source file defines `DebugTraceRecord`?
- Where is the `TrainingTraceEvent` `terminal_reason` field stored?
- What graph files show TF-IDF sentiment classification?
- Where does `RecordTerminalEvent` persist `terminal_reason`?
- Where does training choose `completed_all_epochs` vs `user_cancelled`?
- Where is the pinned-host-memory truth document?
- Where does compiler/preflight warn about unsupported `pin_memory`?
- Where does `TFIDFVectorizer` validate `min_df`?

## Verification

Current manual check:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" build
```

Result:

```text
Wrote docs/Data Studio/tofix42/phase1a_index.json with 432 files and 4498 chunks.
```

Verified searches:

| Query | Expected top evidence |
| --- | --- |
| `What source file defines DebugTraceRecord` | `cyxwiz-engine/src/core/debug_trace_record.h` |
| `TrainingTraceEvent terminal_reason field` | `cyxwiz-engine/src/core/training_trace_collector.h` |
| `TFIDFVectorizer sentiment graph` | `examples/cyxgraph/Sentiment analysis/sentiment_analysis_tfidf_mlp_classifier.cyxgraph` |
| `RecordTerminalEvent terminal_reason message` | `cyxwiz-engine/src/core/training_trace_collector.cpp` |
| `completed_all_epochs terminal_reason user_cancelled` | `cyxwiz-engine/src/core/training_executor.cpp` |
| `Pinned Host Memory and GPU Transfer Backend Truth` | `docs/Data Studio/tofix41.md` |
| `DataLoader pin_memory unsupported current batchers compatibility` | `cyxwiz-engine/src/core/graph_compiler.cpp` |
| `TFIDFVectorizer min_df must be >= 1 Configure` | `cyxwiz-engine/src/core/node_executors/tfidf_vectorizer_operator.cpp` |

Automated check:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" check
```

## Next Gate

Do not add embeddings or a model runtime until these retrieval questions return
the expected evidence with useful citations.
