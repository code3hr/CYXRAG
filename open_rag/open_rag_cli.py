#!/usr/bin/env python3
"""Console entrypoints for Open RAG installed CLI commands.

This module intentionally wraps existing phase scripts so behavior stays stable:
- `open-rag-build` -> phase1a_retrieval.py packet/build/search path
- `open-rag-query` -> phase1a_retrieval.py packet command
- `open-rag-serve` -> phase2_openai_compat_proxy.py serve command
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Optional

from . import phase1a_retrieval
DEFAULT_LOCAL_CONFIG = "open_rag_config.example.json"
PHASE1A_GLOBAL_OPTIONS = {"--index", "--config", "--project-root"}


def _with_default_config(argv: Optional[list[str]]) -> list[str]:
    args = list(argv) if argv is not None else []
    if any(arg == "--config" for arg in args):
        return args
    if Path(DEFAULT_LOCAL_CONFIG).exists():
        return ["--config", str(Path(DEFAULT_LOCAL_CONFIG).resolve()), *args]
    return args


def _split_phase1a_args(argv: list[str]) -> tuple[list[str], list[str]]:
    """Split CLI args into phase1a global options and command-specific arguments."""
    leading = []
    trailing = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in PHASE1A_GLOBAL_OPTIONS:
            leading.append(arg)
            if i + 1 < len(argv):
                leading.append(argv[i + 1])
                i += 2
            else:
                i += 1
            continue
        trailing.append(arg)
        i += 1
    return leading, trailing


def _run_phase1a_command(command: str, argv: Optional[list[str]] = None) -> int:
    """Run a phase1a command with argument ordering normalized for global options."""
    args = _split_phase1a_args(_with_default_config(argv))
    ordered_args = [*args[0], command, *args[1]]
    original_argv = list(sys.argv)
    sys.argv = ["phase1a_retrieval.py", *ordered_args]
    try:
        return phase1a_retrieval.main()
    finally:
        sys.argv = original_argv


def _require_phase2_proxy():
    """Import proxy module only when serve mode is requested."""
    try:
        from . import phase2_openai_compat_proxy
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "phase2_openai_compat_proxy is required for the `open-rag-serve` command."
        ) from exc
    return phase2_openai_compat_proxy


def build(argv: Optional[list[str]] = None) -> int:
    """Run the phase1a retrieval index build command."""
    return _run_phase1a_command("build", argv)


def query(argv: Optional[list[str]] = None) -> int:
    """Run the phase1a retrieval commands.

    Default behavior is `packet`, but keep explicit one-off commands supported for
    parity with documented entry points (for example `fallback-report`).
    """
    args = list(argv) if argv is not None else []
    if args and args[0] == "fallback-report":
        return _run_phase1a_command("fallback-report", args[1:])
    return _run_phase1a_command("packet", args)


def serve(argv: Optional[list[str]] = None) -> int:
    """Run the local /completion JSON HTTP compatibility serve command."""
    phase2_openai_compat_proxy = _require_phase2_proxy()
    return phase2_openai_compat_proxy.main(["serve", *(list(argv) if argv is not None else [])])

