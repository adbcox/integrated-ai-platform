#!/usr/bin/env python3
"""
aider_context_pack.py — D-17-XXX: RAG context pack generator for Aider runs.

Usage:
    python3 bin/aider_context_pack.py \
        --description "Add retry logic to the downloader" \
        --files scripts/downloader.py scripts/retry.py \
        --output /tmp/context_pack_<run_id>.md \
        [--top-k 3] [--embed-url http://192.168.10.142:11434]

Exit 0 always — failures degrade gracefully to an empty/minimal pack.
The pack is written to --output; path is echoed to stdout.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).parent.parent
CORPUS_PATH = REPO_ROOT / "artifacts" / "aider_trace_corpus_v0.parquet"
VERIFIER_EVENTS = REPO_ROOT / "artifacts" / "aider_runs" / "verifier_events.jsonl"
DOCS_ROOTS = [
    REPO_ROOT / "docs" / "runbooks",
    REPO_ROOT / "docs" / "architecture-facts",
]
TOP_K = 3
MAX_PACK_TOKENS = 2000  # approximate; 1 token ≈ 4 chars

# ---------------------------------------------------------------------------
# Embedding: try Ollama nomic-embed-text, fall back to TF-IDF cosine
# ---------------------------------------------------------------------------

def _tfidf_matrix(texts: list[str]) -> np.ndarray:
    """Build a simple TF-IDF matrix (rows = docs, cols = terms)."""
    tokenizer = re.compile(r"[a-z0-9_]+")
    tokenized = [set(tokenizer.findall(t.lower())) for t in texts]
    vocab = sorted({tok for doc in tokenized for tok in doc})
    vocab_idx = {t: i for i, t in enumerate(vocab)}
    mat = np.zeros((len(texts), len(vocab)), dtype=np.float32)
    for i, doc in enumerate(tokenized):
        for tok in doc:
            if tok in vocab_idx:
                mat[i, vocab_idx[tok]] = 1.0
    # IDF weighting
    df = np.sum(mat > 0, axis=0) + 1
    idf = np.log(len(texts) / df + 1)
    mat = mat * idf
    # L2 normalize rows
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def _cosine_scores(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    q = query_vec / (np.linalg.norm(query_vec) + 1e-9)
    return matrix @ q


def _embed_ollama(text: str, base_url: str) -> Optional[np.ndarray]:
    """Call Ollama /api/embeddings with nomic-embed-text. Returns None on any error."""
    try:
        import urllib.request
        payload = json.dumps({"model": "nomic-embed-text", "prompt": text}).encode()
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
        vec = np.array(data["embedding"], dtype=np.float32)
        return vec / (np.linalg.norm(vec) + 1e-9)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Corpus retrieval
# ---------------------------------------------------------------------------

def _file_overlap_score(query_files: list[str], corpus_files_raw: str) -> float:
    """Jaccard overlap between query file basenames and corpus file basenames."""
    if not query_files or not corpus_files_raw:
        return 0.0
    try:
        corpus_files = json.loads(corpus_files_raw) if isinstance(corpus_files_raw, str) else corpus_files_raw
    except Exception:
        return 0.0
    q_bases = {Path(f).name for f in query_files}
    c_bases = {Path(f).name for f in (corpus_files if isinstance(corpus_files, list) else [])}
    if not q_bases or not c_bases:
        return 0.0
    intersection = len(q_bases & c_bases)
    union = len(q_bases | c_bases)
    return intersection / union if union else 0.0


def retrieve_similar(
    description: str,
    files: list[str],
    top_k: int,
    embed_base: Optional[str],
    df: pd.DataFrame,
) -> pd.DataFrame:
    prompts = df["prompt_text"].fillna("").tolist()

    # Semantic score
    sem_scores = np.zeros(len(df), dtype=np.float32)
    if embed_base:
        qvec = _embed_ollama(description, embed_base)
        if qvec is not None:
            corpus_vecs = np.vstack([_embed_ollama(p, embed_base) or np.zeros_like(qvec) for p in prompts])
            sem_scores = _cosine_scores(qvec, corpus_vecs)

    # TF-IDF fallback (always computed; used when embedding unavailable)
    all_texts = [description] + prompts
    tfidf = _tfidf_matrix(all_texts)
    query_tfidf = tfidf[0]
    corpus_tfidf = tfidf[1:]
    tfidf_scores = _cosine_scores(query_tfidf, corpus_tfidf)

    # Combined semantic score: prefer ollama if available
    if np.any(sem_scores > 0):
        final_sem = 0.7 * sem_scores + 0.3 * tfidf_scores
    else:
        final_sem = tfidf_scores

    # File overlap score
    file_scores = np.array([
        _file_overlap_score(files, row) for row in df["requested_files"].fillna("[]")
    ], dtype=np.float32)

    # Combined score: 70% semantic, 30% file overlap
    combined = 0.7 * final_sem + 0.3 * file_scores
    df = df.copy()
    df["_score"] = combined
    return df.nlargest(top_k, "_score")


# ---------------------------------------------------------------------------
# Failure mode summary
# ---------------------------------------------------------------------------

def failure_modes_for_files(files: list[str], df: pd.DataFrame) -> dict[str, dict]:
    """Count failure modes for rows that touch any of the query files."""
    if not files:
        return {}
    basenames = {Path(f).name for f in files}
    def matches(raw):
        try:
            listed = json.loads(raw) if isinstance(raw, str) else raw
            return any(Path(p).name in basenames for p in (listed or []))
        except Exception:
            return False

    subset = df[df["requested_files"].apply(matches)]
    if subset.empty:
        return {}

    modes: dict[str, dict] = {}
    for cls, grp in subset.groupby("failure_mode_class"):
        details = grp["failure_mode_detail"].dropna().value_counts().head(2).to_dict()
        modes[str(cls)] = {
            "count": len(grp),
            "top_details": details,
        }
    return modes


# ---------------------------------------------------------------------------
# Doctrine / runbook retrieval (lexical keyword match)
# ---------------------------------------------------------------------------

def retrieve_docs(description: str, max_docs: int = 3) -> list[tuple[str, str]]:
    """Find doc files whose names or first heading match keywords in description."""
    keywords = set(re.findall(r"[a-z]{4,}", description.lower()))
    if not keywords:
        return []

    candidates: list[tuple[float, str, str]] = []
    for root in DOCS_ROOTS:
        for md in root.glob("*.md"):
            if md.name == "README.md":
                continue
            stem_words = set(re.findall(r"[a-z]+", md.stem.replace("-", " ")))
            overlap = len(keywords & stem_words)
            if overlap == 0:
                continue
            try:
                first_line = md.read_text(encoding="utf-8", errors="replace").splitlines()[0]
                heading = first_line.lstrip("#").strip()
            except Exception:
                heading = md.stem
            rel = str(md.relative_to(REPO_ROOT))
            candidates.append((overlap, rel, heading))

    candidates.sort(key=lambda x: -x[0])
    return [(rel, heading) for _, rel, heading in candidates[:max_docs]]


# ---------------------------------------------------------------------------
# Verifier evidence
# ---------------------------------------------------------------------------

def verifier_summary(description: str) -> list[dict]:
    """Find verifier events for tasks similar to description (keyword overlap)."""
    if not VERIFIER_EVENTS.exists():
        return []
    keywords = set(re.findall(r"[a-z]{4,}", description.lower()))
    results = []
    try:
        with VERIFIER_EVENTS.open() as f:
            for line in f:
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                ev_desc = ev.get("description", "")
                ev_words = set(re.findall(r"[a-z]{4,}", ev_desc.lower()))
                if keywords & ev_words and ev.get("verdict") in ("AGREE", "DISAGREE"):
                    results.append(ev)
    except Exception:
        pass
    return results[:3]


# ---------------------------------------------------------------------------
# Pack rendering
# ---------------------------------------------------------------------------

def _outcome_label(row: pd.Series) -> str:
    cls = str(row.get("failure_mode_class", ""))
    if cls == "success":
        return "success"
    return cls or "unknown"


def _insight(row: pd.Series) -> str:
    detail = str(row.get("failure_mode_detail", "") or "")
    cls = str(row.get("failure_mode_class", "") or "")
    if cls == "success":
        return "Task completed successfully"
    if detail:
        return detail[:80]
    return f"Failed: {cls}"


def render_pack(
    description: str,
    files: list[str],
    similar: pd.DataFrame,
    failure_modes: dict,
    docs: list[tuple[str, str]],
    verifier: list[dict],
    run_id: str,
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = []

    lines.append(f"# Task Context Pack — {ts}")
    lines.append(f"<!-- run_id={run_id} task={description[:60]!r} -->")
    lines.append("")

    # Similar prior tasks
    lines.append("## Similar prior tasks (top 3 by combined score)")
    if similar.empty:
        lines.append("_No similar prior tasks found in corpus._")
    else:
        for _, row in similar.iterrows():
            ts_row = str(row.get("record_timestamp", "?"))[:10]
            outcome = _outcome_label(row)
            prompt = str(row.get("prompt_text", ""))[:120].replace("\n", " ")
            model = str(row.get("model", "?"))
            dur = row.get("duration_seconds", 0)
            dur_s = f"{float(dur):.0f}s" if dur else "?s"
            insight = _insight(row)
            lines.append(f"- **{ts_row}** [{outcome}]: {prompt}…")
            lines.append(f"  model={model} duration={dur_s}")
            lines.append(f"  Insight: {insight}")
            lines.append("")

    # Failure modes for target files
    lines.append("## Known failure modes for target files")
    if not failure_modes:
        lines.append("_No historical failure data for these file paths._")
    else:
        for mode, data in sorted(failure_modes.items(), key=lambda x: -x[1]["count"]):
            count = data["count"]
            tops = ", ".join(f"{k}({v})" for k, v in data["top_details"].items())
            lines.append(f"- **{mode}**: {count} occurrences" + (f" — {tops}" if tops else ""))
    lines.append("")

    # Doctrine and runbooks
    lines.append("## Applicable doctrine and runbooks")
    if not docs:
        lines.append("_No matching doctrine files found._")
    else:
        for rel, heading in docs:
            lines.append(f"- `{rel}`: {heading}")
    lines.append("")

    # Verifier evidence
    lines.append("## Verifier evidence on similar tasks")
    if not verifier:
        lines.append("_No verifier AGREE/DISAGREE events for similar tasks._")
    else:
        for ev in verifier:
            v = ev.get("verdict", "?")
            d = ev.get("description", "")[:80]
            r = (ev.get("reason") or "")[:80]
            lines.append(f"- [{v}] {d}" + (f" — {r}" if r else ""))
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Aider context pack")
    parser.add_argument("--description", "-d", default="", help="Task description / --message text")
    parser.add_argument("--files", "-f", nargs="*", default=[], help="Target file paths")
    parser.add_argument("--output", "-o", required=True, help="Output .md path")
    parser.add_argument("--top-k", type=int, default=TOP_K)
    parser.add_argument("--embed-url", default=None, help="Ollama base URL for nomic-embed-text")
    parser.add_argument("--run-id", default="manual")
    args = parser.parse_args()

    t0 = time.monotonic()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    description = args.description.strip()
    files = [f for f in (args.files or []) if not f.startswith("-")]

    # Graceful: if corpus missing, emit minimal pack
    if not CORPUS_PATH.exists():
        output_path.write_text(f"# Task Context Pack\n_Corpus not found at {CORPUS_PATH}_\n")
        print(output_path)
        return 0

    try:
        df = pd.read_parquet(CORPUS_PATH)
    except Exception as e:
        output_path.write_text(f"# Task Context Pack\n_Corpus load error: {e}_\n")
        print(output_path)
        return 0

    similar = pd.DataFrame()
    failure_modes: dict = {}
    docs: list = []
    verifier: list = []

    if description:
        try:
            similar = retrieve_similar(description, files, args.top_k, args.embed_url, df)
        except Exception:
            pass

        try:
            docs = retrieve_docs(description)
        except Exception:
            pass

        try:
            verifier = verifier_summary(description)
        except Exception:
            pass

    if files:
        try:
            failure_modes = failure_modes_for_files(files, df)
        except Exception:
            pass

    pack = render_pack(description, files, similar, failure_modes, docs, verifier, args.run_id)
    output_path.write_text(pack, encoding="utf-8")

    elapsed = time.monotonic() - t0
    print(output_path, file=sys.stderr)
    print(f"[context-pack] generated in {elapsed:.2f}s ({len(pack)} chars)", file=sys.stderr)
    print(output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
