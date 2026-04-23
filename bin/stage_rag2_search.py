#!/usr/bin/env python3
"""Stage RAG-2 hybrid retriever for Stage-4 planning.

Compared to Stage RAG-1 this helper:
- indexes a broader set of surfaces (bin/, shell/, docs/, src/, tests/, framework/, promotion/, Makefile)
- uses larger adaptive chunks (default 48 lines with 24-line overlap)
- augments lexical BM25 scores with light-weight structural cues (nearest
  function/task labels, shebang blocks, or section headers)
- optionally emits JSON output so higher level managers can consume the ranked
  anchors directly.

The intent is to provide richer multi-line context ahead of Stage-4 probes
without bypassing micro-lane limits. Retrieval remains planning-only.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["bin", "shell", "docs", "src", "tests", "framework", "promotion", "Makefile"]
EXCLUDED_DIRS = {".git", "artifacts", "tmp", "temp", "generated", "node_modules", "__pycache__"}

_TOKENIZER = re.compile(r"[a-z0-9_]+")
_FUNCTION_PATTERN = re.compile(r"^(?:function\s+)?([A-Za-z0-9_./-]+)\s*\(\)\s*\{?$")
_SECTION_PATTERN = re.compile(r"^#\s*(.+)")

@dataclass
class Chunk:
    path: Path
    start_line: int
    end_line: int
    text: str
    tokens: Counter
    symbol: str | None = None

    @property
    def length(self) -> int:
        return sum(self.tokens.values()) or 1


def is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            sample = fh.read(1024)
            if b"\0" in sample:
                return True
            return False
    except OSError:
        return True


def candidate_files() -> Iterable[Path]:
    for target in TARGETS:
        base = (REPO_ROOT / target).resolve()
        if base.is_file():
            if not is_binary(base):
                yield base
            continue
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if any(part in EXCLUDED_DIRS for part in path.parts):
                continue
            if is_binary(path):
                continue
            try:
                if path.stat().st_size > 3_000_000:
                    continue
            except OSError:
                continue
            yield path


def chunk_file(path: Path, chunk_size: int, overlap: int) -> List[Chunk]:
    chunks: List[Chunk] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return chunks
    lines = text.splitlines()
    if not lines:
        return chunks
    start = 0
    while start < len(lines):
        end = min(len(lines), start + chunk_size)
        snippet_lines = lines[start:end]
        snippet_text = "\n".join(snippet_lines)
        tokens = Counter(_TOKENIZER.findall(snippet_text.lower()))
        if tokens:
            symbol = detect_symbol(lines, start)
            chunks.append(
                Chunk(
                    path=path.relative_to(REPO_ROOT),
                    start_line=start + 1,
                    end_line=end,
                    text=snippet_text,
                    tokens=tokens,
                    symbol=symbol,
                )
            )
        start += max(1, chunk_size - overlap)
    return chunks


def detect_symbol(lines: Sequence[str], start_index: int) -> str | None:
    # scan upward for function/section headers within ~40 lines
    lower_bound = max(0, start_index - 40)
    for idx in range(start_index, lower_bound - 1, -1):
        text = lines[idx].strip()
        if not text:
            continue
        func_match = _FUNCTION_PATTERN.match(text)
        if func_match:
            return func_match.group(1)
        if text.startswith("#"):
            section = _SECTION_PATTERN.match(text)
            if section:
                return section.group(1).strip()
    return None


def build_index(chunk_size: int, overlap: int) -> Tuple[List[Chunk], Counter]:
    all_chunks: List[Chunk] = []
    doc_freq: Counter = Counter()
    for filepath in candidate_files():
        chunks = chunk_file(filepath, chunk_size, overlap)
        for chunk in chunks:
            all_chunks.append(chunk)
            for term in set(chunk.tokens):
                doc_freq[term] += 1
    return all_chunks, doc_freq


def tokenize(text: str) -> List[str]:
    return _TOKENIZER.findall(text.lower())


def bm25_score(chunk: Chunk, query_tokens: Sequence[str], doc_freq: Counter, avg_len: float, total_docs: int, k1: float = 1.5, b: float = 0.75) -> float:
    score = 0.0
    for term in query_tokens:
        tf = chunk.tokens.get(term)
        if not tf:
            continue
        df = doc_freq.get(term, 0)
        if df == 0:
            continue
        idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * (chunk.length / avg_len))
        score += idf * (numerator / denominator)
    return score


def structural_bonus(chunk: Chunk, query_tokens: Sequence[str]) -> float:
    if not chunk.symbol:
        return 0.0
    symbol_tokens = set(_TOKENIZER.findall(chunk.symbol.lower()))
    if not symbol_tokens:
        return 0.0
    overlap = symbol_tokens.intersection(query_tokens)
    if not overlap:
        return 0.0
    return 0.2 * len(overlap)


def expand_context(chunk: Chunk, window: int) -> Tuple[int, int, str]:
    if window <= 0:
        return chunk.start_line, chunk.end_line, chunk.text
    path = (REPO_ROOT / chunk.path).resolve()
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return chunk.start_line, chunk.end_line, chunk.text
    start_idx = max(0, chunk.start_line - 1 - window)
    end_idx = min(len(lines), chunk.end_line + window)
    snippet = "\n".join(lines[start_idx:end_idx])
    return start_idx + 1, end_idx, snippet


def format_snippet(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    head = lines[: max_lines - 3]
    tail = lines[-2:]
    return "\n".join(head + ["…"] + tail)


def render_results(results, top: int, preview_lines: int, as_json: bool) -> None:
    if as_json:
        payload = [
            {
                "rank": rank,
                "path": str(chunk.path),
                "start_line": start,
                "end_line": end,
                "symbol": chunk.symbol,
                "score": score,
                "snippet": snippet,
            }
            for rank, (score, chunk, start, end, snippet) in enumerate(results[:top], start=1)
        ]
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return

    for rank, (score, chunk, start, end, snippet) in enumerate(results[:top], start=1):
        banner = f"{rank}. {chunk.path}:{start}-{end} | score={score:.3f}"
        if chunk.symbol:
            banner += f" | context={chunk.symbol}"
        print(banner)
        print("---")
        preview = format_snippet(snippet, preview_lines)
        indented = "\n".join(f"    {line}" for line in preview.splitlines())
        print(indented)
        print("---")


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage RAG-2 structural retriever")
    parser.add_argument("query", nargs="+", help="natural-language query")
    parser.add_argument("--top", type=int, default=6, help="number of chunks to return")
    parser.add_argument("--chunk-size", type=int, default=48, help="base chunk size (lines)")
    parser.add_argument("--overlap", type=int, default=24, help="chunk overlap (lines)")
    parser.add_argument("--window", type=int, default=20, help="additional context window (lines)")
    parser.add_argument("--preview-lines", type=int, default=18, help="lines to print per snippet")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    query_tokens = tokenize(" ".join(args.query))
    if not query_tokens:
        print("No valid tokens in query.", file=sys.stderr)
        return 1

    chunks, doc_freq = build_index(args.chunk_size, args.overlap)
    if not chunks:
        print("No eligible text chunks were indexed.", file=sys.stderr)
        return 1

    avg_len = sum(chunk.length for chunk in chunks) / len(chunks)
    total_docs = len(chunks)

    ranked = []
    for chunk in chunks:
        lexical = bm25_score(chunk, query_tokens, doc_freq, avg_len, total_docs)
        if lexical == 0:
            continue
        structural = structural_bonus(chunk, query_tokens)
        score = lexical + structural
        start, end, expanded = expand_context(chunk, args.window)
        ranked.append((score, chunk, start, end, expanded))

    if not ranked:
        print("No relevant chunks found.")
        return 0

    ranked.sort(key=lambda item: item[0], reverse=True)

    print(f"Query: {' '.join(args.query)}")
    print(f"Indexed chunks: {total_docs} | Avg tokens/chunk: {avg_len:.1f}")
    print("---")
    render_results(ranked, args.top, args.preview_lines, args.json)
    print("(Stage RAG-2 planning output — use with stage4 manager/manager3.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
