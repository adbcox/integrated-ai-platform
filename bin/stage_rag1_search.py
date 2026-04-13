#!/usr/bin/env python3
"""Stage RAG-1 lexical retrieval entrypoint for planning-only workflows.

This lightweight searcher scans repo-aware planning surfaces (bin/, shell/, docs/,
and Makefile) and returns the highest-scoring textual chunks for a natural
language query. Results are only meant to guide file/anchor selection prior to
probe creation; all Stage-3 micro-lane constraints still apply downstream.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["bin", "shell", "docs", "Makefile"]
EXCLUDED_DIRS = {".git", "artifacts", "artifacts", "tmp", "temp", "generated", "__pycache__"}
MAX_FILE_BYTES = 2_000_000  # guardrails against huge temp outputs


_TOKENIZER = re.compile(r"[a-z0-9_]+")


@dataclass
class Chunk:
    path: Path
    start_line: int  # 1-indexed inclusive
    end_line: int    # 1-indexed inclusive
    text: str
    tokens: Counter

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
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield path


def chunk_file(path: Path, chunk_size: int, overlap: int) -> Sequence[Chunk]:
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
            chunks.append(
                Chunk(
                    path=path.relative_to(REPO_ROOT),
                    start_line=start + 1,
                    end_line=end,
                    text=snippet_text,
                    tokens=tokens,
                )
            )
        start += max(1, chunk_size - overlap)
    return chunks


def build_index(chunk_size: int, overlap: int) -> tuple[List[Chunk], Counter]:
    all_chunks: List[Chunk] = []
    doc_freq: Counter = Counter()
    for filepath in candidate_files():
        chunks = chunk_file(filepath, chunk_size, overlap)
        for chunk in chunks:
            all_chunks.append(chunk)
            seen_terms = set(chunk.tokens)
            for term in seen_terms:
                doc_freq[term] += 1
    return all_chunks, doc_freq


def tokenize(text: str) -> List[str]:
    return _TOKENIZER.findall(text.lower())


def bm25_score(chunk: Chunk, query_tokens: Sequence[str], doc_freq: Counter, avg_len: float, total_docs: int, k1: float = 1.5, b: float = 0.75) -> float:
    score = 0.0
    for term in query_tokens:
        if term not in chunk.tokens:
            continue
        df = doc_freq.get(term, 0)
        if df == 0:
            continue
        idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)
        tf = chunk.tokens[term]
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * (chunk.length / avg_len))
        score += idf * (numerator / denominator)
    return score


def format_snippet(text: str, max_lines: int = 12) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    head = lines[: max_lines - 2]
    tail = lines[-2:]
    return "\n".join(head + ["…", *tail])


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage RAG-1 lexical retriever for planning")
    parser.add_argument("query", nargs="+", help="natural-language query")
    parser.add_argument("--top", type=int, default=5, help="number of chunks to return")
    parser.add_argument("--chunk-size", type=int, default=32, help="lines per chunk")
    parser.add_argument("--overlap", type=int, default=12, help="line overlap between chunks")
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

    scored = []
    for chunk in chunks:
        score = bm25_score(chunk, query_tokens, doc_freq, avg_len, total_docs)
        if score > 0:
            scored.append((score, chunk))

    if not scored:
        print("No relevant chunks found.")
        return 0

    scored.sort(key=lambda item: item[0], reverse=True)
    limit = max(1, args.top)
    print("Query:", " ".join(args.query))
    print(f"Indexed chunks: {total_docs} | Avg tokens/chunk: {avg_len:.1f}")
    print("---")
    for rank, (score, chunk) in enumerate(scored[:limit], start=1):
        print(f"{rank}. {chunk.path}:{chunk.start_line}-{chunk.end_line} | score={score:.3f}")
        snippet = format_snippet(chunk.text)
        indented = "\n".join(f"    {line}" for line in snippet.splitlines())
        print(indented)
        print("---")
    print("(For planning guidance only – Stage-3 editing guardrails still apply.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
