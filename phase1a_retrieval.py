#!/usr/bin/env python3
"""Phase 1A local retrieval prototype.

This is intentionally small:
- stdlib only
- manual rebuild
- JSON index
- lexical scoring only
- no model runtime, embeddings, watcher, database, or Studio UI
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from time import monotonic
from typing import Iterable


RAG_NAMESPACE = "open_rag"
RAG_PREFIX = f"{RAG_NAMESPACE}.phase1a"
REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_INDEX = Path(__file__).with_name("phase1a_index.json")
DEFAULT_CONFIG = Path(__file__).with_name("open_rag_config.example.json")
LEGACY_DEFAULT_CONFIG = Path(__file__).with_name("phase1a_config.json")
SCHEMA_INDEX = f"{RAG_PREFIX}.lexical_index.v1"
SCHEMA_SEARCH_REPORT = f"{RAG_PREFIX}.search_report.v1"
SCHEMA_ANSWER_PACKET = f"{RAG_PREFIX}.answer_packet.v1"
SCHEMA_SAVED_QUERIES = f"{RAG_PREFIX}.saved_queries.v1"
SCHEMA_FALLBACK_STATE = f"{RAG_PREFIX}.fallback_state.v1"
SCHEMA_NON_REDISCOVERABLE = f"{RAG_PREFIX}.non_rediscoverable.v1"
SCHEMA_CONFIG_FALLBACK = f"{RAG_PREFIX}.config.fallback"
SCHEMA_CONFIG_UNKNOWN = f"{RAG_PREFIX}.config.unknown"
MAX_SOURCE_CHUNK_LINES = 120
SOURCE_CHUNK_OVERLAP_LINES = 20
FALLBACK_GREP_CONTEXT_LINES = 10
FALLBACK_GREP_MAX_FILES = 200
FALLBACK_GREP_TIMEOUT_MS = 1500
FALLBACK_BUDGET_WARNING_THRESHOLD = 4
FALLBACK_STATE_MAX_EVENTS = 500
FALLBACK_STATE_SUFFIX = ".fallback_state.json"
SCHEMA_FALLBACK_USAGE_REPORT = f"{RAG_PREFIX}.fallback_usage_report.v1"
REDISCOVERABLE_KIND = "rediscoverable"
NON_REDISCOVERABLE_KIND = "non_rediscoverable"

FALLBACK_PATTERNS = [
    "README*",
    "docs/**/*.md",
    "src/**/*.md",
    "src/**/*.py",
    "src/**/*.ts",
    "src/**/*.js",
    "src/**/*.cpp",
    "src/**/*.hpp",
    "src/**/*.h",
    "src/**/*.cc",
    "src/**/*.cxx",
    "src/**/*.c",
    "src/**/*.json",
]

FALLBACK_SUCCESS_CHECKS = [
    # Keep empty default checks for generic compatibility. Use your project config
    # to define project-specific checks.
]

FALLBACK_SAVED_QUERIES = [
    {
        "name": "project_overview",
        "description": "Entry docs and usage information for quick startup.",
        "query": "project overview",
        "source_types": ["markdown"],
        "path_contains": ["readme"],
    }
]

WORD_RE = re.compile(r"[A-Za-z0-9_./:-]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "does",
    "file",
    "for",
    "from",
    "in",
    "is",
    "me",
    "of",
    "show",
    "source",
    "the",
    "this",
    "to",
    "what",
    "where",
    "which",
    "who",
}
SOURCE_TYPE_BOOST = {
    "source": 40,
    "cyxgraph": 30,
    "cyxgraph_node": 25,
    "cyxgraph_links": 10,
    "markdown": 0,
    "text": 0,
}
BROAD_HELP_TERMS = {
    "assist",
    "assistant",
    "capabilities",
    "capability",
    "help",
    "overview",
    "use",
}
PACKET_MODES = {"packet-only", "fetch-first", "memory-first"}
DEFAULT_PACKET_MODE = "packet-only"


def packet_mode_to_strategy(mode: str) -> str:
    return {
        "packet-only": "indexed-retrieval",
        "fetch-first": "fetch-first",
        "memory-first": "memory-hit",
    }.get(mode, "indexed-retrieval")
CPP_DECL_RE = re.compile(
    r"^\s*(?:struct|class|enum\s+class|enum)\s+([A-Za-z_][A-Za-z0-9_]*)\b"
)
CPP_METHOD_RE = re.compile(
    r"^\s*(?:[A-Za-z_:<>~*&]+\s+)+([A-Za-z_][A-Za-z0-9_:~]*::[A-Za-z_][A-Za-z0-9_~]*)\s*\("
)
MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def resolve_project_root(
    explicit_root: Path | str | None,
    *,
    config_root: str | None = None,
    config_path: Path | None = None,
) -> Path:
    if explicit_root is not None:
        root = Path(explicit_root)
        if not root.is_absolute() and config_path is not None:
            root = (config_path.parent / root).resolve()
        return root.resolve()

    if config_root:
        root = Path(config_root)
        if not root.is_absolute() and config_path is not None:
            root = (config_path.parent / root).resolve()
        return root.resolve()

    if config_path is not None:
        return config_path.parent.resolve()

    return Path(__file__).resolve().parent


def activate_project_root(project_root: Path | str) -> Path:
    global REPO_ROOT
    REPO_ROOT = Path(project_root).resolve()
    return REPO_ROOT


@dataclass
class Chunk:
    id: str
    source_type: str
    path: str
    line_start: int
    line_end: int
    title: str
    text: str
    content_hash: str
    tags: list[str]
    kind: str = REDISCOVERABLE_KIND


@dataclass
class IndexedFile:
    path: str
    source_type: str
    content_hash: str
    size_bytes: int


@dataclass
class SearchFilters:
    source_types: list[str]
    path_contains: list[str]
    title_contains: list[str]
    tags: list[str]


@dataclass
class SavedQueryPreset:
    name: str
    description: str
    query: str
    filters: SearchFilters


def repo_rel(path: Path) -> str:
    normalized = path.resolve()
    try:
        return normalized.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return normalized.as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def stable_id(path: str, title: str, line_start: int, text: str) -> str:
    digest = hashlib.sha1(f"{path}:{title}:{line_start}:{text}".encode("utf-8")).hexdigest()
    return digest[:16]


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tags_for(path: Path, source_type: str, extra: Iterable[str] = ()) -> list[str]:
    parts = re.split(r"[/\\ ._-]+", repo_rel(path).lower())
    tags = {source_type, path.suffix.lower().lstrip(".")}
    tags.update(part for part in parts if part)
    tags.update(item.lower() for item in extra if item)
    return sorted(tags)


def make_chunk(
    path: Path,
    source_type: str,
    line_start: int,
    line_end: int,
    title: str,
    text: str,
    kind: str = REDISCOVERABLE_KIND,
    extra_tags: Iterable[str] = (),
) -> Chunk:
    rel = repo_rel(path)
    return Chunk(
        id=stable_id(rel, title, line_start, text),
        source_type=source_type,
        path=rel,
        line_start=line_start,
        line_end=line_end,
        title=title,
        text=text.strip(),
        content_hash=content_hash(text),
        tags=tags_for(path, source_type, extra_tags),
        kind=kind,
    )


def chunk_markdown(path: Path, text: str) -> list[Chunk]:
    lines = text.splitlines()
    starts: list[tuple[int, str]] = []
    for idx, line in enumerate(lines, start=1):
        match = MARKDOWN_HEADING_RE.match(line)
        if match:
            starts.append((idx, match.group(2).strip()))

    if not starts:
        return [make_chunk(path, "markdown", 1, len(lines), path.name, text)]

    chunks: list[Chunk] = []
    for i, (start, title) in enumerate(starts):
        end = starts[i + 1][0] - 1 if i + 1 < len(starts) else len(lines)
        body = "\n".join(lines[start - 1 : end])
        chunks.append(make_chunk(path, "markdown", start, end, title, body))
    return chunks


def chunk_cpp(path: Path, text: str) -> list[Chunk]:
    lines = text.splitlines()
    declarations: list[tuple[int, str]] = []
    for idx, line in enumerate(lines, start=1):
        match = CPP_DECL_RE.match(line)
        if match:
            declarations.append((idx, match.group(1)))
            continue
        match = CPP_METHOD_RE.match(line)
        if match:
            stripped = line.lstrip()
            if stripped.startswith(("return ", ":")):
                continue
            prefix = line[: match.start(1)]
            if "=" in prefix:
                continue
            declarations.append((idx, match.group(1)))

    chunks: list[Chunk] = []
    for i, (start, title) in enumerate(declarations):
        end = declarations[i + 1][0] - 1 if i + 1 < len(declarations) else min(len(lines), start + 120)
        chunk_start = start
        while chunk_start <= end:
            chunk_end = min(end, chunk_start + MAX_SOURCE_CHUNK_LINES - 1)
            body = "\n".join(lines[chunk_start - 1 : chunk_end])
            if not body.strip():
                if chunk_end >= end:
                    break
                chunk_start = max(chunk_start + 1, chunk_end - SOURCE_CHUNK_OVERLAP_LINES + 1)
                continue
            chunk_title = title
            if chunk_start != start or chunk_end != end:
                chunk_title = f"{title}:{chunk_start}-{chunk_end}"
            chunks.append(
                make_chunk(path, "source", chunk_start, chunk_end, chunk_title, body, [title])
            )
            if chunk_end >= end:
                break
            chunk_start = max(chunk_start + 1, chunk_end - SOURCE_CHUNK_OVERLAP_LINES + 1)

    if chunks:
        return chunks

    window = 80
    for start in range(1, len(lines) + 1, window):
        end = min(len(lines), start + window - 1)
        body = "\n".join(lines[start - 1 : end])
        chunks.append(make_chunk(path, "source", start, end, f"{path.name}:{start}-{end}", body))
    return chunks


def chunk_cyxgraph(path: Path, text: str) -> list[Chunk]:
    try:
        graph = json.loads(text)
    except json.JSONDecodeError:
        return [make_chunk(path, "cyxgraph", 1, len(text.splitlines()), path.name, text)]

    chunks: list[Chunk] = []
    name = str(graph.get("name") or path.stem)
    description = str(graph.get("description") or "")
    params = graph.get("parameters") or []
    summary = {
        "name": name,
        "description": description,
        "parameters": params,
    }
    chunks.append(
        make_chunk(
            path,
            "cyxgraph",
            1,
            len(text.splitlines()),
            f"graph:{name}",
            json.dumps(summary, indent=2, ensure_ascii=True),
            ["graph", name],
        )
    )

    nodes = graph.get("nodes") or []
    for node in nodes:
        node_id = str(node.get("id") or "")
        node_type = str(node.get("type") or "")
        node_name = str(node.get("name") or node_id or node_type)
        title = f"node:{node_name}:{node_type}"
        chunks.append(
            make_chunk(
                path,
                "cyxgraph_node",
                1,
                len(text.splitlines()),
                title,
                json.dumps(node, indent=2, ensure_ascii=True),
                ["node", node_id, node_type, node_name],
            )
        )

    links = graph.get("links") or graph.get("connections") or []
    if links:
        chunks.append(
            make_chunk(
                path,
                "cyxgraph_links",
                1,
                len(text.splitlines()),
                f"links:{name}",
                json.dumps(links, indent=2, ensure_ascii=True),
                ["links", name],
            )
        )

    return chunks


def chunk_file(path: Path) -> list[Chunk]:
    text = read_text(path)
    suffix = path.suffix.lower()
    if suffix == ".md":
        return chunk_markdown(path, text)
    if suffix in {".h", ".hpp", ".cpp", ".cc", ".cxx"}:
        return chunk_cpp(path, text)
    if suffix == ".cyxgraph":
        return chunk_cyxgraph(path, text)
    return [make_chunk(path, "text", 1, len(text.splitlines()), path.name, text)]


def source_type_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".md":
        return "markdown"
    if suffix in {".h", ".hpp", ".cpp", ".cc", ".cxx"}:
        return "source"
    if suffix == ".cyxgraph":
        return "cyxgraph"
    return "text"


def file_metadata(path: Path) -> IndexedFile:
    text = read_text(path)
    encoded = text.encode("utf-8")
    return IndexedFile(
        path=repo_rel(path),
        source_type=source_type_for(path),
        content_hash=content_hash(text),
        size_bytes=len(encoded),
    )


def iter_initial_files(patterns: list[str]) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in REPO_ROOT.glob(pattern):
            if path.is_file() and path not in seen:
                found.append(path)
                seen.add(path)
    return sorted(found)


def build_index(config: dict) -> dict:
    chunks: list[Chunk] = []
    patterns = config["source_patterns"]
    files = iter_initial_files(patterns)
    for path in files:
        chunks.extend(chunk_file(path))
    indexed_files = [file_metadata(path) for path in files]

    return {
        "schema": SCHEMA_INDEX,
        "config_schema": config["schema"],
        "config_path": config["config_path"],
        "config_hash": config["config_hash"],
        "repo_root": str(REPO_ROOT),
        "source_patterns": patterns,
        "file_count": len(files),
        "chunk_count": len(chunks),
        "files": [asdict(item) for item in indexed_files],
        "chunks": [asdict(chunk) for chunk in chunks],
    }


def update_index(index: dict, config: dict) -> tuple[dict, dict[str, int]]:
    previous_files = index.get("files", [])
    if not isinstance(previous_files, list):
        previous_files = []
    previous_by_path = {item["path"]: item for item in previous_files if isinstance(item, dict) and "path" in item}

    discovered = [file_metadata(path) for path in iter_initial_files(config["source_patterns"])]
    discovered_by_path = {item.path: item for item in discovered}

    existing_chunks = index.get("chunks", [])
    if not isinstance(existing_chunks, list):
        existing_chunks = []
    existing_by_path: dict[str, list[dict]] = {}
    for chunk in existing_chunks:
        if not isinstance(chunk, dict):
            continue
        existing_by_path.setdefault(chunk.get("path", ""), []).append(chunk)

    updated_files: list[dict] = []
    updated_chunks: list[dict] = []
    stats = {"added": 0, "changed": 0, "unchanged": 0, "removed": 0}
    for item in discovered:
        rel = item.path
        prior = previous_by_path.get(rel)
        if prior and prior.get("content_hash") == item.content_hash:
            updated_files.append(asdict(item))
            updated_chunks.extend(existing_by_path.get(rel, []))
            stats["unchanged"] += 1
            continue

        path = REPO_ROOT / rel
        if prior:
            stats["changed"] += 1
        else:
            stats["added"] += 1
        updated_files.append(asdict(item))
        for chunk in chunk_file(path):
            updated_chunks.append(asdict(chunk))

    removed = len(previous_files) - len(updated_files)
    if removed > 0:
        stats["removed"] = removed

    return (
        {
            "schema": SCHEMA_INDEX,
            "config_schema": index.get("config_schema", config.get("schema", SCHEMA_CONFIG_UNKNOWN)),
            "config_path": str(index.get("config_path", config.get("config_path", ""))),
            "config_hash": config.get("config_hash", index.get("config_hash", "")),
            "repo_root": str(REPO_ROOT),
            "source_patterns": config["source_patterns"],
            "file_count": len(updated_files),
            "chunk_count": len(updated_chunks),
            "files": updated_files,
            "chunks": updated_chunks,
        },
        stats,
    )


def save_index(index: dict, path: Path) -> None:
    path.write_text(json.dumps(index, indent=2, ensure_ascii=True), encoding="utf-8")


def load_index(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config(path: Path, project_root: Path | None = None) -> dict:
    source = path if path.exists() else (
        LEGACY_DEFAULT_CONFIG if LEGACY_DEFAULT_CONFIG.exists() else None
    )
    if source is None:
        resolved_root = resolve_project_root(project_root, config_path=path)
        activate_project_root(resolved_root)
        return {
            "schema": SCHEMA_CONFIG_FALLBACK,
            "config_path": str(path),
            "config_hash": "",
            "project_root": str(resolved_root),
            "source_patterns": FALLBACK_PATTERNS,
            "saved_queries": FALLBACK_SAVED_QUERIES,
            "success_checks": FALLBACK_SUCCESS_CHECKS,
        }

    raw = source.read_text(encoding="utf-8")
    config = json.loads(raw)
    resolved_root = resolve_project_root(
        project_root,
        config_root=config.get("project_root"),
        config_path=source,
    )
    activate_project_root(resolved_root)
    return {
        "schema": config.get("schema", SCHEMA_CONFIG_UNKNOWN),
        "config_path": str(path),
        "config_hash": content_hash(raw) if source == path else "",
        "project_root": str(resolved_root),
        "source_patterns": config.get("source_patterns") or FALLBACK_PATTERNS,
        "saved_queries": config.get("saved_queries") or FALLBACK_SAVED_QUERIES,
        "success_checks": config.get("success_checks") or FALLBACK_SUCCESS_CHECKS,
    }


def tokenize(text: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in WORD_RE.findall(text):
        token = raw.lower()
        variants = [token, normalize_token(token)]
        if token.endswith("vectorizer"):
            variants.append(token.removesuffix("vectorizer"))
            variants.append(normalize_token(token.removesuffix("vectorizer")))
        for variant in variants:
            if variant and variant not in STOPWORDS and len(variant) > 1 and variant not in seen:
                out.append(variant)
                seen.add(variant)
    return out


def normalize_token(text: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "", text.lower())


def normalize_filter_values(values: list[str] | None) -> list[str]:
    return [value.strip().lower() for value in (values or []) if value and value.strip()]


def filters_from_args(args: argparse.Namespace) -> SearchFilters:
    return SearchFilters(
        source_types=normalize_filter_values(getattr(args, "source_type", None)),
        path_contains=normalize_filter_values(getattr(args, "path_contains", None)),
        title_contains=normalize_filter_values(getattr(args, "title_contains", None)),
        tags=normalize_filter_values(getattr(args, "tag", None)),
    )


def merge_filter_values(first: list[str], second: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in [*first, *second]:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def merge_filters(base: SearchFilters, extra: SearchFilters) -> SearchFilters:
    return SearchFilters(
        source_types=merge_filter_values(base.source_types, extra.source_types),
        path_contains=merge_filter_values(base.path_contains, extra.path_contains),
        title_contains=merge_filter_values(base.title_contains, extra.title_contains),
        tags=merge_filter_values(base.tags, extra.tags),
    )


def _parse_int(value: object, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _normalize_profile_key(query: str, filters: SearchFilters, mode: str) -> str:
    payload = {
        "query": " ".join(tokenize(query)),
        "mode": mode,
        "source_types": filters.source_types,
        "path_contains": filters.path_contains,
        "title_contains": filters.title_contains,
        "tags": filters.tags,
    }
    return hashlib.sha1(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
            "utf-8",
        )
    ).hexdigest()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def fallback_state_path(index_path: Path) -> Path:
    return index_path.with_name(f"{index_path.name}{FALLBACK_STATE_SUFFIX}")


def load_fallback_state(path: Path) -> dict:
    if not path.exists():
        return {
            "schema": SCHEMA_FALLBACK_STATE,
            "query_profiles": {},
            "index_builds": [],
            "packet_runs": [],
        }

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "schema": SCHEMA_FALLBACK_STATE,
            "query_profiles": {},
            "index_builds": [],
            "packet_runs": [],
        }

    if not isinstance(raw, dict):
        return {
            "schema": SCHEMA_FALLBACK_STATE,
            "query_profiles": {},
            "index_builds": [],
            "packet_runs": [],
        }

    raw.setdefault("schema", SCHEMA_FALLBACK_STATE)
    raw.setdefault("query_profiles", {})
    raw.setdefault("index_builds", [])
    raw.setdefault("packet_runs", [])
    return raw


def save_fallback_state(path: Path, state: dict) -> None:
    trimmed = {
        "schema": SCHEMA_FALLBACK_STATE,
        "query_profiles": state.get("query_profiles", {}),
        "index_builds": state.get("index_builds", []),
        "packet_runs": state.get("packet_runs", []),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trimmed, indent=2, ensure_ascii=True), encoding="utf-8")


def record_index_build_event(state_path: Path, duration_ms: int, index: dict) -> dict | None:
    if duration_ms <= 0:
        return None
    index_path = str(state_path)
    if index_path.endswith(FALLBACK_STATE_SUFFIX):
        index_path = index_path[: -len(FALLBACK_STATE_SUFFIX)]
    event = {
        "timestamp": _utcnow(),
        "duration_ms": duration_ms,
        "file_count": index.get("file_count", 0),
        "chunk_count": index.get("chunk_count", 0),
        "index_path": index_path,
    }
    state = load_fallback_state(state_path)
    builds = state.get("index_builds", [])
    builds.append(event)
    if len(builds) > FALLBACK_STATE_MAX_EVENTS:
        builds[:] = builds[-FALLBACK_STATE_MAX_EVENTS:]
    state["index_builds"] = builds
    save_fallback_state(state_path, state)
    return event


def _append_packet_run_event(state_path: Path, event: dict) -> dict | None:
    if not event:
        return None
    state = load_fallback_state(state_path)
    runs = state.get("packet_runs", [])
    runs.append(event)
    if len(runs) > FALLBACK_STATE_MAX_EVENTS:
        runs[:] = runs[-FALLBACK_STATE_MAX_EVENTS:]
    state["packet_runs"] = runs
    profiles = state.get("query_profiles", {})
    profile = event.get("query_profile", {})
    profile_count: int | None = None
    if profile and event.get("fallback_used"):
        key = str(profile.get("key", ""))
        entry = profiles.get(key)
        if not isinstance(entry, dict):
            entry = {
                "signature": profile.get("signature", ""),
                "count": 0,
                "first_seen": "",
                "last_seen": "",
            }
        entry["count"] = int(entry.get("count", 0)) + 1
        entry["last_seen"] = event.get("timestamp")
        if not entry.get("first_seen"):
            entry["first_seen"] = event.get("timestamp")
        profiles[key] = entry
        state["query_profiles"] = profiles
        profile_count = int(entry.get("count", 0))
        if profile_count >= 0:
            event["query_profile"]["count"] = profile_count
    save_fallback_state(state_path, state)
    return event


def make_fallback_usage_report(state: dict) -> dict:
    builds = [item for item in state.get("index_builds", []) if isinstance(item, dict)]
    packets = [item for item in state.get("packet_runs", []) if isinstance(item, dict)]
    fallback_packets = [item for item in packets if item.get("fallback_used")]
    last_build = builds[-1] if builds else {}
    last_packet = packets[-1] if packets else {}
    total_builds = len(builds)
    total_packets = len(packets)
    total_fallback_packets = len(fallback_packets)
    avg_build_ms = sum(int(item.get("duration_ms", 0)) for item in builds) / total_builds if total_builds else 0
    avg_packet_ms = sum(int(item.get("duration_ms", 0)) for item in packets) / total_packets if total_packets else 0
    avg_fallback_scanned = (
        sum(int(item.get("fallback_scanned_lines", 0)) for item in fallback_packets) / total_fallback_packets
        if total_fallback_packets
        else 0
    )
    top_profiles = sorted(
        (
            {"key": key, "count": int(value.get("count", 0)), "first_seen": str(value.get("first_seen", "")), "last_seen": str(value.get("last_seen", ""))}
            for key, value in (state.get("query_profiles", {}) or {}).items()
            if isinstance(value, dict)
        ),
        key=lambda item: item["count"],
        reverse=True,
    )[:10]
    return {
        "schema": SCHEMA_FALLBACK_USAGE_REPORT,
        "index_builds": total_builds,
        "packet_runs": total_packets,
        "fallback_packet_runs": total_fallback_packets,
        "index_build_avg_ms": round(avg_build_ms, 2),
        "packet_avg_ms": round(avg_packet_ms, 2),
        "fallback_scanned_lines_avg": round(avg_fallback_scanned, 2),
        "last_build": last_build,
        "last_packet": last_packet,
        "top_fallback_profiles": top_profiles,
    }


def _fallback_profile_warning(profile: dict | None, threshold: int) -> str | None:
    if not profile:
        return None
    count = int(profile.get("count", 0))
    if count < threshold:
        return None
    return (
        "Query profile crossed fallback budget: "
        f"fallback_used={count} >= threshold {threshold}. "
        "Consider indexing this scope or broadening filters."
    )


def _resolve_optional_path(raw: str | Path | None, *, config_path: Path | None = None) -> Path | None:
    if raw is None:
        return None
    candidate = Path(raw)
    if candidate.is_absolute() or config_path is None:
        return candidate
    return (config_path.parent / candidate).resolve()


def _coerce_memory_chunk(raw: dict, fallback_path: str, index: int) -> dict | None:
    if not isinstance(raw, dict):
        return None

    text = str(raw.get("text") or raw.get("snippet") or "").strip()
    if not text:
        return None

    path = str(raw.get("path") or f"{fallback_path}:{index}")
    title = str(raw.get("title") or raw.get("name") or Path(path).stem or "memory chunk")
    line_start = _parse_int(raw.get("line_start"), 1)
    line_end = _parse_int(raw.get("line_end"), line_start)
    if line_end < line_start:
        line_end = line_start

    source_type = str(raw.get("source_type") or "text").strip().lower() or "text"
    tags = normalize_filter_values(
        raw.get("tags")
        if isinstance(raw.get("tags"), list)
        else raw.get("tags") or [str(source_type), path.split("/", 1)[0] if "/" in path else "memory"]
    )

    return {
        "id": str(raw.get("id") or stable_id(path, title, line_start, text)),
        "source_type": source_type,
        "path": path,
        "line_start": line_start,
        "line_end": line_end,
        "title": title,
        "text": text,
        "content_hash": content_hash(text),
        "tags": sorted(set(tags)),
        "kind": str(raw.get("kind") or NON_REDISCOVERABLE_KIND),
        "schema": SCHEMA_NON_REDISCOVERABLE,
    }


def load_memory_chunks(raw_path: str | None, config_path: Path) -> list[dict]:
    if not raw_path:
        return []

    memory_path = _resolve_optional_path(raw_path, config_path=Path(config_path))
    if memory_path is None:
        return []
    if not memory_path.exists():
        raise FileNotFoundError(f"Memory source not found: {memory_path}")
    raw_text = read_text(memory_path).strip()
    if not raw_text:
        return []

    decoded: object
    try:
        decoded = json.loads(raw_text)
    except json.JSONDecodeError:
        decoded = None

    payloads: list[dict] = []
    if isinstance(decoded, list):
        payloads = [item for item in decoded if isinstance(item, dict)]
    elif isinstance(decoded, dict):
        payloads = [x for x in decoded.get("chunks", []) if isinstance(x, dict)]
        if not payloads:
            payloads = [x for x in decoded.get("items", []) if isinstance(x, dict)]
        if not payloads and decoded.get("schema") == SCHEMA_NON_REDISCOVERABLE and "text" in decoded:
            payloads = [decoded]
        if decoded.get("path") and decoded.get("text"):
            payloads = [decoded]
    if not payloads and decoded is None:
        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict):
                payloads.append(candidate)

    chunks: list[dict] = []
    fallback_path = str(memory_path)
    for index, payload in enumerate(payloads):
        chunk = _coerce_memory_chunk(payload, fallback_path, index)
        if chunk is not None:
            chunks.append(chunk)
    return chunks


def file_matches_filters_for_grep(path: Path, filters: SearchFilters | None) -> bool:
    if filters is None:
        return True

    source_type = source_type_for(path)
    path_text = str(path).replace("\\", "/").lower()
    title = path.name.lower()
    if filters.source_types and source_type not in filters.source_types:
        return False
    if filters.path_contains and not all(term in path_text for term in filters.path_contains):
        return False
    if filters.title_contains and not all(term in title for term in filters.title_contains):
        return False
    return True


def run_fallback_grep(
    query: str,
    config: dict,
    filters: SearchFilters | None,
    top: int,
    *,
    max_files: int = FALLBACK_GREP_MAX_FILES,
    context_lines: int = FALLBACK_GREP_CONTEXT_LINES,
    timeout_ms: int = FALLBACK_GREP_TIMEOUT_MS,
) -> dict:
    if top <= 0:
        return {"chunks": [], "meta": {"timed_out": False, "scanned_files": 0, "scanned_lines": 0}}

    search_terms = tokenize(query)
    if not search_terms:
        search_terms = [term for term in query.split() if term.strip()]
    if not search_terms:
        return {"chunks": [], "meta": {"timed_out": False, "scanned_files": 0, "scanned_lines": 0}}

    max_files = _parse_int(max_files, FALLBACK_GREP_MAX_FILES)
    max_files = max(1, max_files)
    context_lines = _parse_int(context_lines, FALLBACK_GREP_CONTEXT_LINES)
    context_lines = max(2, context_lines)
    timeout_ms = _parse_int(timeout_ms, FALLBACK_GREP_TIMEOUT_MS)
    timeout_ms = max(0, timeout_ms)

    deadline = monotonic() + (timeout_ms / 1000.0) if timeout_ms else None
    fallback_scanned_files = 0
    fallback_scanned_lines = 0
    timed_out = False
    half_window = max(1, context_lines // 2)

    lower_terms = [term.lower() for term in search_terms]
    hits: dict[tuple[str, int, int], dict] = {}
    file_index = 0
    for path in iter_initial_files(config["source_patterns"]):
        if file_index >= max_files:
            break
        file_index += 1
        if not file_matches_filters_for_grep(path, filters):
            continue
        if deadline is not None and monotonic() >= deadline:
            timed_out = True
            break
        fallback_scanned_files += 1
        try:
            lines = read_text(path).splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        fallback_scanned_lines += len(lines)
        if not lines:
            continue

        for line_no, line in enumerate(lines, start=1):
            if deadline is not None and monotonic() >= deadline:
                timed_out = True
                break
            line_lower = line.lower()
            if not any(term in line_lower for term in lower_terms):
                continue
            window_start = max(1, line_no - half_window)
            window_end = min(len(lines), line_no + half_window)
            chunk_text = "\n".join(lines[window_start - 1 : window_end]).strip()
            if not chunk_text:
                continue
            key = (repo_rel(path), window_start, window_end)
            if key in hits:
                continue
            chunk_id = stable_id(key[0], path.name, window_start, chunk_text)
            hits[key] = {
                "id": chunk_id,
                "source_type": source_type_for(path),
                "path": repo_rel(path),
                "line_start": window_start,
                "line_end": window_end,
                "title": f"{path.name}:{window_start}-{window_end}",
                "text": chunk_text,
                "content_hash": content_hash(chunk_text),
                "tags": [source_type_for(path), "fallback_grep"],
                "kind": REDISCOVERABLE_KIND,
            }
        if timed_out:
            break

    if not hits:
        return {
            "chunks": [],
            "meta": {
                "timed_out": timed_out,
                "scanned_files": fallback_scanned_files,
                "scanned_lines": fallback_scanned_lines,
            },
        }
    return {
        "chunks": search({"chunks": list(hits.values())}, query, top, filters),
        "meta": {
            "timed_out": timed_out,
            "scanned_files": fallback_scanned_files,
            "scanned_lines": fallback_scanned_lines,
            "timeout_ms": timeout_ms,
        },
    }


def normalize_preset(raw: dict) -> SavedQueryPreset:
    return SavedQueryPreset(
        name=str(raw.get("name") or "").strip(),
        description=str(raw.get("description") or "").strip(),
        query=str(raw.get("query") or "").strip(),
        filters=SearchFilters(
            source_types=normalize_filter_values(raw.get("source_types")),
            path_contains=normalize_filter_values(raw.get("path_contains")),
            title_contains=normalize_filter_values(raw.get("title_contains")),
            tags=normalize_filter_values(raw.get("tag") or raw.get("tags")),
        ),
    )


def preset_map(config: dict) -> dict[str, SavedQueryPreset]:
    presets: dict[str, SavedQueryPreset] = {}
    for raw in config.get("saved_queries", []):
        if not isinstance(raw, dict):
            continue
        preset = normalize_preset(raw)
        if preset.name:
            presets[preset.name] = preset
    return presets


def resolve_query_and_filters(
    config: dict,
    args: argparse.Namespace,
) -> tuple[str, SearchFilters, SavedQueryPreset | None]:
    presets = preset_map(config)
    preset_name = str(getattr(args, "preset", "") or "").strip()
    preset = presets.get(preset_name) if preset_name else None
    if preset_name and preset is None:
        available = ", ".join(sorted(presets))
        raise ValueError(f"Unknown preset: {preset_name}. Available presets: {available}")
    query = str(getattr(args, "query", "") or "").strip()
    if not query and preset is not None:
        query = preset.query
    if not query:
        raise ValueError("A query is required unless --preset provides one.")
    explicit_filters = filters_from_args(args)
    filters = merge_filters(preset.filters, explicit_filters) if preset else explicit_filters
    return query, filters, preset


def has_active_filters(filters: SearchFilters) -> bool:
    return bool(
        filters.source_types
        or filters.path_contains
        or filters.title_contains
        or filters.tags
    )


def chunk_matches_filters(chunk: dict, filters: SearchFilters) -> bool:
    source_type = str(chunk.get("source_type", "")).lower()
    path = str(chunk.get("path", "")).lower()
    title = str(chunk.get("title", "")).lower()
    tags = {str(tag).lower() for tag in chunk.get("tags", [])}

    if filters.source_types and source_type not in filters.source_types:
        return False
    if filters.path_contains and not all(term in path for term in filters.path_contains):
        return False
    if filters.title_contains and not all(term in title for term in filters.title_contains):
        return False
    if filters.tags and not all(tag in tags for tag in filters.tags):
        return False
    return True


def score_chunk(chunk: dict, query: str, query_terms: list[str]) -> int:
    text = chunk.get("text", "").lower()
    title = chunk.get("title", "").lower()
    path = chunk.get("path", "").lower()
    tags = " ".join(chunk.get("tags", [])).lower()
    query_lower = query.lower()
    text_norm = normalize_token(text)
    title_norm = normalize_token(title)
    path_norm = normalize_token(path)
    tags_norm = normalize_token(tags)

    score = 0
    score += SOURCE_TYPE_BOOST.get(chunk.get("source_type", ""), 0)
    broad_help_query = (
        len(query_terms) <= 4
        and (not query_terms or any(term in BROAD_HELP_TERMS for term in query_terms))
    )
    if broad_help_query:
        source_type = chunk.get("source_type", "")
        if source_type in {"markdown", "text"}:
            score += 120
        if "knowledge_seed" in path or "overview" in path or "readme" in path:
            score += 100
        if "usage" in path or "assistant" in path or "capabilities" in path:
            score += 40
    if query_lower and query_lower in text:
        score += 30
    if query_lower and query_lower in title:
        score += 40
    matched_terms = 0
    for term in query_terms:
        if not term:
            continue
        exact_weight = min(len(term), 16)
        term_norm = normalize_token(term)
        text_hits = min(max(text.count(term), text_norm.count(term_norm)), 3)
        title_hits = min(max(title.count(term), title_norm.count(term_norm)), 2)
        path_hits = min(max(path.count(term), path_norm.count(term_norm)), 2)
        tag_hits = min(max(tags.count(term), tags_norm.count(term_norm)), 2)
        if text_hits or title_hits or path_hits or tag_hits:
            matched_terms += 1
        score += text_hits * max(1, exact_weight // 4)
        score += title_hits * (10 + exact_weight)
        score += path_hits * (6 + exact_weight)
        score += tag_hits * (4 + exact_weight)
    if matched_terms:
        score += matched_terms * matched_terms * 3
        if matched_terms == len(query_terms):
            score += 30
        elif matched_terms >= max(3, len(query_terms) - 1):
            score += 15
    return score


def search(index: dict, query: str, top: int, filters: SearchFilters | None = None) -> list[dict]:
    query_terms = tokenize(query)
    filters = filters or SearchFilters([], [], [], [])
    results: list[dict] = []
    for chunk in index.get("chunks", []):
        if not chunk_matches_filters(chunk, filters):
            continue
        score = score_chunk(chunk, query, query_terms)
        if score > 0:
            results.append({"score": score, "chunk": chunk})
    results.sort(
        key=lambda item: (
            -item["score"],
            item["chunk"].get("path", ""),
            item["chunk"].get("line_start", 0),
        )
    )
    return results[:top]


def preview_text(text: str, query: str, limit: int = 500) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact

    lower = compact.lower()
    best = -1
    for term in sorted(tokenize(query), key=len, reverse=True):
        idx = lower.find(term.lower())
        if idx >= 0:
            best = idx
            break

    if best < 0:
        return compact[:limit]

    start = max(0, best - limit // 3)
    end = min(len(compact), start + limit)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(compact) else ""
    return f"{prefix}{compact[start:end]}{suffix}"


def print_results(results: list[dict], query: str) -> None:
    if not results:
        print("No matches.")
        return

    for rank, item in enumerate(results, start=1):
        chunk = item["chunk"]
        citation = f"{chunk['path']}:{chunk['line_start']}-{chunk['line_end']}"
        preview = preview_text(chunk["text"], query, 280)
        print(f"{rank}. score={item['score']} {citation}")
        print(f"   title: {chunk['title']}")
        print(f"   type: {chunk['source_type']}")
        print(f"   preview: {preview}")


def summarize_results_by_file(results: list[dict], top_files: int) -> list[dict]:
    summary: dict[str, dict] = {}
    for item in results:
        chunk = item["chunk"]
        path = chunk["path"]
        existing = summary.get(path)
        if existing is None:
            summary[path] = {
                "path": path,
                "source_type": chunk.get("source_type", ""),
                "best_score": item["score"],
                "hit_count": 1,
                "best_title": chunk.get("title", ""),
                "line_start": chunk.get("line_start", 0),
                "line_end": chunk.get("line_end", 0),
            }
            continue
        existing["hit_count"] += 1
        if item["score"] > existing["best_score"]:
            existing["best_score"] = item["score"]
            existing["best_title"] = chunk.get("title", "")
            existing["line_start"] = chunk.get("line_start", 0)
            existing["line_end"] = chunk.get("line_end", 0)
            existing["source_type"] = chunk.get("source_type", "")
    ordered = sorted(
        summary.values(),
        key=lambda item: (-item["best_score"], item["path"]),
    )
    return ordered[:top_files]


def make_search_report(
    index: dict,
    query: str,
    top: int,
    top_files: int,
    include_full_text: bool,
    filters: SearchFilters | None = None,
    preset_name: str = "",
) -> dict:
    filters = filters or SearchFilters([], [], [], [])
    results = search(index, query, top, filters)
    query_terms = tokenize(query)
    items = []
    for rank, item in enumerate(results, start=1):
        chunk = item["chunk"]
        record = {
            "rank": rank,
            "score": item["score"],
            "citation": citation_for(chunk),
            "preview": preview_text(chunk["text"], query, 280),
        }
        if include_full_text:
            record["text"] = chunk["text"]
        items.append(record)
    return {
        "schema": SCHEMA_SEARCH_REPORT,
        "query": query,
        "query_terms": query_terms,
        "preset": preset_name,
        "filters": {
            "source_types": filters.source_types,
            "path_contains": filters.path_contains,
            "title_contains": filters.title_contains,
            "tags": filters.tags,
        },
        "index": {
            "path": index.get("config_path", ""),
            "file_count": index.get("file_count", 0),
            "chunk_count": index.get("chunk_count", 0),
        },
        "result_count": len(results),
        "file_summary": summarize_results_by_file(results, top_files),
        "results": items,
    }


def print_search_report_text(report: dict) -> None:
    print(f"Query: {report['query']}")
    if report.get("preset"):
        print(f"Preset: {report['preset']}")
    terms = ", ".join(report.get("query_terms", [])) or "(none)"
    print(f"Query terms: {terms}")
    filters = report.get("filters", {})
    if any(filters.get(key) for key in ("source_types", "path_contains", "title_contains", "tags")):
        print("Filters:")
        if filters.get("source_types"):
            print(f"  source_types: {', '.join(filters['source_types'])}")
        if filters.get("path_contains"):
            print(f"  path_contains: {', '.join(filters['path_contains'])}")
        if filters.get("title_contains"):
            print(f"  title_contains: {', '.join(filters['title_contains'])}")
        if filters.get("tags"):
            print(f"  tags: {', '.join(filters['tags'])}")
    index_meta = report.get("index", {})
    print(
        "Index: "
        f"{index_meta.get('file_count', 0)} files, "
        f"{index_meta.get('chunk_count', 0)} chunks"
    )

    file_summary = report.get("file_summary", [])
    if file_summary:
        print("\nTop files:")
        for item in file_summary:
            citation = f"{item['path']}:{item['line_start']}-{item['line_end']}"
            print(
                f"- score={item['best_score']} hits={item['hit_count']} "
                f"{citation}"
            )
            print(f"  title: {item['best_title']}")
            print(f"  type: {item['source_type']}")

    results = report.get("results", [])
    if not results:
        print("\nNo matches.")
        return

    print("\nTop chunks:")
    for item in results:
        citation = item["citation"]
        line_ref = f"{citation['line_start']}-{citation['line_end']}"
        print(f"{item['rank']}. score={item['score']} {citation['path']}:{line_ref}")
        print(f"   title: {citation['title']}")
        print(f"   type: {citation['source_type']}")
        print(f"   preview: {item['preview']}")
        if "text" in item:
            print("   text:")
            for line in str(item["text"]).splitlines():
                print(f"     {line}")


def citation_for(chunk: dict) -> dict:
    return {
        "path": chunk["path"],
        "line_start": chunk["line_start"],
        "line_end": chunk["line_end"],
        "title": chunk["title"],
        "source_type": chunk["source_type"],
        "kind": chunk.get("kind", REDISCOVERABLE_KIND),
    }


def make_answer_packet(
    index: dict,
    query: str,
    top: int,
    filters: SearchFilters | None = None,
    *,
    packet_mode: str = DEFAULT_PACKET_MODE,
    memory_chunks: list[dict] | None = None,
    fallback_grep: list[dict] | None = None,
    fallback_meta: dict | None = None,
    fallback_budget_warning: str | None = None,
) -> dict:
    filters = filters or SearchFilters([], [], [], [])
    fallback_meta = fallback_meta or {}
    index_chunks = index.get("chunks", [])
    search_inputs = {
        "chunks": [
            *index_chunks,
            *(memory_chunks or []),
        ]
    }
    primary_results = search(search_inputs, query, top, filters)

    evidence = []
    seen: set[tuple[str, int, int, str]] = set()
    for item in primary_results:
        chunk = item["chunk"]
        marker = (
            str(chunk.get("path", "")),
            int(chunk.get("line_start", -1)),
            int(chunk.get("line_end", -1)),
            str(chunk.get("kind", REDISCOVERABLE_KIND)),
        )
        if marker in seen:
            continue
        seen.add(marker)
        evidence.append(
            {
                "rank": len(evidence) + 1,
                "score": item["score"],
                "citation": citation_for(chunk),
                "text": chunk["text"],
            }
        )

    fallback_chunks = fallback_grep or []
    fallback_used = packet_mode in {"fetch-first", "memory-first"} and not evidence
    if fallback_chunks and len(evidence) < top:
        for item in fallback_chunks:
            chunk = item["chunk"]
            marker = (
                str(chunk.get("path", "")),
                int(chunk.get("line_start", -1)),
                int(chunk.get("line_end", -1)),
                str(chunk.get("kind", REDISCOVERABLE_KIND)),
            )
            if marker in seen:
                continue
            seen.add(marker)
            evidence.append(
                {
                    "rank": len(evidence) + 1,
                    "score": item["score"],
                    "citation": citation_for(chunk),
                    "text": chunk["text"],
                }
            )
            fallback_used = True
            if len(evidence) >= top:
                break
    evidence = evidence[:top]

    missing_notes = []
    if not evidence:
        missing_notes.append("No matching local evidence was found in the retrieval index.")
    if evidence and len(evidence) < top:
        missing_notes.append("Fewer evidence chunks were available than requested.")
    if fallback_used and not fallback_chunks:
        missing_notes.append("No fallback chunks were available to enrich sparse results.")
    if fallback_meta.get("timed_out"):
        missing_notes.append("Fallback scan reached timeout; results may be incomplete.")

    source_miss = len(evidence) == 0
    strategy = packet_mode_to_strategy(packet_mode)
    index_chunks_scanned = len(search_inputs["chunks"])
    fallback_chunks_scanned = len(fallback_chunks) if fallback_used else 0
    fallback_scanned_lines = int(fallback_meta.get("scanned_lines", 0))
    fallback_scanned_files = int(fallback_meta.get("scanned_files", 0))
    fallback_timed_out = bool(fallback_meta.get("timed_out", False))
    fallback_budget_note = str(fallback_budget_warning or "").strip()

    tradeoff_rationale = [
        "memory-first: include non-rediscoverable memory chunks" if memory_chunks else "no memory source merged",
        f"index {'used' if index_chunks_scanned else 'empty/disabled'} for primary search",
        "fallback grep executed" if fallback_used else "fallback grep not used",
    ]
    if fallback_timed_out:
        tradeoff_rationale.append("fallback scan timed out and was bounded by timeout_ms")
    if fallback_budget_note:
        tradeoff_rationale.append(fallback_budget_note)

    return {
        "schema": SCHEMA_ANSWER_PACKET,
        "strategy": strategy,
        "source_miss": source_miss,
        "fallback_used": fallback_used,
        "question": query,
        "preset": "",
        "filters": {
            "source_types": filters.source_types,
            "path_contains": filters.path_contains,
            "title_contains": filters.title_contains,
            "tags": filters.tags,
        },
        "sources": {
            "index_chunks": len(index_chunks),
            "memory_chunks": len(memory_chunks or []),
            "fallback_chunks": len(fallback_chunks),
        },
        "metrics": {
            "evidence_hits": len(evidence),
            "index_chunks_scanned": index_chunks_scanned,
            "fallback_chunks_scanned": fallback_chunks_scanned,
            "fallback_scanned_lines": fallback_scanned_lines,
            "fallback_scanned_files": fallback_scanned_files,
        },
        "fallback_timed_out": fallback_timed_out,
        "tradeoff_rationale": tradeoff_rationale,
        "tradeoff_warning": fallback_budget_note,
        "answer_contract": {
            "mode": "retrieval_only",
            "model_runtime": "not_used",
            "rules": [
                "answer only from cited evidence",
                "separate fact from inference",
                "state when evidence is missing",
                "do not invent behavior claims not supported by evidence",
            ],
        },
        "evidence": evidence,
        "missing_evidence_notes": missing_notes,
    }


def print_answer_packet_markdown(packet: dict) -> None:
    print(f"# Answer Packet\n")
    print(f"Question: {packet['question']}\n")
    if packet.get("preset"):
        print(f"Preset: {packet['preset']}\n")
    print(f"Mode: {packet.get('strategy', 'indexed-retrieval')}")
    print(f"Source miss: {str(packet.get('source_miss', False)).lower()}")
    print(f"Fallback used: {str(packet.get('fallback_used', False)).lower()}")
    print("Model runtime: not_used\n")
    metrics = packet.get("metrics", {})
    if metrics:
        print("## Metrics")
        print(f"- evidence_hits: {metrics.get('evidence_hits', 0)}")
        print(f"- index_chunks_scanned: {metrics.get('index_chunks_scanned', 0)}")
        print(f"- fallback_chunks_scanned: {metrics.get('fallback_chunks_scanned', 0)}")
        if metrics.get("fallback_scanned_files") is not None:
            print(f"- fallback_scanned_files: {metrics.get('fallback_scanned_files', 0)}")
        if metrics.get("fallback_scanned_lines") is not None:
            print(f"- fallback_scanned_lines: {metrics.get('fallback_scanned_lines', 0)}")
        if packet.get("fallback_timed_out"):
            print(f"- fallback_timed_out: {str(packet.get('fallback_timed_out', False)).lower()}")
        print("")
    filters = packet.get("filters", {})
    if any(filters.get(key) for key in ("source_types", "path_contains", "title_contains", "tags")):
        print("Filters:")
        if filters.get("source_types"):
            print(f"- source_types: {', '.join(filters['source_types'])}")
        if filters.get("path_contains"):
            print(f"- path_contains: {', '.join(filters['path_contains'])}")
        if filters.get("title_contains"):
            print(f"- title_contains: {', '.join(filters['title_contains'])}")
        if filters.get("tags"):
            print(f"- tags: {', '.join(filters['tags'])}")
        print("")

    evidence = packet.get("evidence", [])
    if not evidence:
        print("No evidence found.")
    else:
        print("## Evidence")
        for item in evidence:
            citation = item["citation"]
            line_ref = f"{citation['line_start']}-{citation['line_end']}"
            preview = preview_text(item["text"], packet["question"], 500)
            print(f"{item['rank']}. score={item['score']} {citation['path']}:{line_ref}")
            print(f"   title: {citation['title']}")
            print(f"   type: {citation['source_type']}")
            print(f"   kind: {citation.get('kind', 'rediscoverable')}")
            print(f"   preview: {preview}")

    rationale = packet.get("tradeoff_rationale", [])
    if rationale:
        print("\n## Tradeoff rationale")
        for item in rationale:
            print(f"- {item}")
    fallback_warning = packet.get("tradeoff_warning")
    if fallback_warning:
        print("\n## Fallback Warning")
        print(f"- {fallback_warning}")

    notes = packet.get("missing_evidence_notes", [])
    if notes:
        print("\n## Missing Evidence Notes")
        for note in notes:
            print(f"- {note}")


def cmd_check(args: argparse.Namespace) -> int:
    if not args.index.exists():
        print(f"Index not found: {args.index}")
        print("Run build first.")
        return 2

    index = load_index(args.index)
    config = load_config(args.config, args.project_root)
    failed = 0
    for check in config["success_checks"]:
        results = search(index, check["query"], top=1)
        if not results:
            print(f"FAIL: {check['query']}")
            print("  no results")
            failed += 1
            continue

        chunk = results[0]["chunk"]
        path_ok = chunk["path"] == check["expected_path"]
        title_ok = chunk["title"] == check["expected_title"]
        status = "PASS" if path_ok and title_ok else "FAIL"
        print(f"{status}: {check['query']}")
        print(f"  got:      {chunk['path']} :: {chunk['title']}")
        print(f"  expected: {check['expected_path']} :: {check['expected_title']}")
        if not (path_ok and title_ok):
            failed += 1

    if failed:
        print(f"{failed} Phase 1A retrieval check(s) failed.")
        return 1

    print("All Phase 1A retrieval checks passed.")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    if not args.index.exists():
        print(f"Index not found: {args.index}")
        print("Run build first.")
        return 2

    index = load_index(args.index)
    config = load_config(args.config, args.project_root)
    indexed_by_path = {
        item["path"]: item
        for item in index.get("files", [])
        if isinstance(item, dict) and "path" in item
    }
    current_files = [file_metadata(path) for path in iter_initial_files(config["source_patterns"])]
    current_by_path = {item.path: item for item in current_files}

    changed: list[str] = []
    added: list[str] = []
    removed: list[str] = []
    config_changed = index.get("config_hash") != config.get("config_hash")

    for path, current in current_by_path.items():
        indexed = indexed_by_path.get(path)
        if indexed is None:
            added.append(path)
            continue
        if indexed.get("content_hash") != current.content_hash:
            changed.append(path)

    for path in indexed_by_path:
        if path not in current_by_path:
            removed.append(path)

    print(f"Index: {args.index}")
    print(f"Config: {args.config}")
    print(f"Indexed files: {len(indexed_by_path)}")
    print(f"Current files: {len(current_by_path)}")
    print(f"Indexed chunks: {index.get('chunk_count', 'unknown')}")

    if not changed and not added and not removed and not config_changed:
        print("Status: fresh")
        return 0

    print("Status: stale")
    if config_changed:
        print("config changed:")
        print(f"  indexed: {index.get('config_path', '')}")
        print(f"  current: {config.get('config_path', '')}")
    for label, paths in (("changed", changed), ("added", added), ("removed", removed)):
        if paths:
            print(f"{label}:")
            for path in sorted(paths):
                print(f"  {path}")
    return 1


def cmd_build(args: argparse.Namespace) -> int:
    start = monotonic()
    config = load_config(args.config, args.project_root)
    index: dict
    stats: dict[str, int] | None = None
    if args.incremental and args.index.exists():
        try:
            index, stats = update_index(load_index(args.index), config)
        except (json.JSONDecodeError, OSError):
            index = build_index(config)
    else:
        index = build_index(config)

    save_index(index, args.index)
    elapsed_ms = int((monotonic() - start) * 1000)
    state_path = fallback_state_path(args.index)
    record_index_build_event(state_path, elapsed_ms, index)

    if stats:
        print(
            f"Updated {args.index} with {index['file_count']} files and "
            f"{index['chunk_count']} chunks."
        )
        print(
            f"  added={stats['added']} changed={stats['changed']} "
            f"unchanged={stats['unchanged']} removed={stats['removed']}"
        )
        return 0

    print(
        f"Wrote {args.index} with {index['file_count']} files and "
        f"{index['chunk_count']} chunks."
    )
    return 0


def cmd_presets(args: argparse.Namespace) -> int:
    config = load_config(args.config, args.project_root)
    presets = preset_map(config)
    ordered = [presets[name] for name in sorted(presets)]
    if args.json:
        payload = {
            "schema": SCHEMA_SAVED_QUERIES,
            "preset_count": len(ordered),
            "presets": [
                {
                    "name": preset.name,
                    "description": preset.description,
                    "query": preset.query,
                    "filters": {
                        "source_types": preset.filters.source_types,
                        "path_contains": preset.filters.path_contains,
                        "title_contains": preset.filters.title_contains,
                        "tags": preset.filters.tags,
                    },
                }
                for preset in ordered
            ],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 0
    if not ordered:
        print("No saved query presets.")
        return 0
    print("Saved query presets:")
    for preset in ordered:
        print(f"- {preset.name}")
        print(f"  description: {preset.description or '(none)'}")
        print(f"  query: {preset.query or '(none)'}")
        if has_active_filters(preset.filters):
            print("  filters:")
            if preset.filters.source_types:
                print(f"    source_types: {', '.join(preset.filters.source_types)}")
            if preset.filters.path_contains:
                print(f"    path_contains: {', '.join(preset.filters.path_contains)}")
            if preset.filters.title_contains:
                print(f"    title_contains: {', '.join(preset.filters.title_contains)}")
            if preset.filters.tags:
                print(f"    tags: {', '.join(preset.filters.tags)}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    if not args.index.exists():
        print(f"Index not found: {args.index}")
        print("Run build first.")
        return 2
    index = load_index(args.index)
    config = load_config(args.config, args.project_root)
    try:
        query, filters, preset = resolve_query_and_filters(config, args)
    except ValueError as exc:
        print(exc)
        return 2
    report = make_search_report(
        index,
        query,
        args.top,
        args.top_files,
        args.include_full_text,
        filters,
        preset.name if preset else "",
    )
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        print_search_report_text(report)
    return 0


def cmd_fallback_report(args: argparse.Namespace) -> int:
    state_path = fallback_state_path(args.index)
    state = load_fallback_state(state_path)
    report = make_fallback_usage_report(state)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return 0

    if report["index_builds"] == 0 and report["packet_runs"] == 0:
        print(f"No fallback usage data yet. Build and run packet queries first.")
        print(f"Expected state file: {state_path}")
        return 0

    print("Fallback usage report")
    print(f"Index builds: {report['index_builds']}")
    print(f"Packet runs: {report['packet_runs']}")
    print(f"Fallback packet runs: {report['fallback_packet_runs']}")
    print(f"Avg index build ms: {report['index_build_avg_ms']}")
    print(f"Avg packet ms: {report['packet_avg_ms']}")
    print(f"Avg fallback scanned lines: {report['fallback_scanned_lines_avg']}")

    last_build = report.get("last_build", {})
    if last_build:
        print(f"Last build: {last_build.get('index_path', 'n/a')} "
              f"{last_build.get('file_count', 0)} files, "
              f"{last_build.get('chunk_count', 0)} chunks, "
              f"{last_build.get('duration_ms', 0)}ms")

    top_profiles = report.get("top_fallback_profiles", [])
    if top_profiles:
        print("Top fallback profiles:")
        for item in top_profiles[:10]:
            print(
                f"- {item['count']}x {item['key']} "
                f"({item.get('first_seen', '')} .. {item.get('last_seen', '')})"
            )
    return 0


def cmd_packet(args: argparse.Namespace) -> int:
    start = monotonic()
    if args.no_index and args.mode == "packet-only":
        print("packet-only mode requires an index. Use --mode fetch-first or memory-first with --no-index.")
        return 2

    if args.memory_only and not args.memory_path:
        print("--memory-only requires --memory-path.")
        return 2

    if args.memory_only and args.mode != "memory-first":
        print("--memory-only currently pairs with --mode memory-first.")
        return 2

    if not args.index.exists() and not args.no_index:
        print(f"Index not found: {args.index}")
        print("Run build first.")
        return 2
    if args.no_index or args.memory_only:
        index = {"config_path": str(args.index), "file_count": 0, "chunk_count": 0, "chunks": []}
    else:
        index = load_index(args.index)

    config = load_config(args.config, args.project_root)
    try:
        query, filters, preset = resolve_query_and_filters(config, args)
    except ValueError as exc:
        print(exc)
        return 2

    memory_chunks: list[dict] = []
    if args.memory_path and args.mode == "memory-first":
        try:
            memory_chunks = load_memory_chunks(args.memory_path, Path(config["config_path"]))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"Could not load memory source: {exc}")
            return 2

    if args.no_index and not args.memory_only and not args.memory_path and args.mode == "memory-first":
        print("memory-first mode is active but no memory source was provided.")

    fallback_chunks: list[dict] = []
    fallback_meta: dict = {}
    if args.fallback_grep:
        try:
            fallback_result = run_fallback_grep(
                query,
                config,
                filters,
                args.top,
                max_files=args.fallback_max_files,
                context_lines=args.fallback_context_lines,
                timeout_ms=args.fallback_timeout_ms,
            )
            fallback_meta = (
                fallback_result.get("meta", {}) if isinstance(fallback_result, dict) else {}
            )
            candidate_chunks = fallback_result.get("chunks", []) if isinstance(fallback_result, dict) else []
            if isinstance(candidate_chunks, list):
                fallback_chunks = candidate_chunks
        except Exception as exc:  # defensive: fallback is optional
            print(f"Fallback grep failed: {exc}")
            fallback_chunks = []

    packet = make_answer_packet(
        index,
        query,
        args.top,
        filters,
        packet_mode=args.mode,
        memory_chunks=memory_chunks,
        fallback_grep=fallback_chunks,
        fallback_meta=fallback_meta,
    )
    packet["preset"] = preset.name if preset else ""
    profile_key = _normalize_profile_key(query, filters, args.mode)
    profile = {"key": profile_key, "signature": query}
    packet_duration_ms = int((monotonic() - start) * 1000)
    run_event = _append_packet_run_event(
        fallback_state_path(args.index),
        {
            "timestamp": _utcnow(),
            "duration_ms": packet_duration_ms,
            "fallback_scanned_lines": packet.get("metrics", {}).get("fallback_scanned_lines", 0),
            "fallback_scanned_files": packet.get("metrics", {}).get("fallback_scanned_files", 0),
            "mode": args.mode,
            "top": args.top,
            "top_used": len(packet.get("evidence", [])),
            "no_index": args.no_index,
            "memory_only": args.memory_only,
            "fallback_grep": args.fallback_grep,
            "query_profile": profile,
            "query": query,
            "preset": preset.name if preset else "",
            "source_miss": packet.get("source_miss", False),
            "fallback_used": packet.get("fallback_used", False),
            "metrics": packet.get("metrics", {}),
        },
    )
    budget_warning = _fallback_profile_warning(
        run_event.get("query_profile") if isinstance(run_event, dict) else None,
        _parse_int(args.fallback_budget_warn_threshold, FALLBACK_BUDGET_WARNING_THRESHOLD),
    )
    if budget_warning:
        packet["tradeoff_warning"] = budget_warning
        if budget_warning not in packet.get("tradeoff_rationale", []):
            packet["tradeoff_rationale"].append(budget_warning)
    if args.json:
        print(json.dumps(packet, indent=2, ensure_ascii=True))
    else:
        print_answer_packet_markdown(packet)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Open RAG Phase 1A retrieval")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="explicit project root for source discovery (defaults to config or script directory)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build_parser = sub.add_parser("build", help="rebuild the local JSON index")
    build_parser.add_argument(
        "--incremental",
        action="store_true",
        help="reuse unchanged file chunks when index already exists",
    )
    build_parser.set_defaults(func=cmd_build)

    sub.add_parser("check", help="run Phase 1A success checks").set_defaults(func=cmd_check)

    sub.add_parser("status", help="check whether indexed files changed").set_defaults(func=cmd_status)

    presets_parser = sub.add_parser("presets", help="list saved query presets")
    presets_parser.add_argument("--json", action="store_true")
    presets_parser.set_defaults(func=cmd_presets)

    search_parser = sub.add_parser("search", help="search the local JSON index")
    search_parser.add_argument("query", nargs="?")
    search_parser.add_argument("--preset")
    search_parser.add_argument("--top", type=int, default=5)
    search_parser.add_argument("--top-files", type=int, default=3)
    search_parser.add_argument("--include-full-text", action="store_true")
    search_parser.add_argument("--json", action="store_true", help="emit a structured search report")
    search_parser.add_argument("--source-type", action="append", choices=["source", "markdown", "cyxgraph", "cyxgraph_node", "cyxgraph_links", "text"])
    search_parser.add_argument("--path-contains", action="append")
    search_parser.add_argument("--title-contains", action="append")
    search_parser.add_argument("--tag", action="append")
    search_parser.set_defaults(func=cmd_search)

    packet_parser = sub.add_parser("packet", help="build a retrieval-only answer packet")
    packet_parser.add_argument("query", nargs="?")
    packet_parser.add_argument("--preset")
    packet_parser.add_argument("--top", type=int, default=5)
    packet_parser.add_argument(
        "--mode",
        default=DEFAULT_PACKET_MODE,
        choices=sorted(PACKET_MODES),
        help="retrieval strategy: packet-only, fetch-first, or memory-first",
    )
    packet_parser.add_argument(
        "--no-index",
        action="store_true",
        help="construct a packet without index fallback (requires --mode fetch-first|memory-first)",
    )
    packet_parser.add_argument("--memory-path", type=str, help="path to non-rediscoverable memory source")
    packet_parser.add_argument(
        "--memory-only",
        action="store_true",
        help="search only the supplied memory source (requires --memory-path and --memory-first)",
    )
    packet_parser.add_argument(
        "--fallback-grep",
        action="store_true",
        help="when packet evidence is sparse, run local fallback grep scanning source files",
    )
    packet_parser.add_argument(
        "--fallback-max-files",
        type=int,
        default=FALLBACK_GREP_MAX_FILES,
        help="limit fallback grep to at most this many source files (default: 200)",
    )
    packet_parser.add_argument(
        "--fallback-context-lines",
        type=int,
        default=FALLBACK_GREP_CONTEXT_LINES,
        help="number of lines per fallback grep chunk window (default: 10)",
    )
    packet_parser.add_argument(
        "--fallback-timeout-ms",
        type=int,
        default=FALLBACK_GREP_TIMEOUT_MS,
        help="bounded fallback scan time in milliseconds (default: 1500)",
    )
    packet_parser.add_argument(
        "--fallback-budget-warn-threshold",
        type=int,
        default=FALLBACK_BUDGET_WARNING_THRESHOLD,
        help="warn when one query profile uses fallback this many times",
    )
    packet_parser.add_argument("--json", action="store_true", help="emit packet as JSON")
    packet_parser.add_argument("--source-type", action="append", choices=["source", "markdown", "cyxgraph", "cyxgraph_node", "cyxgraph_links", "text"])
    packet_parser.add_argument("--path-contains", action="append")
    packet_parser.add_argument("--title-contains", action="append")
    packet_parser.add_argument("--tag", action="append")
    packet_parser.set_defaults(func=cmd_packet)

    fallback_report_parser = sub.add_parser("fallback-report", help="show fallback/index telemetry")
    fallback_report_parser.add_argument("--json", action="store_true", help="emit report JSON")
    fallback_report_parser.set_defaults(func=cmd_fallback_report)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
