# Structure Review: OPEN_RAG Re-organization

## Completed cleanup
- Removed root-level markdown redirect files that were duplicates of canonical docs.
- Moved canonical documentation into `docs/`.
- Reorganized executable Python modules under `open_rag/` package.

## Remaining duplicates by name (intentional)

### Runtime compatibility shims (intended)
The root `phase*.py` and `tofix42_*.py` files are lightweight shims kept for compatibility.
They import and re-export corresponding modules under `open_rag/`.

- `open_rag_cli.py` -> `open_rag/open_rag_cli.py` (entry-point shim)
- `phase1a_retrieval.py` -> `open_rag/phase1a_retrieval.py`
- `phase1b_answer.py` -> `open_rag/phase1b_answer.py`
- `phase2_endpoint_doctor.py` -> `open_rag/phase2_endpoint_doctor.py`
- `phase2_local_endpoint_scan.py` -> `open_rag/phase2_local_endpoint_scan.py`
- `phase2_openai_compat_proxy.py` -> `open_rag/phase2_openai_compat_proxy.py`
- `phase2_probe_report_check.py` -> `open_rag/phase2_probe_report_check.py`
- `phase2_probe_suite.py` -> `open_rag/phase2_probe_suite.py`
- `phase2_real_model_check.py` -> `open_rag/phase2_real_model_check.py`
- `phase2_stub_runtime.py` -> `open_rag/phase2_stub_runtime.py`
- `phase3_debug_context.py` -> `open_rag/phase3_debug_context.py`
- `phase4_training_context.py` -> `open_rag/phase4_training_context.py`
- `phase5_graph_context.py` -> `open_rag/phase5_graph_context.py`
- `phase6_eval_capture.py` -> `open_rag/phase6_eval_capture.py`
- `phase7_finetune_decision.py` -> `open_rag/phase7_finetune_decision.py`
- `phase7_prepare_finetune_dataset.py` -> `open_rag/phase7_prepare_finetune_dataset.py`
- `phase8_knowledge_pack.py` -> `open_rag/phase8_knowledge_pack.py`
- `tofix42_check_all.py` -> `open_rag/tofix42_check_all.py`
- `tofix42_status.py` -> `open_rag/tofix42_status.py`

### Project-specific content duplicates (intended split)
- `README.md` and `implementation/README.md` serve different audiences.
- `docs/<x>.md` and `implementation/<x>.md` are not content-identical; implementation docs are operational context, not user/canonical docs.
- `knowledge_pack/manifest.json` and `phase7_dataset/manifest.json` have different schemas.

## Why this design is kept
- Keeps existing `python phaseX...py` and legacy call paths working.
- Improves import cleanliness by centralizing actual implementation under package module paths.
- Preserves a clean top-level API surface (`README.md`, `open_rag_cli.py`, `phase...` shims, `pyproject.toml`).

## Sanity checks run
- `python -c "import open_rag, open_rag_cli, phase1a_retrieval, ..."` (imports + exports)
- `python phase1a_retrieval.py --help` and other phase `--help` checks
- Root shim smoke test: `open_rag_cli.build(...)`, `open_rag_cli.query(...)`
- README link validation scan completed with no missing local markdown targets.
