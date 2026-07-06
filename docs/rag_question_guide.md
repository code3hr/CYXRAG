# RAG Question Guide

## Purpose

Explain how to ask useful questions against the current CyxWiz local RAG
prototype, what kinds of questions work well, and what kinds of questions are
still weak.

## Short Rule

Ask for:

- a file
- a field
- a validation rule
- an operator behavior
- an example graph
- a trace explanation tied to selected context

Do not expect strong answers yet for:

- broad product-help questions
- open-ended tutorials
- vague "what can you do" prompts
- general chat

## Why This Matters

The current system is retrieval-first.

That means:

1. retrieval finds evidence
2. the model answers from that evidence

If retrieval finds the wrong kind of evidence, the answer can still be formally
well-structured but not useful.

## Good Question Shapes

These work well because they point retrieval toward concrete evidence.

### File-definition questions

```text
What source file defines DebugTraceRecord?
What source file defines TrainingTraceEvent?
```

### Field or validation questions

```text
Where does TFIDFVectorizer validate min_df?
TrainingTraceEvent terminal_reason field
```

### Behavior questions tied to explicit terms

```text
DataLoader pin_memory unsupported current batchers compatibility
What does terminal_reason mean in TrainingTraceEvent?
```

### Example-graph questions

```text
TFIDFVectorizer sentiment graph
Which example graph uses TFIDFVectorizer?
```

### Context-backed explanation questions

```text
Explain the selected trace.
Why did this training run stop?
```

These become strongest when backed by active trace or training context.

## Weak Question Shapes

These are likely to retrieve the wrong evidence today.

### Broad capability questions

```text
What can you assist me with in CyxWiz engine?
What is CyxWiz?
How do I use everything?
```

Problem:

- retrieval may latch onto arbitrary files containing "engine" or "config"
- source chunks are not the same thing as product capability docs

### Open-ended procedural questions

```text
How do I build a linear regression with CyxWiz engine?
How do I make a full pipeline?
```

Problem:

- source code may expose implementation truth
- but not user-facing workflow steps
- model may invent procedure beyond evidence

### Vague concept questions

```text
Tell me about training.
Explain graphs.
```

Problem:

- too many possible evidence targets
- weak lexical specificity

## Real Example of a Bad but Structured Answer

Question:

```text
what can u assist me with in cyxwiz engine?
```

Observed retrieval:

- `cyxwiz-engine/src/core/engine_config.cpp`
- `EngineConfig::Save`

Observed answer:

```text
Assistance with saving engine configuration files in CyxWiz engine.
```

Why this is bad:

- it is structurally valid
- but semantically unrelated to the user’s real intent

So:

- parse success is not the same as answer usefulness
- retrieval hit quality still matters more than format compliance

## How to Improve a Weak Question

Rewrite broad questions into concrete evidence-seeking questions.

### Instead of:

```text
What can you assist me with in CyxWiz engine?
```

Ask:

```text
What source file defines DebugTraceRecord?
Where does TFIDFVectorizer validate min_df?
What example graph uses TFIDFVectorizer?
What does terminal_reason mean in TrainingTraceEvent?
```

### Instead of:

```text
How do I build a linear regression with CyxWiz engine?
```

Ask:

```text
Where is LinearRegressionOperator configured?
What parameters does LinearRegressionOperator::Configure accept?
Is there a cyxgraph example for linear regression?
```

## Practical Question Pattern

Use this pattern:

```text
What file / where / what field / what validation / what example / what does X mean
```

This works better than:

```text
How do I do everything about X?
```

## Recommended Workflow

1. Start with retrieval
2. Check top citation
3. If the top citation looks wrong, rewrite the question
4. Only then run the full probe

Example:

```powershell
python "docs/Data Studio/tofix42/phase1a_retrieval.py" search "What source file defines DebugTraceRecord?"
```

If retrieval is correct, continue:

```powershell
powershell -ExecutionPolicy Bypass -File `
  "D:\Dev\CyxWiz_Claude\docs\Data Studio\tofix42\run_my_test.ps1" `
  "What source file defines DebugTraceRecord?"
```

## Trust Rule

Treat the current RAG as:

- a local codebase evidence assistant
- a retrieval-backed explainer

Do not treat it yet as:

- a broad product help bot
- a tutorial generator
- a general conversational assistant

## Recommendation

For the current system, the best user questions are:

```text
specific
evidence-seeking
repo-grounded
```

That is the right way to get meaningful answers out of the current CyxWiz RAG
prototype.
