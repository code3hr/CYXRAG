# Contributing

Open RAG is intended to be a minimal, local-first retrieval utility.
Contributions should stay focused, local, and reproducible.

## Scope

- Keep behavior deterministic by default.
- Prefer small, reviewable changes.
- Keep compatibility shims minimal and explicit.
- Avoid adding new model dependencies unless they are required.

## Developer setup

- Install Python 3.10+.
- From the project root:

```bash
python -m pip install -U pip
```

## Code and test expectations

Before opening a PR or merge request:

1. Use UTF-8, no BOM for JSON inputs/outputs used by CLI tools.
2. Keep CLI behavior backward-compatible for existing JSON contracts.
3. Run the smoke paths documented in `README.md` for any retrieval/runtime change.
4. Add or update tests/docs in the corresponding `phase*` markdown and scripts.

## PR checklist

- [ ] Focused change and rationale in description.
- [ ] Added/updated docs for user-facing behavior.
- [ ] Reproducible verification steps included.
- [ ] No unrelated refactors.

## Style

- Keep edits small and explicit.
- Use existing helper functions and utility patterns.
- Prefer ASCII text unless a file already contains Unicode content.
