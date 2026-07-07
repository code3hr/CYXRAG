# Open RAG Examples

This folder contains small repositories/configs that show how Open RAG is used
against another project.

## Dummy project

`dummy_project/` is a tiny codebase with docs, source, and a ready
`open_rag_config.json`.

## Full flow: retrieval only

Run this from the Open RAG repository root:

```bash
python phase1a_retrieval.py --index /tmp/open_rag_dummy_index.json --config examples/dummy_project/open_rag_config.json build
python phase1a_retrieval.py --index /tmp/open_rag_dummy_index.json --config examples/dummy_project/open_rag_config.json search "How does dummy trade approval work?" --source-type markdown --top 5 --json
python phase1a_retrieval.py --index /tmp/open_rag_dummy_index.json --config examples/dummy_project/open_rag_config.json packet "How does dummy trade approval work?" --source-type markdown --top 5 --json > /tmp/open_rag_dummy_packet.json
python phase1b_answer.py check --packet /tmp/open_rag_dummy_packet.json --max-chars-per-evidence 1200
python open_rag_benchmark.py --config examples/dummy_project/open_rag_config.json --source-type markdown --top 5 "How does dummy trade approval work?"
```

This mirrors the real-project flow:

1. create a project config,
2. build a local index,
3. ask a focused question,
4. validate the evidence packet before using a model runtime.

## Full flow: with llama-server

Open RAG does not require a model for retrieval. A model is only needed when you
want a natural-language answer from the packet.

Prerequisites:

- a `llama-server` executable from llama.cpp,
- a GGUF instruction model,
- enough memory/compute for the chosen model.

### Start llama-server

PowerShell:

```powershell
& "D:\tmp\llama.cpp\build\bin\Release\llama-server.exe" `
  -m "D:\tmp\models\qwen2.5-coder-3b-instruct-q4_k_m.gguf" `
  --host 127.0.0.1 `
  --port 8768 `
  --log-disable
```

Bash:

```bash
llama-server \
  -m /path/to/model.gguf \
  --host 127.0.0.1 \
  --port 8768 \
  --log-disable
```

Probe the endpoint:

```bash
curl -s http://127.0.0.1:8768/completion \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Say ready in one word.","n_predict":16,"stream":false}'
```

A working server returns JSON with a `content` field.

### Ask the dummy project with the model

Build the index and packet:

```bash
python phase1a_retrieval.py --index /tmp/open_rag_dummy_index.json --config examples/dummy_project/open_rag_config.json build
python phase1a_retrieval.py --index /tmp/open_rag_dummy_index.json --config examples/dummy_project/open_rag_config.json packet "How does dummy trade approval work?" --source-type markdown --top 3 --json > /tmp/open_rag_dummy_packet.json
python phase1b_answer.py check --packet /tmp/open_rag_dummy_packet.json --max-chars-per-evidence 800
```

Send the packet to the local model:

```bash
python phase1b_answer.py answer \
  --packet /tmp/open_rag_dummy_packet.json \
  --runtime json-http \
  --endpoint http://127.0.0.1:8768/completion \
  --max-chars-per-evidence 800 \
  --max-tokens 256 \
  --timeout-seconds 120 \
  --json
```

PowerShell equivalent:

```powershell
python phase1a_retrieval.py --index D:/tmp/open_rag_dummy_index.json --config examples/dummy_project/open_rag_config.json build
python phase1a_retrieval.py --index D:/tmp/open_rag_dummy_index.json --config examples/dummy_project/open_rag_config.json packet "How does dummy trade approval work?" --source-type markdown --top 3 --json > D:/tmp/open_rag_dummy_packet.json
python phase1b_answer.py check --packet D:/tmp/open_rag_dummy_packet.json --max-chars-per-evidence 800
python phase1b_answer.py answer --packet D:/tmp/open_rag_dummy_packet.json --runtime json-http --endpoint http://127.0.0.1:8768/completion --max-chars-per-evidence 800 --max-tokens 256 --timeout-seconds 120 --json
```

Expected result:

- retrieval returns cited evidence from `dummy_project`,
- `check` validates the packet shape,
- `answer` calls `llama-server` and returns model output plus citations.

Example successful answer shape:

```json
{
  "schema": "open_rag.phase1b.answer.v1",
  "mode": "json-http",
  "question": "How does dummy trade approval work?",
  "answer": "Answer\nDummy Trade Service approves a trade after validating buyer and seller ids, checking that the amount is positive, and checking that the amount is within the configured maximum. Rejected trades include a public reason and an audit reason.\n\nEvidence\n- examples/dummy_project/README.md\n- examples/dummy_project/docs/policy.md\n- examples/dummy_project/docs/architecture.md\n\nUnknowns\n- Payment execution is not implemented in TradeService.\n\nUnsupported or not implemented\n- The evidence does not show real payment rail integration.",
  "citations": [
    {
      "path": "README.md",
      "title": "Product behavior"
    },
    {
      "path": "docs/policy.md",
      "title": "Trade Approval Policy"
    }
  ]
}
```

Exact wording depends on the local model. The important checks are:

- `mode` should be `json-http` when the local runtime answered,
- `citations` should point to files from the target project,
- the answer should not claim behavior missing from the evidence,
- strict section parsing may fail on small models even when the answer is useful.

## Local model note

Small local models are useful for cheap offline answers, but they may not follow
strict output formatting every time. In a real mixed-codebase test, a 3B coder
model answered from evidence, but failed the strict section parser on one run and
timed out on a larger packet.

For small models:

- use `--top 2` or `--top 3`,
- keep `--max-chars-per-evidence` around `500-800`,
- keep `--max-tokens` modest,
- treat the evidence packet as the reliable output,
- use a stronger model when strict structured answers are required.
