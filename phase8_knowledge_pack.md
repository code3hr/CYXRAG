# Phase 8 Knowledge Pack

## Purpose

Build the first versioned retrieval knowledge pack for the CyxWiz assistant.

This is the implementation bridge between:

- the Phase 1A development index
- the plugin/backend knowledge-pack design

The pack lets the assistant load retrieval-ready data without rescanning the
repository on every startup.

## Output Layout

Default output:

```text
docs/Data Studio/tofix42/knowledge_pack/
  manifest.json
  chunks.jsonl
  lexicon.json
  postings.json
  metadata.json
  diagnostics.json
```

## Build

```powershell
python "docs/Data Studio/tofix42/phase8_knowledge_pack.py" build `
  --engine-version dev `
  --build-id local
```

Current generated pack:

- files: `432`
- chunks: `4498`
- retrieval backend: `lexical-v1`

## Validate

```powershell
python "docs/Data Studio/tofix42/phase8_knowledge_pack.py" validate
```

JSON:

```powershell
python "docs/Data Studio/tofix42/phase8_knowledge_pack.py" validate --json
```

Expected result:

```text
OK: True
```

## Run Pack Retrieval Checks

```powershell
python "docs/Data Studio/tofix42/phase8_knowledge_pack.py" check
```

This runs the existing Phase 1A retrieval success checks against the knowledge
pack rather than against `phase1a_index.json`.

Expected result:

```text
All knowledge-pack retrieval checks passed.
```

## Search

```powershell
python "docs/Data Studio/tofix42/phase8_knowledge_pack.py" search `
  "What source file defines DebugTraceRecord" `
  --top 3
```

Expected top citation:

```text
cyxwiz-engine/src/core/debug_trace_record.h:31-46
```

## Build an Answer Packet

```powershell
python "docs/Data Studio/tofix42/phase8_knowledge_pack.py" packet `
  "TrainingTraceEvent terminal_reason field" `
  --top 1 `
  --json
```

Expected top citation:

```text
cyxwiz-engine/src/core/training_trace_collector.h:13-48
```

## Filters

Search and packet commands support the same basic filters as Phase 1A:

```powershell
python "docs/Data Studio/tofix42/phase8_knowledge_pack.py" search `
  "terminal_reason" `
  --source-type source `
  --path-contains training
```

Supported filters:

- `--source-type`
- `--path-contains`
- `--title-contains`
- `--tag`

## What This Proves

This proves the assistant can:

1. build a versioned retrieval asset from the repo/docs/examples
2. load the pack without rescanning files
3. search using prebuilt lexical assets
4. return citations and answer packets from the pack
5. detect basic pack/version validation failures

## Not Yet Done

The pack is not yet wired into:

- the C++ assistant plugin
- the Assistant panel backend
- Command Window slash commands
- model runtime calls

Those belong to the next roadmap phase.
