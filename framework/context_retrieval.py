"""Narrow local-first retrieval over inspected RepomapGenerator surface."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# Inspection gate: verify RepomapGenerator is importable and has the expected API
from framework.codebase_repomap import RepomapGenerator, RepomapEntry

assert callable(RepomapGenerator), "RepomapGenerator must be callable"
assert hasattr(RepomapGenerator, "scan_repository"), "RepomapGenerator must have scan_repository"


@dataclass(frozen=True)
class RetrievalQuery:
    query: str
    top_k: int = 5
    include_snippets: bool = True


@dataclass(frozen=True)
class RetrievedFile:
    path: str
    score: float
    symbol_matches: tuple = ()
    snippet: str = ""


@dataclass
class RetrievalResult:
    query: str
    files: List[RetrievedFile] = field(default_factory=list)
    snippet: str = ""


def retrieve_context(
    query: RetrievalQuery,
    source_root: Path,
) -> RetrievalResult:
    source_root = Path(source_root)
    if not source_root.is_dir():
        return RetrievalResult(query=query.query)

    try:
        gen = RepomapGenerator(source_root)
        entries = gen.scan_repository(
            include_patterns=["**/*.py"],
            max_files=500,
        )
    except Exception:
        return RetrievalResult(query=query.query)

    tokens = _tokenize(query.query)
    if not tokens:
        return RetrievalResult(query=query.query)

    scored: List[tuple] = []
    for rel_path, entry in entries.items():
        score, matches = _score_entry(entry, tokens)
        if score > 0:
            snippet = _make_snippet(entry, matches) if query.include_snippets else ""
            scored.append((score, rel_path, matches, snippet))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: query.top_k]

    files = [
        RetrievedFile(
            path=rel_path,
            score=score,
            symbol_matches=tuple(matches),
            snippet=snippet,
        )
        for score, rel_path, matches, snippet in top
    ]

    combined_snippet = "\n\n".join(f.snippet for f in files if f.snippet)
    return RetrievalResult(query=query.query, files=files, snippet=combined_snippet)


def retrieve_file_content(path: str, source_root: Path) -> str:
    target = Path(source_root) / path
    if not target.is_file():
        try:
            target = Path(path)
            if not target.is_file():
                return ""
        except Exception:
            return ""
    try:
        return target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _tokenize(query: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", query)
    return [t.lower() for t in tokens if len(t) >= 2]


def _score_entry(entry: RepomapEntry, tokens: List[str]) -> tuple:
    path_lower = entry.path.lower()
    matches: List[str] = []
    score = 0.0

    for token in tokens:
        if token in path_lower:
            score += 0.5

    for sym in entry.symbols:
        sym_lower = sym.name.lower()
        for token in tokens:
            if token in sym_lower:
                score += 1.0
                if sym.name not in matches:
                    matches.append(sym.name)
                break

    if matches:
        score += len(matches) * 0.1

    return score, matches


def _make_snippet(entry: RepomapEntry, matches: List[str]) -> str:
    if not matches:
        return ""
    lines = [f"# {entry.path}"]
    for sym in entry.symbols:
        if sym.name in matches:
            kind = sym.kind
            lines.append(f"  {kind} {sym.name}  (line {sym.line})")
    return "\n".join(lines)


__all__ = [
    "RetrievalQuery",
    "RetrievedFile",
    "RetrievalResult",
    "retrieve_context",
    "retrieve_file_content",
]
