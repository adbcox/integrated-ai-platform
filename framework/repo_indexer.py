"""Smart keyword-based file selector for cloned reference repositories.

Given a task description, scores all .py files in ~/ai-reference/ by relevance
(filename + docstring + imports) and returns the top N that fit within the
context budget.

Why not embeddings? The 14b model is already running; adding an embedding
model for ~6 file searches per minute is overkill. BM25-style keyword scoring
over 50-200 files completes in milliseconds.

Budget reality check (qwen2.5-coder:14b, 32k token window):
  Aider system prompt: ~2,000 tokens
  Mini repo context:   ~1,300 tokens
  Current patterns:   ~1,100 tokens
  Task + target file: ~1,000 tokens
  Remaining budget:   ~27,000 tokens = ~108,000 chars

We cap at 80,000 chars (20k tokens) to leave 7k tokens for model output.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

AI_REFERENCE_DIR = Path.home() / "ai-reference"

# Max chars for ALL repo files combined (on top of curated patterns)
REPO_BUDGET_CHARS = 80_000

# Files larger than this are skipped (likely generated or data files)
MAX_FILE_CHARS = 8_000

# Domain-specific keyword sets for category matching
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "MEDIA": ["stream", "video", "audio", "ffmpeg", "media", "player", "codec", "transcode"],
    "UI": ["widget", "dashboard", "frontend", "render", "display", "chart", "component"],
    "API": ["endpoint", "route", "handler", "fastapi", "flask", "rest", "http", "request"],
    "DATA": ["etl", "pipeline", "transform", "database", "query", "schema", "migration"],
    "OPS": ["monitor", "alert", "metric", "health", "deploy", "docker", "kubernetes"],
    "LEARN": ["train", "model", "inference", "predict", "embedding", "neural"],
    "TEST": ["test", "assert", "fixture", "mock", "coverage", "pytest"],
    "CORE": ["executor", "factory", "registry", "plugin", "dispatch", "abstract"],
    "PERIPH": ["serial", "bluetooth", "usb", "printer", "gpio", "i2c", "protocol", "device"],
}

# Boost scores for files whose NAMES contain these terms (high signal)
NAME_BOOST_TERMS = [
    "pattern", "example", "demo", "base", "abstract", "interface",
    "factory", "adapter", "observer", "repository", "service",
]


def _tokenize(text: str) -> list[str]:
    """Split text into lowercase tokens, stripping punctuation."""
    return re.findall(r"[a-z][a-z0-9_]{2,}", text.lower())


def _score_file(path: Path, query_tokens: set[str], category_tokens: set[str]) -> float:
    """Score a single .py file for relevance to the query.

    Scoring:
    - Filename match: 5.0 per token hit (highest signal)
    - Name boost terms: 2.0 each
    - First 100 lines (docstrings, imports, class/def names): 0.5 per hit
    - Category keyword match in content: 1.0 per hit (capped at 5)
    """
    score = 0.0
    stem_tokens = set(_tokenize(path.stem))

    # Filename matches
    for token in query_tokens & stem_tokens:
        score += 5.0

    # Name boost (pattern files, examples, etc.)
    for term in NAME_BOOST_TERMS:
        if term in path.stem.lower():
            score += 2.0
            break

    try:
        content = path.read_text(errors="replace")
        # Only scan first 100 lines for speed
        lines = content.splitlines()[:100]
        head = " ".join(lines)
        head_tokens = set(_tokenize(head))

        # Query token matches in head
        hits = len(query_tokens & head_tokens)
        score += hits * 0.5

        # Category keyword matches
        cat_hits = len(category_tokens & head_tokens)
        score += min(cat_hits, 5) * 1.0

    except Exception:
        pass

    return score


class RepoIndexer:
    """Selects the most relevant .py files from cloned reference repositories."""

    def __init__(self, reference_dir: Optional[Path] = None) -> None:
        self.reference_dir = reference_dir or AI_REFERENCE_DIR

    def repos_available(self) -> bool:
        """True if at least one repo has been cloned."""
        if not self.reference_dir.exists():
            return False
        return any(
            p.is_dir() and any(p.rglob("*.py"))
            for p in self.reference_dir.iterdir()
        )

    def get_relevant_files(
        self,
        task_description: str,
        category: str = "_default",
        budget_chars: int = REPO_BUDGET_CHARS,
        max_files: int = 5,
    ) -> list[str]:
        """Return list of --read=<path> flags for the most relevant repo files.

        Args:
            task_description: The aider task message.
            category: Roadmap category (MEDIA, API, etc.)
            budget_chars: Max total chars for all selected files.
            max_files: Hard limit on number of files to select.

        Returns:
            List of "--read=/path/to/file.py" strings, sorted by relevance.
        """
        if not self.repos_available():
            return []

        query_tokens = set(_tokenize(task_description))
        category_tokens = set(CATEGORY_KEYWORDS.get(category.upper(), []))

        # Score all eligible .py files across all cloned repos
        candidates: list[tuple[float, Path]] = []
        for repo_dir in self.reference_dir.iterdir():
            if not repo_dir.is_dir():
                continue
            for py_file in repo_dir.rglob("*.py"):
                # Skip __pycache__, setup.py, conftest etc.
                if any(part.startswith("__") or part == ".git"
                       for part in py_file.parts):
                    continue
                if py_file.name in ("setup.py", "conftest.py", "manage.py"):
                    continue
                size = py_file.stat().st_size
                if size < 100 or size > MAX_FILE_CHARS:
                    continue
                score = _score_file(py_file, query_tokens, category_tokens)
                if score > 0:
                    candidates.append((score, py_file))

        candidates.sort(reverse=True)

        flags: list[str] = []
        used = 0
        for score, path in candidates:
            size = path.stat().st_size
            if used + size > budget_chars:
                continue
            flags.append(f"--read={path}")
            used += size
            if len(flags) >= max_files:
                break

        return flags

    def list_repos(self) -> list[tuple[str, int]]:
        """Return (repo_name, file_count) for each cloned repo."""
        if not self.reference_dir.exists():
            return []
        result = []
        for repo_dir in sorted(self.reference_dir.iterdir()):
            if repo_dir.is_dir():
                count = sum(1 for _ in repo_dir.rglob("*.py"))
                result.append((repo_dir.name, count))
        return result
