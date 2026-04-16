"""Retrieval planning integration with codebase repomap for better file selection.

This module enhances retrieval target selection by incorporating symbol-aware
codebase understanding from the repomap to:
- Identify most relevant files for query topics
- Understand inter-file dependencies
- Provide better context scope suggestions
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .codebase_repomap import RepomapEntry


@dataclass
class RetrievalTarget:
    """Candidate file for retrieval/editing in a task."""
    path: str
    relevance_score: float  # 0.0 to 1.0
    reason: str
    symbol_match_count: int
    dependency_distance: int  # 0 = direct, 1 = transitive, etc.


class RepomapAwareRetrieval:
    """Retrieval selector using repomap symbol understanding."""

    def __init__(self, repomap_path: Optional[Path] = None) -> None:
        self.repomap: dict[str, Any] = {}
        if repomap_path and repomap_path.exists():
            try:
                self.repomap = json.loads(repomap_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass

    def select_targets(
        self,
        *,
        query: str,
        query_tokens: list[str],
        max_targets: int = 10,
        include_dependents: bool = True,
    ) -> list[RetrievalTarget]:
        """Select most relevant files based on query and symbol understanding."""

        if not self.repomap.get("files"):
            return []

        targets: list[RetrievalTarget] = []
        query_terms = set(t.lower() for t in query_tokens)

        files = self.repomap.get("files", [])
        file_by_path = {f["path"]: f for f in files}

        # Score each file
        for file_info in files:
            path = file_info["path"]
            symbols = file_info.get("symbols", [])

            # Count symbol matches
            symbol_matches = 0
            for symbol in symbols:
                name = str(symbol.get("name", "")).lower()
                kind = str(symbol.get("kind", ""))
                for term in query_terms:
                    if term in name:
                        symbol_matches += 1
                        break

            # Check if filename itself matches query
            filename_score = 0.0
            filename_lower = path.lower()
            for term in query_terms:
                if term in filename_lower:
                    filename_score = max(filename_score, 0.8)

            # Base relevance from direct matches
            relevance = filename_score + min(0.3, symbol_matches * 0.1)

            if relevance > 0.0:
                targets.append(
                    RetrievalTarget(
                        path=path,
                        relevance_score=relevance,
                        reason=f"filename_score={filename_score:.2f}, symbol_matches={symbol_matches}",
                        symbol_match_count=symbol_matches,
                        dependency_distance=0,
                    )
                )

            # Include direct dependents if requested
            if include_dependents and symbol_matches > 0:
                for other_file in files:
                    other_path = other_file["path"]
                    if other_path == path:
                        continue
                    depends_on = other_file.get("depends_on", [])
                    if path in depends_on:
                        targets.append(
                            RetrievalTarget(
                                path=other_path,
                                relevance_score=relevance * 0.6,  # Reduced for indirect
                                reason=f"depends_on={path}",
                                symbol_match_count=0,
                                dependency_distance=1,
                            )
                        )

        # Sort by relevance and limit
        targets.sort(key=lambda t: (-t.relevance_score, -t.symbol_match_count, t.path))
        return targets[:max_targets]

    def estimate_context_scope(
        self,
        targets: list[RetrievalTarget],
    ) -> dict[str, Any]:
        """Estimate total context size needed for targets."""

        if not self.repomap.get("files"):
            return {"estimated_tokens": 0, "file_count": 0}

        file_by_path = {f["path"]: f for f in self.repomap.get("files", [])}
        total_loc = 0
        file_count = 0

        for target in targets:
            file_info = file_by_path.get(target.path)
            if file_info:
                # Rough token estimate: ~4 tokens per line of code
                total_loc += file_info.get("lines_of_code", 0)
                file_count += 1

        estimated_tokens = int(total_loc * 4)

        return {
            "estimated_tokens": estimated_tokens,
            "file_count": file_count,
            "total_loc": total_loc,
            "within_budget": estimated_tokens < 32000,  # Budget for bounded multi-file task context
        }
