# Open RAG Examples

This folder contains small repositories/configs that show how Open RAG is used
against another project.

## Dummy project

`dummy_project/` is a tiny codebase with docs, source, and a ready
`open_rag_config.json`.

Run it from the Open RAG repository root:

```bash
python phase1a_retrieval.py --index /tmp/open_rag_dummy_index.json --config examples/dummy_project/open_rag_config.json build
python phase1a_retrieval.py --index /tmp/open_rag_dummy_index.json --config examples/dummy_project/open_rag_config.json search "How does dummy trade approval work?" --source-type markdown --top 5 --json
python phase1a_retrieval.py --index /tmp/open_rag_dummy_index.json --config examples/dummy_project/open_rag_config.json packet "How does dummy trade approval work?" --source-type markdown --top 5 --json | python phase1b_answer.py check --packet - --max-chars-per-evidence 1200
```

This mirrors the real-project flow:

1. create a project config,
2. build a local index,
3. ask a focused question,
4. validate the evidence packet before using a model runtime.
