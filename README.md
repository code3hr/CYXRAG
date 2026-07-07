# Open RAG

Open RAG is a local, script-first retrieval stack with an optional local model runtime.

## Project layout (current)

- `open_rag/`: source package (all executable modules).
- Root `*.py` files: compatibility shims so legacy direct calls like `python phase1a_retrieval.py` still work.
- `docs/`: canonical markdown documentation location.

## What this solves

- Reduce token spend by grounding LLM questions in local evidence packets first.
- Improve coding-agent reliability by requiring repo evidence before expensive model calls.
- Speed up review and onboarding with fast answers to "where/how/why" questions in code and docs.
- Preserve privacy and offline workflows by running retrieval and runtime locally.

## Use cases

- **Token-efficient coding assistant:** retrieve evidence for model prompts instead of full-file context dumps.
- **Cyxcode integration:** pre-tool skill for context-first code edits and reviews.
- **Codebase Q&A:** map architecture, ownership, and behavior quickly across a repo.
- **Compliance and drift checks:** track fallback hits and packet misses to decide when indexing or memory should expand.

## Use cases by phase

- **Phase 1A**: lexical index, search, and evidence packets (`phase1a_retrieval.py`)
- **Phase 1B**: strict evidence prompts and optional local JSON runtime adapter (`phase1b_answer.py`)
- **Phase 8**: prebuilt knowledge packs for fast reloads (`phase8_knowledge_pack.py`)
- **Cyxcode contract**: local-only retrieval-first skill contract (`open_rag_skill_contract.md`)

## Usage instructions

Yes. This file already contains the full usage path. The minimum viable flow is:

1. Configure a project-specific file:

   ```bash
   cp open_rag_config.example.json open_rag_config.json
   ```

2. Build or refresh local index:

   ```bash
   open-rag-build --index /tmp/open_rag_index.json --config open_rag_config.json
   ```

3. Run a packet query:

   ```bash
   open-rag-query --index /tmp/open_rag_index.json --config open_rag_config.json "How does this project initialize?" --top 5 --json
   ```

4. Validate packet quality:

   ```bash
   open-rag-query --index /tmp/open_rag_index.json --config open_rag_config.json packet "How does this project initialize?" --top 5 --json | python phase1b_answer.py check --packet - --max-chars-per-evidence 1200
   ```

5. Optional local runtime (for model answer):

   ```bash
   open-rag-serve --host 127.0.0.1 --port 8768 --upstream http://127.0.0.1:1234/v1/chat/completions
   open-rag-query --index /tmp/open_rag_index.json --config open_rag_config.json packet "How does this project initialize?" --top 5 --json | python phase1b_answer.py answer --runtime json-http --endpoint http://127.0.0.1:8768/completion --max-tokens 512 --json
   ```

## Example project

For a small runnable example, see `examples/dummy_project/`. The full walkthrough
in `examples/README.md` shows both retrieval-only usage and local model usage
with `llama-server`.

```bash
python phase1a_retrieval.py --index /tmp/open_rag_dummy_index.json --config examples/dummy_project/open_rag_config.json build
python phase1a_retrieval.py --index /tmp/open_rag_dummy_index.json --config examples/dummy_project/open_rag_config.json search "How does dummy trade approval work?" --source-type markdown --top 5 --json
python phase1a_retrieval.py --index /tmp/open_rag_dummy_index.json --config examples/dummy_project/open_rag_config.json packet "How does dummy trade approval work?" --source-type markdown --top 5 --json | python phase1b_answer.py check --packet - --max-chars-per-evidence 1200
```

The example mirrors the intended user flow:

1. add an `open_rag_config.json` to a project,
2. build a local index,
3. ask a focused question,
4. validate the packet before spending model tokens,
5. optionally send the packet to `llama-server` with `phase1b_answer.py answer`.

## Local model expectations

Open RAG separates retrieval quality from model quality.

In a real mixed codebase test, retrieval and packet validation worked correctly.
A small local 3B coder model could answer a focused question from evidence, but it
struggled to follow strict section formatting and timed out on a larger packet.

Practical guidance:

- use `--top 2` or `--top 3` for small local models,
- keep `--max-chars-per-evidence` around `500-800` when latency matters,
- treat Phase 1A packets as the reliable grounding layer,
- treat model answers as optional runtime output,
- use a stronger local model when strict structured answers are required.

## Why this design now

This project intentionally follows the same direction described in Qodo's 2026 review of RAG:
full-codebase indexing is useful, but only when it provides net value.

- We keep retrieval local-first and deterministic for question answering.
- We can still operate with minimal indexing overhead for small or fast-changing repos.
- We treat codebase text as rediscoverable context, with a separate optional memory layer for
  non-rediscoverable signals (past decisions, conventions, recurring findings).
- We favor low-cost evidence packets first, then optional runtime escalation only when needed.

Reference:
https://www.qodo.ai/blog/we-built-a-state-of-the-art-rag-system-for-code-review-in-qodo-2-4-we-took-most-of-it-out

Why this matters for your project:

- Fast repos can stay on `packet-only` with indexing.
- Large repos can run `fetch-first` to keep cost low and expose misses explicitly.
- Teams with policy decisions or reviewer notes can add `memory-first` without touching source indexing.

## Quickstart (generic use)

From your project root, copy/keep `open_rag_config.example.json` as your starting config and edit `project_root` + `source_patterns`.

```bash
cd /path/to/project-root
cp open_rag_config.example.json open_rag_config.json
```

Use a stable index path per project:

```bash
open-rag-build --index /tmp/open_rag_index.json --config open_rag_config.json
open-rag-query --index /tmp/open_rag_index.json --config open_rag_config.json search "your question" --top 5 --json
```

### Installed CLI (optional)

From this folder (or editable install), you can use:

```bash
pip install -e .

open-rag-build --index /tmp/open_rag_index.json --config open_rag_config.json
open-rag-build --index /tmp/open_rag_index.json --config open_rag_config.json --incremental
open-rag-query --index /tmp/open_rag_index.json --config open_rag_config.json "How does this project initialize?" --top 5 --json
open-rag-query --index /tmp/open_rag_index.json --mode fetch-first --no-index "Where is this project documented?" --top 5 --json
open-rag-query --index /tmp/open_rag_index.json --mode memory-first --memory-only --memory-path /tmp/open_rag_memory.json "Which policy applies to error handling?" --top 5 --json
open-rag-serve --host 127.0.0.1 --port 8768 --upstream http://127.0.0.1:1234/v1/chat/completions
open-rag-benchmark --config open_rag_config.json --index /tmp/open_rag_benchmark_index.json --top 5 "How does this project initialize?"
```

These command names map directly to existing scripts without changing default behavior.

`open-rag-query --mode` controls strategy metadata:

- `packet-only` (default): indexed retrieval only (legacy behavior).
- `fetch-first`: report that fetch/other strategies would be required when index misses.
- `memory-first`: same behavior shape, but marks strategy as `memory-hit` for non-rediscoverable context.

You can also enable lightweight fallback grep if packet evidence is sparse:

```bash
open-rag-query --index /tmp/open_rag_index.json --mode fetch-first --no-index "How is training configured?" --fallback-grep --top 5 --json
```

Bounded fallback knobs:

- `--fallback-max-files` limits how many files are scanned.
- `--fallback-context-lines` controls chunk window depth around each match.
- `--fallback-timeout-ms` caps fallback scan wall time.

Periodic telemetry:

```bash
open-rag-query --index /tmp/open_rag_index.json fallback-report
open-rag-query --index /tmp/open_rag_index.json fallback-report --json
```

Legacy-compatible direct command equivalent:

```bash
python phase1a_retrieval.py fallback-report --index /tmp/open_rag_index.json
```

Benchmark token savings and retrieval timing:

```bash
open-rag-benchmark --config open_rag_config.json --index /tmp/open_rag_benchmark_index.json --top 5 "How does this project initialize?"
open-rag-benchmark --config open_rag_config.json --source-type markdown --top 5 "Where is project ownership documented?" --json
```

The benchmark compares estimated tokens for a prompt containing all indexed
content against the Phase 1B evidence-packet prompt. Token counts are estimates
using `ceil(characters / 4)` because exact tokenizer counts vary by model.

### Deciding when to index

Use this before running large indexing jobs:

Checklist:

1. Is the repo stable between sessions (not frequently rebased)?
2. Do most queries target rediscoverable source/docs?
3. Is `packet-only` returning enough hits at your top-k target?
4. Are build times acceptable for your editing cadence?
5. Do fallback warnings stay below your budget threshold?
6. If answer quality drops, add a memory source before forcing full indexing.

If you answer "yes" to most items, index-first is a good default. Otherwise start
with `--no-index` workflows and only enable indexing when telemetry shows gains.

Deletion criteria for optional features (keep your implementation cheap):

- Remove `--fallback-grep` if fallback packets are never useful for your question
  mix.
- Remove `--memory-path`/`--memory-only` unless you must retain non-rediscoverable
  decisions in local JSON.
- Remove this telemetry path (including `fallback-report`) if you do not run
  scheduled packet validation.
- If full indexing is not materially better than no-index mode, keep only
  `search` + optional `fetch-first`.


This is the same economic tradeoff from Qodo's review: full indexing only where it saves enough rework to justify its cost.

Example:

```bash
open-rag-query --config open_rag_config.example.json --mode fetch-first --no-index "Where is project ownership documented?" --json
```

If `fallback_used` is true and `source_miss` is true, the query is a miss under the selected strategy and should route to your repo tools or a memory source.

Build a packet and run retrieval-only validation:

```bash
open-rag-query --index /tmp/open_rag_index.json --config open_rag_config.json packet "How does this project initialize?" --top 5 --json \
  | python phase1b_answer.py check --packet - --max-chars-per-evidence 1200
```

If you need a runtime answer, keep runtime optional:

```bash
open-rag-query --index /tmp/open_rag_index.json --config open_rag_config.json packet "How does this project initialize?" --top 5 --json \
  | python phase1b_answer.py answer --runtime json-http --endpoint http://127.0.0.1:8768/completion --max-tokens 512 --json
```

Build and validate a reusable knowledge pack:

```bash
python phase8_knowledge_pack.py --pack /tmp/open_rag_pack build --config open_rag_config.json --engine-version docs --build-id local
python phase8_knowledge_pack.py --pack /tmp/open_rag_pack validate --json
```

## Use this in another repository

1. Copy `open_rag_config.example.json` and set:
   - `project_root` to the target repo path
   - `source_patterns` to match your file types (`**/*.md`, `**/*.py`, `**/*.ts`, etc.)
2. Build once from that repo directory.
3. Keep `index`, `packet`, and optional `pack` under a location like `/tmp/open_rag_*` (or any local path).
4. Use the same `--config` and `--index` for each query.

## Important path note

`--project-root` is treated as a CLI override and is resolved against the config path when relative.
To avoid surprises, either:

- omit `--project-root` (the config value is used), or
- pass an absolute `--project-root` path.

## Running a local llama-server

`phase1b_answer.py` expects a local JSON endpoint and sends:

- `POST /completion`
- JSON body: `{"prompt":"...","n_predict":<max_tokens>,"stream":false}`

One tested launch pattern (replace placeholders with your local paths):

```powershell
& "C:\path\to\llama-server.exe" `
  -m "C:\path\to\model\qwen2.5-coder-3b-instruct-q4_k_m.gguf" `
  --host 127.0.0.1 --port 8768 --log-disable
```

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8768/completion" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"prompt":"Write one sentence about this project.","n_predict":32,"stream":false}'
```

A successful response contains text in `content`.

If the server returns 503 on first request, it is often still starting the model. Wait a few seconds and retry.

For a complete runnable flow that starts from a sample project and ends with a
model answer, see `examples/README.md`.

## Files worth reading first

- `open_rag_config.example.json` - CLI config starting point
- `examples/README.md` - runnable example project and commands
- `docs/BENCHMARKS.md` - token reduction and timing benchmark notes
- `docs/phase1a_retrieval.md` - retrieval CLI contract and saved query behavior
- `docs/phase1b_answer.md` - strict prompt format and runtime modes
- `docs/phase8_knowledge_pack.md` - pack format and validation
- `docs/open_rag_skill_contract.md` - cyxcode integration contract
- `docs/done1.md` - post-Qodo design update considerations
- `CONTRIBUTING.md` - contribution checklist and expectations
- `SECURITY.md` - local/runtime security guidance
- `CHANGELOG.md` - release notes
- `LICENSE` - MIT-licensed project usage terms (replace if you need a different license)

