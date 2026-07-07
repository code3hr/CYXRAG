# Benchmarks

Open RAG benchmarks compare a focused evidence packet against a prompt that
contains all files selected by the same Open RAG config.

Token counts are estimates using:

```text
ceil(characters / 4)
```

Exact tokenizer counts vary by model, but this estimate is useful for comparing
relative prompt size.

## Command

```bash
open-rag-benchmark \
  --config open_rag_config.json \
  --index /tmp/open_rag_benchmark_index.json \
  --source-type markdown \
  --top 5 \
  "How does project memory and semantic recall work?"
```

The command reports:

- indexed files and chunks,
- indexed byte size,
- time to read full selected context,
- time to build the index,
- time to create the evidence packet,
- estimated full-context prompt tokens,
- estimated packet prompt tokens,
- estimated packet JSON tokens,
- reduction percentage,
- citations selected for the packet.

## CyxCode Benchmark

This benchmark was run on a local CyxCode checkout using a config that indexed
project docs plus main TypeScript source areas while excluding dependency/build
artifacts such as `node_modules`.

Question:

```text
How does CyxCode project memory and semantic recall work?
```

Filters:

```text
--source-type markdown --top 5 --max-chars-per-evidence 1200
```

Result summary:

| Metric | Result |
| --- | ---: |
| Indexed files | 2,444 |
| Index chunks | 4,132 |
| Indexed bytes | 25,549,690 |
| Read full selected context | 59,824.45 ms |
| Build index | 6,147.79 ms |
| Make packet | 171.03 ms |
| Estimated full-context prompt tokens | 6,365,224 |
| Estimated packet prompt tokens | 1,465 |
| Estimated packet JSON tokens | 3,082 |
| Packet prompt reduction | 99.98% |
| Packet JSON reduction | 99.95% |
| Evidence hits | 5 |
| Source miss | false |
| Fallback used | false |

Top citations selected:

- `docs/RECALL.md:42-49`
- `docs/FAQ.md:51-117`
- `docs/RECALL.md:7-19`
- `docs/security_layer.md:476-546`
- `demo/02-project-init-memory/README.md:1-39`

## Interpretation

This does not prove answer quality by itself. It proves the prompt-size reduction
and retrieval timing for the selected query/config.

For this run, Open RAG reduced the prompt sent to a model from an estimated
6.36M-token full selected context to a 1.5K-token evidence prompt. The packet was
created in about 171 ms after indexing.

Build time is a one-time or refresh cost. Repeated questions reuse the index and
pay only packet creation plus optional model runtime.

## Small Example Benchmark

The dummy example under `examples/dummy_project/` is intentionally tiny. It is
useful for smoke testing and documentation, not for proving meaningful savings.

Latest local smoke result:

| Metric | Result |
| --- | ---: |
| Indexed files | 5 |
| Index chunks | 10 |
| Estimated full-context prompt tokens | 1,008 |
| Estimated packet prompt tokens | 625 |
| Packet prompt reduction | 38.0% |

Use larger real repositories for meaningful savings numbers.
