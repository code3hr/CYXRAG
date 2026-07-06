# Open RAG Plan

## Goal
Create a generic, open-source-friendly RAG utility from the current implementation, then make it usable as a cyxcode skill that prefers local retrieval and minimizes LLM token spend.

## Scope
- Open the current `tofix42` implementation for external, project-agnostic use.
- Keep existing retrieval strengths (chunking, lexical search, ranked snippets, evidence packets).
- Add a thin, stable integration layer for cyxcode skills.
- Publish/run with clear docs and sane defaults.

## Lean Guardrails (applied)
- Keep behavior local-first and deterministic by default.
- Avoid adding optional complexity (UI, embeddings, vector DB, retraining) until the local retrieval loop is proven stable.
- Keep compatibility support explicit and minimal; old schema names are accepted only on input, never emitted by default.
- Defer packaging/distribution scaffolding until the core retrieval-to-answer path and skill contract are correct.

## Phase 1: Genericization (no product assumptions)
1. Remove CyxWiz-specific naming and defaults from pack schema, prompts, config, and docs.
2. Replace hardcoded repo-root assumptions with explicit config inputs.
3. Normalize output schema and IDs to `open_rag.*` namespace.
4. Provide language-agnostic instructions and examples.
5. Keep legacy compatibility shim only if it is minimal and clearly marked.

## Phase 2: Packaging for reuse
6. Add a packaging entry so it can be installed/distributed.
7. Provide `open_rag` CLI commands for:
   - `build` (index)
   - `query` (search + evidence packet)
   - `serve` (optional local JSON API)
8. Add deterministic defaults in one config file (`open_rag.toml` + env/CLI overrides).

## Phase 3: Quality and reliability
9. Add a smoke test matrix:
   - index a sample repo
   - run 3 simple queries
   - validate packet schema and references
10. Add clear error cases and exit codes for corrupt packs, empty results, unsupported files.
11. Document performance notes for large repos and throttling behavior.

## Phase 4: Documentation and open-source prep
12. Add `README` with install, onboarding, privacy, and example workflows.
13. Add `LICENSE` + `CONTRIBUTING` + `SECURITY` + `CHANGELOG` stubs.
14. Remove internal branding from filenames, folder names, and user-facing strings.

## Phase 5: Cyxcode skill integration
15. Add a skill contract that:
   - accepts `question`, optional `scope`, optional `project_root`
   - returns ranked snippets + evidence list
   - avoids extra tokens unless explicitly escalated
16. Define optional fallback path:
   - if local confidence is low, pass top evidence to local/remote model as second-stage reasoning.
17. Keep skill behavior deterministic and easy to disable.

## Exit Criteria
- A new user can copy this repo and run index/query on a foreign project with minimal setup.
- No CyxWiz-specific paths, prompts, or schema assumptions in defaults.
- Skill output is citation-first and reproducible.

### Current Status (as of latest run)
- [x] CLI naming, schemas, and project-root inputs are generic in phase 1A/1B/phase8.
- [x] Legacy schema compatibility retained only in readers (not producers).
- [x] Add a concrete cyxcode skill contract and integration entrypoint.
- [x] Add minimal OSS-focused `README` + docs for quick start.
- [x] Add open-source prep files: `LICENSE` (MIT), `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`.
- [x] Add `pyproject.toml` / entry points for installable distribution.

## Execution Plan (Ready to implement)

### Sprint 0: Baseline snapshot (no behavior change)
1. Inventory current behavior by running:
   - `python phase1a_retrieval.py --help`
   - `python phase8_knowledge_pack.py --help`
   - `python phase1b_answer.py --help`
2. Export a short command log to prove current output format still works.

### Sprint 1: Generic core
3. Create explicit config contract and stop implicit path assumptions:
   - `phase1a_retrieval.py` should consume repo root/project path from config/CLI/env.
   - keep defaults minimal and neutral.
4. Rename namespace and schema ids in:
   - `phase8_knowledge_pack.py` (manifest/schema IDs)
   - `phase1a` packet output fields where they are presented externally.
5. Remove CyxWiz-specific wording and defaults in docs/prompts:
   - `phase1b_answer.py`
   - `phase1a_retrieval.py`
   - `usage.md`
6. Add one generic sample config file: `open_rag_config.example.toml` (or `.json`).
7. Add migration note for current `phase1a_config.json` / existing naming.

### Sprint 2: Open-source packaging + docs
8. Add OSS-facing README sections:
   - quickstart
   - data model
   - supported file types and exclusions
   - privacy + offline behavior
9. Add minimal publishing metadata (`LICENSE`, `pyproject.toml` / entry points).
10. Add `CONTRIBUTING`, `SECURITY`, `CHANGELOG` skeletons.

### Sprint 3: Skill contract for cyxcode
11. Define a stable contract in a dedicated doc (new):
   - input: `question`, optional `scope`, `max_tokens`, `max_hits`, `project_root`
   - output: ranked evidence snippets, top-k sources, confidence, fallback signal
12. Add a cyxcode mapping doc/skill stub file in `OPEN_RAG` that explains how to call:
   - local search first
   - optional model escalation only when confidence is below threshold.
13. Add policy for read-only behavior and refusal handling.

### Sprint 4: Acceptance + polish
14. Create a minimal smoke test script and expected artifacts for a small sample repo.
15. Add a packaging smoke test: build+query on first run.
16. Define versioning and backward compatibility policy for pack format.

### Do / Don’t (for first release)
- Do: keep default behavior local-first, deterministic, and cite-first.
- Do: keep model calls optional and explicit.
- Do: document deprecation path for old internal names.
- Don’t: rename or rewrite internal files beyond what is needed to make generic.
- Don’t: add fine-tuning hooks before retrieval quality is stable.

