#!/usr/bin/env python3
"""Compatibility shim for Open RAG benchmark."""

from open_rag.benchmark import main


if __name__ == "__main__":
    raise SystemExit(main())
