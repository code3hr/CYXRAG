# tofix42 Phase 1B Answer Adapter

## Scope

Phase 1B starts with a minimal answer adapter over Phase 1A retrieval packets.

It does:

- consume `cyxwiz.tofix42.phase1a.answer_packet.v1`
- build a strict evidence-grounded prompt
- emit runtime-unavailable answers with citations when no runner is configured
- optionally call an explicit local `llama-cli`-style runner
- optionally call a configured local JSON HTTP runtime endpoint
- parse successful runner output into the requested answer sections
- emit structured runner error details when local inference fails or times out

It does not:

- download models
- call network services
- add embeddings
- add a vector database
- add Studio UI
- mutate graphs or source files
- fine-tune

## Prompt

Generate a strict prompt from a packet:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" prompt --packet "D:/tmp/tofix42_packet.json"
```

## Runtime-Unavailable Answer

When no local runner is configured, return a clean answer envelope with
citations and an explicit unavailable note:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" answer --packet "D:/tmp/tofix42_packet.json" --runtime none --json
```

PowerShell pipe form:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" packet "DataLoader pin_memory unsupported current batchers compatibility" --top 1 --json |
  python "docs/Data Studio/tofix42/phase1b_answer.py" answer --runtime none --json
```

## Doctor

Check adapter readiness:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" doctor --runtime none --json
python "docs/Data Studio/tofix42/phase1b_answer.py" doctor --runtime llama-cli --runner "llama-cli" --model "smollm-135m.Q4_K_M.gguf" --json
```

Validate a packet and report runner/model availability:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" doctor --packet "D:/tmp/tofix42_packet.json" --runtime llama-cli --json
```

`doctor` checks paths and packet validity. It does not load the model or run
inference.

## Local Runner

If a compatible `llama-cli` executable exists:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" answer `
  --packet "D:/tmp/tofix42_packet.json" `
  --runtime llama-cli `
  --runner "llama-cli" `
  --model "smollm-135m.Q4_K_M.gguf" `
  --max-tokens 32 `
  --timeout-seconds 120 `
  --json
```

With `--json`, runner failures return a `runtime_error` envelope containing the
runner command, exit code when available, timeout flag, and bounded stdout/stderr
excerpts. The process still exits with code `2` for failed local inference.

The adapter invokes `llama-cli` with single-turn, no-display-prompt, and
simple-io style flags. It also disables runner logs, disables warmup, closes
stdin, and adds a final prompt sentinel so echoed prompt text can be stripped
before parsing stdout. Recent llama.cpp builds can otherwise auto-enable
conversation mode for chat-template models, write UI/banner text to stdout, or
leave the subprocess waiting for more input until the adapter timeout kills it.

Successful local-runner JSON keeps the full `raw_model_output` and also fills
`model_output_sections` from the requested headings:

- `Answer:`
- `Evidence:`
- `Unknowns:`
- `Unsupported or not implemented:`

No runner is assumed or downloaded by Phase 1B.

## Local JSON Runtime

Phase 2 adds an optional local JSON HTTP runtime path without changing the
Phase 1A packet schema or Phase 1B answer envelope.

Check the configured endpoint without probing it:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" doctor `
  --packet "D:/tmp/tofix42_packet.json" `
  --runtime json-http `
  --endpoint "http://127.0.0.1:8080/completion" `
  --json
```

Call a running local JSON endpoint:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" answer `
  --packet "D:/tmp/tofix42_packet.json" `
  --runtime json-http `
  --endpoint "http://127.0.0.1:8080/completion" `
  --max-tokens 384 `
  --timeout-seconds 120 `
  --json
```

The adapter posts:

```json
{
  "prompt": "<strict Phase 1B prompt>",
  "n_predict": 384,
  "stream": false
}
```

Accepted response shapes include:

- `{ "content": "Answer: ..." }`
- `{ "response": "Answer: ..." }`
- `{ "completion": "Answer: ..." }`
- `{ "generated_text": "Answer: ..." }`
- `{ "text": "Answer: ..." }`
- `{ "choices": [{ "message": { "content": "Answer: ..." } }] }`
- `{ "choices": [{ "text": "Answer: ..." }] }`

The adapter does not start a server, download a model, or contact external
network services by itself. `json-http` only accepts `localhost`, `127.0.0.1`,
or `::1` endpoints.

## First Test Packet

Create a packet from Phase 1A:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" packet "DataLoader pin_memory unsupported current batchers compatibility" --top 1 --json > "D:/tmp/tofix42_packet.json"
```

Then run:

```powershell
python "docs/Data Studio/tofix42/phase1b_answer.py" prompt --packet "D:/tmp/tofix42_packet.json"
python "docs/Data Studio/tofix42/phase1b_answer.py" answer --packet "D:/tmp/tofix42_packet.json" --runtime none --json
python "docs/Data Studio/tofix42/phase1b_answer.py" check --packet "D:/tmp/tofix42_packet.json"
```

Expected behavior:

- prompt cites `graph_compiler.cpp`
- runtime-unavailable answer includes the citation
- no unsupported claim is made
- no graph/source mutation occurs

## Phase 1B Check

The `check` command verifies:

- strict prompt instruction is present
- the model-output sentinel is present and echoed prompt text can be stripped
- expected source citation is present
- relevant `pin_memory` warning text survives prompt truncation
- runtime-unavailable answer envelope has schema, mode, and citations
- runtime-error answer envelope preserves runner failure details
- successful runner output can be parsed into answer sections
- stubbed JSON runtime success and failure follow the same answer/error
  envelope contract
- the JSON HTTP adapter can post to an in-process localhost fixture and handle
  both success and HTTP failure responses
- non-local JSON runtime endpoints are rejected before any request is made

Packet input accepts UTF-8 and UTF-16 text so PowerShell redirected JSON works.
