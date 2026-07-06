#!/usr/bin/env python3
"""Compatibility shim for package migration."""

from importlib import import_module

mod = import_module("open_rag.phase1a_retrieval")

__all__ = getattr(mod, "__all__", [name for name in dir(mod) if not name.startswith("_")])
for _name in __all__:
    globals()[_name] = getattr(mod, _name)


if __name__ == "__main__":
    main = getattr(mod, "main", None)
    if callable(main):
        raise SystemExit(main())
