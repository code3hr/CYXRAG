# tofix42 Init Call Plan

## Purpose

Use this plan to align the first implementation phases for the local CyxWiz
source-aware assistant.

The guiding decision is fixed:

```text
Phase 1 = local small model + retrieval over CyxWiz source/docs/graphs/traces
Phase later = optional fine-tuning after reviewed CyxWiz-specific examples exist
```

## Lean Guardrails

Use `lean-software-guardrails` for tofix42 planning and implementation.

Principles:

- Prove one thin vertical slice before broadening the assistant.
- Treat every model, dependency, service, cache, UI surface, and configuration
  knob as a cost until it proves necessary.
- Keep the assistant optional. Engine training must not depend on it.
- Prefer plain local files and deterministic test fixtures before databases,
  background services, or broad plugin hooks.
- Keep boundaries narrow: indexer, retriever, context builder, model runtime,
  and UI caller should each have one clear job.
- Add extensibility through small replaceable modules, not a broad core.
- Avoid implementing graph/source mutation in the first plan.
- Validate with small questions that have known answers in the repository.

First lean slice:

```text
docs/source/graph files -> local index -> retrieval test questions -> cited answer
```

Only after that slice works should Studio Debugger integration and model
runtime polish expand.

## Phase 0: Scope Lock

Goal: agree on what the first assistant is and is not.

Decisions:

- Assistant is local-first and offline-capable.
- Assistant is read-only in the first implementation.
- Retrieval is the source of truth.
- Fine-tuning is explicitly deferred.
- Engine training/build/test work is not part of tofix42.
- No graph or source mutation happens without later explicit approval flow.

Outputs:

- confirm design docs are the current plan
- confirm first surface is a command/internal harness before UI, unless Studio
  Debugger integration is explicitly chosen
- confirm first indexed roots are intentionally small
- confirm model/runtime evaluation target
- confirm the minimum answer contract

Lean phase gate:

- one-page decision record is enough
- no implementation work starts until the first three success questions are
  agreed
- no dependency choice is final until retrieval works on local text fixtures

Recommended Phase 0 decisions:

- First surface: internal command/test harness.
- First roots: `docs/Data Studio/tofix42`, `docs/usage`, selected debugger and
  training trace source headers, and `examples/cyxgraph/Sentiment analysis`.
- First answer contract: answer, evidence citations, unsupported/unknown.
- First source precedence: structured runtime context, source, active graph,
  docs, older tofix notes, logs.

## Phase 1: Corpus and Index Prototype

Goal: build a local index that can answer from CyxWiz files.

Lean scope:

- Start with local text files only.
- Do not add a vector database yet if lexical retrieval can prove the first
  questions.
- Do not watch the filesystem yet. Use manual rebuild first.
- Do not index private dataset rows or binary model weights.
- Do not run a local LLM yet if retrieval quality is not proven.

Initial inputs:

- `docs/Data Studio/tofix42/`
- `docs/usage/`
- `examples/cyxgraph/Sentiment analysis/README.md`
- `examples/cyxgraph/Sentiment analysis/*.cyxgraph`
- `cyxwiz-engine/src/core/debug_trace_record.h`
- `cyxwiz-engine/src/core/training_trace_collector.h`
- `cyxwiz-engine/src/core/debug_run_store.h`

Later inputs:

- `docs/`
- `docs/Data Studio/`
- `cyxwiz-engine/src`
- `cyxwiz-backend/src`
- `examples/cyxgraph/`

Work:

- define chunk schema
- chunk markdown by heading
- chunk source by symbol where possible
- chunk `.cyxgraph` files by graph, node, params, and links
- compute content hashes
- store local index metadata
- add simple lexical search before vector search if needed

Thin implementation shape:

- `Chunk`: id, source type, path, optional line range, title/symbol, text, hash,
  tags
- `Index`: list of chunks persisted as local JSON
- `Search`: lexical scoring over chunk text, path, title/symbol, and tags
- `AnswerPacket`: question, top chunks, citations, missing-evidence notes

Exit criteria:

- can retrieve docs/source/graph snippets for a query
- results include path and line or graph metadata
- changed files can be detected
- three first success questions retrieve the expected evidence

Phase 1 success questions:

- What source file defines `DebugTraceRecord`?
- What does `terminal_reason` mean in a training trace?
- What graph files show TF-IDF sentiment classification?

## Phase 2: Local Model Runtime

Goal: connect a small local answer model to retrieved context.

Lean scope:

- Use one answer model backend first.
- Keep embedding model optional until lexical retrieval hits its limit.
- Keep model configuration to path, context size, and max output tokens.
- Do not add model download/install automation in the first pass.

Work:

- choose first runtime path
- choose first small instruct model profile
- choose embedding model profile
- define assistant prompt contract
- return cited answers
- handle model unavailable states cleanly

Exit criteria:

- answer from retrieved context
- cite files/graphs/docs used
- say when evidence is missing
- do not claim unsupported CyxWiz behavior

Phase gate:

- the model is not useful until Phase 1 retrieval produces the right evidence
- if the model cannot cite evidence consistently, keep it out of Studio UI

## Phase 3: Debugger Explanation Slice

Goal: make the first Studio integration useful for engine work.

First target:

- Studio Debugger selected warning/error/trace explanation

Context to pass:

- selected `DebugTraceRecord`
- run id
- node id/name/type
- phase and role
- issues
- payload
- related active graph
- latest training trace when relevant

Exit criteria:

- answer what happened, where, likely why, and what to inspect next
- cite trace fields and source/docs
- distinguish fact from inference
- do not rely only on rendered UI text

Lean scope:

- one button or command: `Explain selected trace`
- one context object: selected trace plus run id
- no chat history required for the first slice
- no graph/source edits

## Phase 4: Training Trace Explanation

Goal: explain training run state and terminal reasons.

Context:

- `TrainingTraceSummary`
- `terminal_reason`
- recent events
- materialization events
- warnings
- checkpoint records

Questions:

- Why did training stop?
- Was this completed, early-stopped, cancelled, or failed?
- What warning likely mattered?
- What source or graph node owns the issue?

Exit criteria:

- terminal state is explained from trace data
- materialization failures are linked to graph/source when possible
- warnings are not overstated as proven root causes

Lean scope:

- start with last run only
- explain terminal state before attempting curve diagnosis
- do not build broad metric analytics until trace explanation is reliable

## Phase 5: Graph-Aware Help

Goal: help users understand and draft graphs without applying changes.

Work:

- selected node explanation
- selected property explanation
- graph path explanation
- graph improvement suggestions
- graph draft generation
- optional preflight check as a later approval step

Exit criteria:

- graph drafts use supported node types and properties
- assumptions and risks are listed
- no graph mutation happens automatically

Lean scope:

- start with node/property explanation before graph generation
- generate graph plans before generating full `.cyxgraph` JSON
- require preflight before any future apply step

## Phase 6: Evaluation and QA Capture

Goal: measure quality before any fine-tuning discussion.

Work:

- create retrieval tests for known files/symbols
- create debugger explanation fixtures
- create training trace explanation fixtures
- create graph draft validity fixtures
- record bad answers
- collect reviewed corrections

Exit criteria:

- answer failures are reproducible
- quality can be compared across models
- reviewed examples are ready for future training data

Lean scope:

- keep fixtures tiny and readable
- prefer deterministic expected citations over broad subjective grading
- capture failures as plain markdown/JSON examples first

## Phase 7: Optional Fine-Tuning Decision

Goal: decide whether fine-tuning is worth the maintenance cost.

Only start if:

- RAG assistant works
- enough reviewed examples exist
- graph drafts have validation evidence
- debugger examples have trace evidence
- source/docs retrieval remains mandatory

Exit criteria:

- fine-tuning experiment is approved or rejected from evidence
- retrieval remains the truth layer either way

Lean rejection rule:

- if retrieval plus base model is good enough, do not fine-tune
- if fine-tuning weakens citations or unsupported-feature refusal, reject it

## First Call Agenda

1. Confirm the first assistant surface: Studio Debugger vs command prototype.
2. Confirm first indexed roots and excluded data.
3. Pick first runtime path for model and embeddings.
4. Define the minimum answer format.
5. Define first success test questions.
6. Assign Phase 1 implementation owner.

## First Success Questions

- What source file defines `DebugTraceRecord`?
- What does `terminal_reason` mean in a training trace?
- Why did this selected debugger trace fail?
- What does the `DataLoader` `pin_memory` property actually guarantee today?
- Generate a draft text-classification graph using supported CyxWiz nodes.
- Point me to the likely source responsible for a TF-IDF materialization error.

## Immediate Next Work

Start with Phase 1A, not the full assistant.

Phase 1A deliverable:

- a tiny local index format
- a manual rebuild command or test harness
- lexical retrieval over the initial inputs
- expected evidence for the first three success questions

Phase 1A non-goals:

- no Studio UI
- no local LLM
- no embeddings
- no background watcher
- no database
- no graph/source mutation
- no fine-tuning

Phase 1B deliverable:

- add a local model runtime behind a narrow interface
- feed retrieved chunks into the prompt
- produce a cited answer packet

Phase 1C deliverable:

- connect the answer packet to one Studio Debugger explanation path
- keep the UI surface narrow and read-only
