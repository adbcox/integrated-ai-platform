#!/usr/bin/env python3
"""Dynamic token budgeting and file relevance scoring for executor prompt construction.

This is a domain module — NOT Python's contextlib.
Import as: ``from domains.context_manager import ContextManager``

Constants:
    DEFAULT_TOKEN_BUDGET: Default token limit for a single prompt context.
    RELEVANCE_DECAY_DAYS: Half-life (in days) for recency score calculation.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_TOKEN_BUDGET: int = 8000
RELEVANCE_DECAY_DAYS: int = 30

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class FileRelevance:
    """Relevance score for a single file relative to a query.

    Attributes:
        path: Absolute or repo-relative path to the file.
        import_count: Number of other files that import this file.
        reference_count: Number of query token matches in this file.
        recency_score: Exponential decay score based on days since last modification.
        total_score: Weighted composite: import*0.3 + reference*0.5 + recency*0.2.
    """

    path: str
    import_count: int
    reference_count: int
    recency_score: float
    total_score: float


@dataclass
class ContextBudget:
    """Token budget allocation across files.

    Attributes:
        total_tokens: Total tokens available.
        allocated: Mapping of file_path → token count allocated.
        remaining: Tokens not yet allocated.
    """

    total_tokens: int
    allocated: Dict[str, int] = field(default_factory=dict)
    remaining: int = 0

    def __post_init__(self) -> None:
        if self.remaining == 0 and not self.allocated:
            self.remaining = self.total_tokens


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class ContextManager:
    """Dynamic token budgeting and file relevance scoring.

    Scores files by how many other files import them, how many query tokens
    appear in them, and how recently they were modified. Allocates a token
    budget proportionally and truncates file content to fit.

    Example::

        cm = ContextManager(repo_root="/path/to/repo", token_budget=4000)
        context = cm.build_context("improve ExecutorFactory", ["framework/code_executor.py"])
        print(context)
    """

    def __init__(
        self,
        repo_root: str,
        token_budget: int = DEFAULT_TOKEN_BUDGET,
    ) -> None:
        """Initialise the context manager.

        Args:
            repo_root: Absolute path to the repository root.
            token_budget: Maximum tokens for built context.
        """
        self.repo_root = Path(repo_root)
        self.token_budget = token_budget
        self._usage_log = self.repo_root / "artifacts" / "token_usage.jsonl"
        self._usage_log.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(
            "ContextManager initialised repo=%s budget=%d", repo_root, token_budget
        )

    # ------------------------------------------------------------------
    # Relevance scoring
    # ------------------------------------------------------------------

    def score_file_relevance(
        self, file_path: str, query_tokens: set[str]
    ) -> FileRelevance:
        """Compute a composite relevance score for a single file.

        The score combines:
        - ``import_count``: how many other files import this file (weight 0.3)
        - ``reference_count``: query token hits in the file (weight 0.5)
        - ``recency_score``: exp(−days_since_modified / RELEVANCE_DECAY_DAYS) (weight 0.2)

        Args:
            file_path: Path to the file (absolute or relative to repo_root).
            query_tokens: Set of lowercase token strings from the query.

        Returns:
            A ``FileRelevance`` instance.
        """
        resolved = self._resolve_path(file_path)
        import_count = self._count_imports(resolved)
        reference_count = self._count_references(resolved, query_tokens)
        recency_score = self._recency_score(resolved)

        total = (
            import_count * 0.3
            + reference_count * 0.5
            + recency_score * 0.2
        )

        return FileRelevance(
            path=str(file_path),
            import_count=import_count,
            reference_count=reference_count,
            recency_score=recency_score,
            total_score=round(total, 4),
        )

    def rank_files(
        self, query: str, candidate_files: List[str]
    ) -> List[FileRelevance]:
        """Rank candidate files by relevance to a query.

        Args:
            query: Free-text query string.
            candidate_files: Paths to files to rank.

        Returns:
            List of ``FileRelevance`` objects sorted descending by total_score.
        """
        query_tokens = self._tokenize(query)
        scored = [
            self.score_file_relevance(fp, query_tokens) for fp in candidate_files
        ]
        scored.sort(key=lambda r: r.total_score, reverse=True)
        logger.debug("Ranked %d files for query %r", len(scored), query[:60])
        return scored

    # ------------------------------------------------------------------
    # Budget allocation
    # ------------------------------------------------------------------

    def allocate_budget(self, files: List[FileRelevance]) -> ContextBudget:
        """Allocate tokens proportionally by relevance score.

        Any single file is capped at 25% of the total budget to ensure
        diversity across files.

        Args:
            files: Ranked list of ``FileRelevance`` objects.

        Returns:
            A ``ContextBudget`` with per-file token allocations.
        """
        budget = ContextBudget(total_tokens=self.token_budget)

        if not files:
            budget.remaining = self.token_budget
            return budget

        total_score = sum(f.total_score for f in files)
        cap = int(self.token_budget * 0.25)

        if total_score == 0:
            # Equal split when all scores are zero
            per_file = min(cap, self.token_budget // max(1, len(files)))
            for fr in files:
                budget.allocated[fr.path] = per_file
        else:
            for fr in files:
                proportion = fr.total_score / total_score
                allocated = min(cap, int(self.token_budget * proportion))
                budget.allocated[fr.path] = allocated

        budget.remaining = self.token_budget - sum(budget.allocated.values())
        logger.debug(
            "Budget allocated: %d files, %d tokens used, %d remaining",
            len(budget.allocated),
            self.token_budget - budget.remaining,
            budget.remaining,
        )
        return budget

    # ------------------------------------------------------------------
    # Content truncation
    # ------------------------------------------------------------------

    def truncate_to_budget(self, file_path: str, token_count: int) -> str:
        """Read a file and truncate its content to approximately *token_count* tokens.

        Prefers class and function definitions over implementation details:
        if the file has top-level ``class`` or ``def`` statements, those are
        surfaced first before implementation lines.

        Args:
            file_path: Path to the file.
            token_count: Token limit for the returned content.

        Returns:
            Truncated file content string.
        """
        resolved = self._resolve_path(file_path)
        if not resolved.is_file():
            logger.warning("File not found for truncation: %s", resolved)
            return ""

        try:
            content = resolved.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.error("Failed to read %s: %s", resolved, exc)
            return ""

        lines = content.splitlines(keepends=True)

        # Prefer definitions first
        definition_lines: List[str] = []
        implementation_lines: List[str] = []
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith("class ") or stripped.startswith("def "):
                definition_lines.append(line)
            else:
                implementation_lines.append(line)

        ordered_lines = definition_lines + implementation_lines
        char_budget = token_count * 4

        result_chars = 0
        result_lines: List[str] = []
        for line in ordered_lines:
            if result_chars + len(line) > char_budget:
                break
            result_lines.append(line)
            result_chars += len(line)

        return "".join(result_lines)

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count using a chars/4 heuristic.

        Args:
            text: Input text.

        Returns:
            Estimated token count.
        """
        return max(0, len(text) // 4)

    # ------------------------------------------------------------------
    # Context building
    # ------------------------------------------------------------------

    def build_context(self, query: str, files: List[str]) -> str:
        """Build a concatenated context string within the token budget.

        Ranks files by relevance, allocates a token budget proportionally,
        truncates each file to its allocation, and concatenates everything.

        Args:
            query: The user query driving relevance scoring.
            files: Candidate file paths.

        Returns:
            Concatenated context string ready for prompt injection.
        """
        if not files:
            return ""

        ranked = self.rank_files(query, files)
        budget = self.allocate_budget(ranked)

        sections: List[str] = []
        for fr in ranked:
            allocation = budget.allocated.get(fr.path, 0)
            if allocation <= 0:
                continue
            content = self.truncate_to_budget(fr.path, allocation)
            if content.strip():
                header = f"# File: {fr.path} (relevance={fr.total_score:.3f})\n"
                sections.append(header + content)

        context = "\n\n".join(sections)
        logger.info(
            "Built context: %d files, ~%d tokens",
            len(sections),
            self.estimate_tokens(context),
        )
        return context

    # ------------------------------------------------------------------
    # Usage tracking
    # ------------------------------------------------------------------

    def track_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        operation: str,
    ) -> None:
        """Append a token usage record to artifacts/token_usage.jsonl.

        Args:
            prompt_tokens: Number of tokens in the prompt.
            completion_tokens: Number of tokens in the completion.
            operation: Label for the operation (e.g. "build_context").
        """
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }
        try:
            with self._usage_log.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
        except OSError as exc:
            logger.warning("Failed to write token usage log: %s", exc)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Return aggregated token usage statistics.

        Returns:
            Dict with keys: total (int), by_operation (dict), recent_trend (list).
        """
        if not self._usage_log.is_file():
            return {"total": 0, "by_operation": {}, "recent_trend": []}

        records: List[Dict[str, Any]] = []
        try:
            for line in self._usage_log.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to read token usage log: %s", exc)
            return {"total": 0, "by_operation": {}, "recent_trend": []}

        total = sum(r.get("total_tokens", 0) for r in records)
        by_op: Dict[str, int] = {}
        for r in records:
            op = r.get("operation", "unknown")
            by_op[op] = by_op.get(op, 0) + r.get("total_tokens", 0)

        # Last 10 records as trend
        trend = [
            {"operation": r.get("operation"), "total": r.get("total_tokens", 0), "ts": r.get("timestamp")}
            for r in records[-10:]
        ]

        return {"total": total, "by_operation": by_op, "recent_trend": trend}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve a file path relative to repo_root if not absolute.

        Args:
            file_path: Absolute or relative path.

        Returns:
            Resolved ``Path`` object.
        """
        p = Path(file_path)
        if p.is_absolute():
            return p
        return self.repo_root / p

    def _tokenize(self, text: str) -> set[str]:
        """Extract lowercase alpha-numeric tokens from text.

        Args:
            text: Input string.

        Returns:
            Set of token strings.
        """
        return set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]+", text.lower()))

    def _count_imports(self, file_path: Path) -> int:
        """Count how many files in the repo import the given file.

        Uses grep to avoid loading the entire codebase into memory.

        Args:
            file_path: Resolved path to the file.

        Returns:
            Import reference count (0 on error).
        """
        # Derive module-style reference (e.g. "domains.context_manager")
        try:
            rel = file_path.relative_to(self.repo_root)
        except ValueError:
            return 0

        # Build possible import patterns
        module_name = str(rel.with_suffix("")).replace(os.sep, ".")
        stem = file_path.stem
        patterns = [module_name, stem]

        total = 0
        for pattern in patterns:
            try:
                result = subprocess.run(
                    ["grep", "-r", "--include=*.py", "-l", pattern, str(self.repo_root)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                hits = [
                    line for line in result.stdout.splitlines()
                    if line.strip() and line.strip() != str(file_path)
                ]
                total += len(hits)
            except Exception:  # pylint: disable=broad-except
                pass

        return total

    def _count_references(self, file_path: Path, query_tokens: set[str]) -> int:
        """Count occurrences of query tokens inside a file.

        Args:
            file_path: Resolved path to the file.
            query_tokens: Set of lowercase tokens to search for.

        Returns:
            Total token hit count.
        """
        if not file_path.is_file() or not query_tokens:
            return 0

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            return 0

        return sum(content.count(tok) for tok in query_tokens)

    def _recency_score(self, file_path: Path) -> float:
        """Compute an exponential decay recency score.

        Score = exp(−days_since_modified / RELEVANCE_DECAY_DAYS).
        Newer files score close to 1.0; files untouched for RELEVANCE_DECAY_DAYS
        score approximately 0.37.

        Args:
            file_path: Resolved path to the file.

        Returns:
            Recency score in [0, 1].
        """
        if not file_path.exists():
            return 0.0
        try:
            mtime = file_path.stat().st_mtime
            days_ago = (time.time() - mtime) / 86400.0
            return math.exp(-days_ago / RELEVANCE_DECAY_DAYS)
        except OSError:
            return 0.0
