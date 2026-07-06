# Changelog

All notable changes to Open RAG should be documented here.

## [Unreleased]

- Added `phase1a_retrieval.py packet` strategy controls (`packet-only`, `fetch-first`, `memory-first`),
  including `strategy`, `source_miss`, and `fallback_used` in packet JSON/markdown output.
- Added OSS-facing `README.md` with generic setup, query, pack, and runtime usage.
- Added `open_rag_skill_contract.md` and plan updates for cyxcode retrieval-first integration.
- Added placeholders for open-source legal/process docs: `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`.
- Replaced LICENSE placeholder with a default MIT license text for immediate OSS distribution.
- Added `pyproject.toml` and installable CLI entry points:
  - `open-rag-build`
  - `open-rag-query`
  - `open-rag-serve`
- Added memory ingestion support in packet mode:
  - `--memory-path` / `--memory-only`
  - non-rediscoverable chunk import with `kind`
- Added `--fallback-grep` path for sparse/no-index packet fills.
- Documented reusable local setup and runtime guidance for `llama-server`.
- Added `build --incremental` to reuse unchanged chunks and reduce rebuild cost.
- Added bounded fallback controls (`--fallback-max-files`, `--fallback-context-lines`, `--fallback-timeout-ms`)
  plus packet-run budget warning based on repeated fallback profile usage.
- Added packet run telemetry persistence and a new `fallback-report` command for periodic
  comparison of index build and fallback usage cost.
- Fixed `open_rag_cli` dispatch so `open-rag-query fallback-report` correctly runs the
  fallback telemetry command, while keeping query mode default behavior unchanged.
- Made `open_rag_cli` lazy-load the optional serve module so `query/build` can be used
  without requiring `phase2_openai_compat_proxy` in minimal installs.

## [0.1.0] - 2026-07-05

- Initial open-source preparation baseline:
  - Genericized retrieval/answering namespace and configs.
  - Added smoke-testable command paths for local projects.
  - Added optional local JSON runtime path (`/completion`) contract notes.
