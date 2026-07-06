#!/usr/bin/env python3
"""Compatibility shim for package migration."""

from importlib import import_module

mod = import_module("open_rag.open_rag_cli")

build = mod.build
query = mod.query
serve = mod.serve


__all__ = ["build", "query", "serve"]
