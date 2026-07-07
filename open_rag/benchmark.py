#!/usr/bin/env python3
"""Benchmark Open RAG packet size against indexed full-context size."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from time import perf_counter

from . import phase1a_retrieval
from . import phase1b_answer


SCHEMA = "open_rag.benchmark.v1"


def estimate_tokens(text: str) -> int:
    # A conservative model-agnostic estimate. Exact tokenizer counts vary by model.
    return max(1, math.ceil(len(text) / 4))


def pct_reduction(full_tokens: int, packet_tokens: int) -> float:
    if full_tokens <= 0:
        return 0.0
    return round((1.0 - (packet_tokens / full_tokens)) * 100.0, 2)


def full_context_prompt(question: str, files: list[Path]) -> tuple[str, int]:
    parts = [
        "You are answering from the repository context below.",
        f"Question: {question}",
        "Repository context:",
    ]
    total_bytes = 0
    for path in files:
        text = phase1a_retrieval.read_text(path)
        total_bytes += len(text.encode("utf-8", errors="replace"))
        parts.append(f"\n[FILE] {phase1a_retrieval.repo_rel(path)}\n{text}")
    return "\n".join(parts), total_bytes


def filters_from_args(args: argparse.Namespace) -> phase1a_retrieval.SearchFilters:
    return phase1a_retrieval.SearchFilters(
        source_types=[item.lower() for item in args.source_type],
        path_contains=[item.lower() for item in args.path_contains],
        title_contains=[item.lower() for item in args.title_contains],
        tags=[item.lower() for item in args.tag],
    )


def run(args: argparse.Namespace) -> dict:
    config = phase1a_retrieval.load_config(args.config, args.project_root)

    t0 = perf_counter()
    files = phase1a_retrieval.iter_initial_files(config["source_patterns"])
    full_prompt, total_bytes = full_context_prompt(args.query, files)
    full_read_ms = round((perf_counter() - t0) * 1000, 2)

    t1 = perf_counter()
    index = phase1a_retrieval.build_index(config)
    build_ms = round((perf_counter() - t1) * 1000, 2)
    if args.index:
        phase1a_retrieval.save_index(index, args.index)

    filters = filters_from_args(args)
    t2 = perf_counter()
    packet = phase1a_retrieval.make_answer_packet(
        index,
        args.query,
        args.top,
        filters,
        packet_mode=args.mode,
    )
    packet_ms = round((perf_counter() - t2) * 1000, 2)

    packet_json = json.dumps(packet, ensure_ascii=True, separators=(",", ":"))
    packet_prompt = phase1b_answer.build_prompt(packet, args.max_chars_per_evidence)

    full_tokens = estimate_tokens(full_prompt)
    packet_prompt_tokens = estimate_tokens(packet_prompt)
    packet_json_tokens = estimate_tokens(packet_json)

    return {
        "schema": SCHEMA,
        "question": args.query,
        "config": {
            "path": str(args.config),
            "project_root": config["project_root"],
            "source_patterns": config["source_patterns"],
        },
        "scope": {
            "indexed_files": len(files),
            "index_chunks": index.get("chunk_count", len(index.get("chunks", []))),
            "indexed_bytes": total_bytes,
        },
        "timings_ms": {
            "read_full_context": full_read_ms,
            "build_index": build_ms,
            "make_packet": packet_ms,
        },
        "tokens_estimated": {
            "method": "ceil(characters / 4)",
            "full_indexed_context_prompt": full_tokens,
            "packet_prompt": packet_prompt_tokens,
            "packet_json": packet_json_tokens,
            "packet_prompt_reduction_percent": pct_reduction(full_tokens, packet_prompt_tokens),
            "packet_json_reduction_percent": pct_reduction(full_tokens, packet_json_tokens),
        },
        "packet": {
            "strategy": packet.get("strategy"),
            "source_miss": packet.get("source_miss"),
            "fallback_used": packet.get("fallback_used"),
            "evidence_hits": packet.get("metrics", {}).get("evidence_hits", 0),
            "top": args.top,
            "max_chars_per_evidence": args.max_chars_per_evidence,
            "citations": [item.get("citation", {}) for item in packet.get("evidence", [])],
        },
    }


def print_markdown(report: dict) -> None:
    tokens = report["tokens_estimated"]
    scope = report["scope"]
    timings = report["timings_ms"]
    packet = report["packet"]
    print("# Open RAG Benchmark")
    print("")
    print(f"Question: {report['question']}")
    print("")
    print("## Scope")
    print(f"- indexed files: {scope['indexed_files']}")
    print(f"- index chunks: {scope['index_chunks']}")
    print(f"- indexed bytes: {scope['indexed_bytes']}")
    print("")
    print("## Timing")
    print(f"- read full context: {timings['read_full_context']} ms")
    print(f"- build index: {timings['build_index']} ms")
    print(f"- make packet: {timings['make_packet']} ms")
    print("")
    print("## Estimated Tokens")
    print(f"- full indexed context prompt: {tokens['full_indexed_context_prompt']}")
    print(f"- packet prompt: {tokens['packet_prompt']}")
    print(f"- packet JSON: {tokens['packet_json']}")
    print(f"- packet prompt reduction: {tokens['packet_prompt_reduction_percent']}%")
    print(f"- packet JSON reduction: {tokens['packet_json_reduction_percent']}%")
    print("")
    print("## Packet")
    print(f"- evidence hits: {packet['evidence_hits']}")
    print(f"- source miss: {str(packet['source_miss']).lower()}")
    print(f"- fallback used: {str(packet['fallback_used']).lower()}")
    print("")
    print("## Citations")
    for citation in packet["citations"]:
        print(
            f"- {citation.get('path', '')}:"
            f"{citation.get('line_start', '')}-{citation.get('line_end', '')}"
            f" ({citation.get('title', '')})"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark Open RAG token and timing reduction")
    parser.add_argument("query")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--mode", choices=sorted(phase1a_retrieval.PACKET_MODES), default="packet-only")
    parser.add_argument("--max-chars-per-evidence", type=int, default=1200)
    parser.add_argument("--source-type", action="append", default=[])
    parser.add_argument("--path-contains", action="append", default=[])
    parser.add_argument("--title-contains", action="append", default=[])
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = run(args)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        print_markdown(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
