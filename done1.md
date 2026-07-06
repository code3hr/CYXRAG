# Open RAG Roadmap Additions (Post-Qodo Review)

This plan captures follow-up work to keep retrieval token-cheap by default while
supporting a small memory layer for non-rediscoverable decisions.

## Guiding principle

- Keep retrieval local and deterministic as default behavior.
- Prefer fetch-on-demand behavior when context can be acquired cheaply outside indexing.
- Use a compact memory layer only for facts that are hard to rediscover from source.

## TODO

### 1) Strategy and packet telemetry
- [x] Add explicit packet mode options: `packet-only`, `fetch-first`, `memory-first`.
- [x] Emit packet strategy as one of:
  - `indexed-retrieval`
  - `fetch-first`
  - `memory-hit`
- [x] Track `source_miss` and `fallback_used` in packet output.
- [x] Add per-run lightweight ROI counters:
  - `evidence_hits`
  - `index_chunks_scanned`
  - `fallback_chunks_scanned`

### 2) Rediscoverability split
- [x] Introduce chunk `kind` with values:
  - `rediscoverable` (source/docs/config artifacts)
  - `non_rediscoverable` (decisions/policies/review notes)
- [x] Add schema label `open_rag.non_rediscoverable.v1`.
- [x] Update skill contract to require `kind` in evidence citations.

### 3) Memory layer
- [x] Add importer for local memory JSON (list/envelope/NDJSON).
- [x] Add append/update helper that avoids full re-index rebuild.
- [x] Add `--memory-path` and `--memory-only` packet options.
- [x] Add memory smoke path with `--memory-only`.

### 4) On-demand fallback and no-index mode
- [x] Add `--fallback-grep` for symbol/text fallback scans.
- [x] Add `--no-index` support for environments that should use direct discovery or memory.
- [x] Add quality knobs to keep fallback bounded (max file count, scan depth, timeout).
- [x] Add budget warning when fallback is repeatedly required for the same query profile.

### 5) Open-source readiness
- [x] Keep `README` generic and include install/index/query/serve instructions.
- [x] Add `LICENSE`, `CONTRIBUTING`, `SECURITY`, `CHANGELOG`.
- [x] Add `pyproject.toml` entry points:
  - `open-rag-build`
  - `open-rag-query`
  - `open-rag-serve`
- [x] Add a deletion criteria section for expensive optional features.
- [x] Add a concrete decision checklist before enabling indexing at scale.

### 6) Qodo-inspired production hardening
- [x] Keep local-only retrieval as the default "cheap path."
- [x] Add a tiny "tradeoff note" in packet output for why indexing/fallback was used.
- [x] Add a periodic report that compares index build/runtime cost versus direct lookup fallback.
- [x] Validate in one external sample project that the workflow copies cleanly.
  - Verified with external copy at `D:/tmp/open_rag_external_smoke/toolset` plus a sample project at `D:/tmp/open_rag_external_smoke/sample_project`.
  - Ran `build`, `packet`, and `fallback-report` successfully.

## Definition of done

- New functionality includes at least one runnable usage example and a smoke check.
- Changes remain opt-in; default behavior must stay stable.
- Skill contract is updated when strategy or output schema changes.

## Status update

- [x] README decision guide and strategy examples added for packet/no-index behavior.
- [x] `open_rag_skill_contract.md` updated with strategy, `source_miss`, `fallback_used`, and memory/fallback controls.
- [x] Memory loading + packet merge behavior implemented in `phase1a_retrieval.py`.
