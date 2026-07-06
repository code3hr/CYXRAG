# Open RAG Cyxcode Skill Contract

## Purpose
Let cyxcode call local evidence retrieval first, and use model runtime only when confidence is low. The contract keeps token usage bounded by relying on local evidence and optional explicit escalation.

## Strategy support

The contract mirrors `phase1a_retrieval.py packet --mode` and returns packet strategy metadata:
- `indexed-retrieval`
- `fetch-first`
- `memory-hit`

In this project, retrieval strategy is exposed as a cost-control dial:
- `packet-only`: index-first, no fallback scans.
- `fetch-first`: index-first with explicit miss telemetry.
- `memory-first`: include non-rediscoverable memory chunks, optionally without index.

## Invocation Model
- Inputs come in as UTF-8 JSON.
- The skill runs one local retrieval step and returns structured evidence + a compact answer suggestion.
- Runtime model calls are optional and only made when the result confidence is below threshold.

## Input Schema
`open_rag.cyxcode.skill.request.v1`

```json
{
  "question": "How does training stop cleanly?",
  "scope": {
    "project_root": ".",
    "path_contains": ["src", "docs"],
    "source_type": ["markdown", "source", "cyxgraph"],
    "tag": ["training", "runtime"],
    "tag_filter_mode": "all"
  },
  "max_hits": 5,
  "max_tokens": 0,
  "force_runtime": false,
  "confidence_threshold": 0.65,
  "packet_mode": "packet-only",
  "no_index": false,
  "memory_path": "",
  "memory_only": false,
  "fallback_grep": false
}
```

Field notes:
- `question` (string, required): raw user question.
- `scope.project_root` (string, optional): absolute or relative root for discovery.
- `scope.path_contains`, `scope.source_type`, `scope.tag` (arrays, optional): filters.
- `max_hits` (int, default 5): evidence items to return.
- `max_tokens` (int, default 0): reserved for future runtime escalation.
- `force_runtime` (bool, default false): true means always run local runtime stage if configured.
- `confidence_threshold` (float 0..1, default 0.65): below-threshold triggers optional escalation.
- `packet_mode` (string, default `packet-only`): retrieval strategy; supported values `packet-only`, `fetch-first`, `memory-first`.
- `memory_path` (string, optional): path to local non-rediscoverable memory file (json list/envelope/ndjson).
- `memory_only` (bool, default false): if true, ignore index and use memory source only.
- `fallback_grep` (bool, default false): run lightweight repo scanning when packet evidence is sparse.
- `no_index` (bool, default false): true builds a packet without index fallback.
- `source_type` and `tag` values should align with index naming:
  - `source`: source files
  - `markdown`: docs and markdown files
  - `text`: plain text or generated artifacts
  - `kind` is preserved on citation for classification:
    - `rediscoverable` for source-derived snippets
    - `non_rediscoverable` for memory-guided snippets

## Output Schema
`open_rag.cyxcode.skill.response.v1`

```json
{
  "schema": "open_rag.cyxcode.skill.response.v1",
  "question": "...",
  "mode": "retrieval_only | escalated_runtime | no_evidence | runtime_unavailable",
  "strategy": "indexed-retrieval | fetch-first | memory-hit",
  "source_miss": false,
  "fallback_used": false,
  "confidence": 0.82,
  "evidence": [
    {
      "rank": 1,
      "score": 412,
      "citation": {
        "path": "src/foo.py",
        "line_start": 12,
        "line_end": 43,
        "title": "foo::handle_train",
        "source_type": "source",
        "kind": "rediscoverable"
      },
      "snippet": "..."
    }
  ],
  "sources": {
    "index_chunks": 0,
    "memory_chunks": 3,
    "fallback_chunks": 1
  },
  "snippet_count": 3,
  "answer": "optional short summary if runtime was used",
  "unknowns": ["..."],
  "unsupported_or_not_implemented": ["..."]
}
```

## Minimal execution flow
1. Resolve the project root.
2. Build/refresh index if needed.
3. Generate answer packet via `python phase1a_retrieval.py packet ... --json`.
4. If `max_hits` is reached and snippet scores are sparse, set `mode: no_evidence`.
5. Compute confidence from evidence density and score spread.
6. If `force_runtime` or confidence `< threshold`, run the optional runtime path (local runner or JSON endpoint) to produce `mode: escalated_runtime`; otherwise keep `mode: retrieval_only`.
7. Never mutate files and never invent behavior absent from evidence.

Recommended packet invocation pattern for the contract:

```bash
python phase1a_retrieval.py \
  --config /path/to/open_rag_config.json \
  --index /tmp/open_rag_index.json \
  packet "$QUESTION" \
  --mode memory-first \
  --memory-path /path/to/memory.json \
  --fallback-grep \
  --top 5 --json
```

## Local-first rule
- The default is local retrieval only (`max_tokens` does not trigger model calls).
- Any model escalation must be explicit in the tool output via `mode: escalated_runtime`.

## Error policy
- Missing packet: return `mode: no_evidence` with `unknowns` filled.
- Broken config or invalid schema: return `mode: runtime_unavailable` with a short reason.
- Do not retry external endpoints from this skill by default.

## Suggested integration
- Wrap this document in a thin `cyxcode` adapter script.
- Adapter parameters:
  - `open_rag_skill_request = stdin`
  - `python phase1a_retrieval.py packet ...`
  - optional `python phase1b_answer.py prompt/answer` only when escalation is requested.
