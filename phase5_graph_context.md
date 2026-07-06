# tofix42 Phase 5 Graph Context

## Purpose

Explain a selected graph node from a local `.cyxgraph` file without mutating the
graph or requiring a model server.

This Phase 5 slice is read-only. It reports selected node identity,
parameters, incoming and outgoing links, nearby nodes, graph paths, deterministic
suggestions, structural audit checks, graph draft plans, and retrieved source
citations. It does not generate final `.cyxgraph` JSON or apply graph edits.

## Commands

Build selected-node context:

```powershell
python "docs/Data Studio/tofix42/phase5_graph_context.py" context `
  --graph "examples/cyxgraph/Sentiment analysis/sentiment_analysis_tfidf_mlp_classifier.cyxgraph" `
  --node-id 2 `
  --pretty
```

Explain the selected node:

```powershell
python "docs/Data Studio/tofix42/phase5_graph_context.py" explain `
  --graph "examples/cyxgraph/Sentiment analysis/sentiment_analysis_tfidf_mlp_classifier.cyxgraph" `
  --node-id 2
```

Explain one selected node parameter:

```powershell
python "docs/Data Studio/tofix42/phase5_graph_context.py" explain `
  --graph "examples/cyxgraph/Sentiment analysis/sentiment_analysis_tfidf_mlp_classifier.cyxgraph" `
  --node-id 2 `
  --parameter min_df
```

Build a Phase 1B-compatible packet:

```powershell
python "docs/Data Studio/tofix42/phase5_graph_context.py" packet `
  --graph "examples/cyxgraph/Sentiment analysis/sentiment_analysis_tfidf_mlp_classifier.cyxgraph" `
  --node-id 2 `
  --top 5
```

Build a Phase 1B-compatible packet focused on a parameter:

```powershell
python "docs/Data Studio/tofix42/phase5_graph_context.py" packet `
  --graph "examples/cyxgraph/Sentiment analysis/sentiment_analysis_tfidf_mlp_classifier.cyxgraph" `
  --node-id 2 `
  --parameter min_df `
  --top 5
```

Explain a directed graph path:

```powershell
python "docs/Data Studio/tofix42/phase5_graph_context.py" path `
  --graph "examples/cyxgraph/Sentiment analysis/sentiment_analysis_tfidf_mlp_classifier.cyxgraph" `
  --from-node-id 1 `
  --to-node-id 4
```

Build a Phase 1B-compatible packet for a directed graph path:

```powershell
python "docs/Data Studio/tofix42/phase5_graph_context.py" path-packet `
  --graph "examples/cyxgraph/Sentiment analysis/sentiment_analysis_tfidf_mlp_classifier.cyxgraph" `
  --from-node-id 1 `
  --to-node-id 4 `
  --top 5
```

Emit read-only graph improvement suggestions:

```powershell
python "docs/Data Studio/tofix42/phase5_graph_context.py" suggest `
  --graph "examples/cyxgraph/Sentiment analysis/sentiment_analysis_tfidf_mlp_classifier.cyxgraph" `
  --pretty
```

Build a Phase 1B-compatible packet for graph suggestions:

```powershell
python "docs/Data Studio/tofix42/phase5_graph_context.py" suggest-packet `
  --graph "examples/cyxgraph/Sentiment analysis/sentiment_analysis_tfidf_mlp_classifier.cyxgraph" `
  --top 5
```

Emit a read-only graph audit:

```powershell
python "docs/Data Studio/tofix42/phase5_graph_context.py" audit `
  --graph "examples/cyxgraph/Sentiment analysis/sentiment_analysis_tfidf_mlp_classifier.cyxgraph" `
  --pretty
```

Build a Phase 1B-compatible packet for a graph audit:

```powershell
python "docs/Data Studio/tofix42/phase5_graph_context.py" audit-packet `
  --graph "examples/cyxgraph/Sentiment analysis/sentiment_analysis_tfidf_mlp_classifier.cyxgraph" `
  --top 5
```

Emit a read-only graph draft plan:

```powershell
python "docs/Data Studio/tofix42/phase5_graph_context.py" draft-plan `
  --template text-classification-tfidf-mlp `
  --pretty
```

Build a Phase 1B-compatible packet for a graph draft plan:

```powershell
python "docs/Data Studio/tofix42/phase5_graph_context.py" draft-plan-packet `
  --template text-classification-tfidf-mlp `
  --top 5
```

Run the deterministic gate:

```powershell
python "docs/Data Studio/tofix42/phase5_graph_context.py" check
```

## Output

Context schema: `cyxwiz.tofix42.phase5.graph_node_context.v1`

Explanation schema: `cyxwiz.tofix42.phase5.graph_node_explanation.v1`

Path context schema: `cyxwiz.tofix42.phase5.graph_path_context.v1`

Path explanation schema: `cyxwiz.tofix42.phase5.graph_path_explanation.v1`

Suggestions schema: `cyxwiz.tofix42.phase5.graph_suggestions.v1`

Audit schema: `cyxwiz.tofix42.phase5.graph_audit.v1`

Draft plan schema: `cyxwiz.tofix42.phase5.graph_draft_plan.v1`

The packet command emits the existing
`cyxwiz.tofix42.phase1a.answer_packet.v1` shape with `graph_context` preserved
for downstream callers.

## Boundary

This slice does not mutate graphs, generate final `.cyxgraph` JSON, launch
training, or claim runtime support without cited source evidence. Sensitive
parameter keys such as paths, dataset names, raw previews, tokens, and secrets
are redacted.
