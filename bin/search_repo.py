#!/usr/bin/env python3
"""Repo-wide code search with ranked results."""

import sys
import subprocess
import re
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple


class RepoSearch:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def search(self, query: str, file_pattern: str = "*.py") -> List[Tuple[str, int, str, int]]:
        """Search and rank results.

        Returns: [(file, line_num, line_text, score), ...]
        """
        # Use ripgrep if available, fallback to git grep
        try:
            result = subprocess.run(
                ["rg", "-n", "--type", "py", query, str(self.repo_root)],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except FileNotFoundError:
            result = subprocess.run(
                ["git", "grep", "-n", query, "--", file_pattern],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            print("Search timeout", file=sys.stderr)
            return []

        matches = []
        for line in result.stdout.split("\n"):
            if not line:
                continue

            parts = line.split(":", 2)
            if len(parts) < 3:
                continue

            file_path, line_num, text = parts
            try:
                score = self._score_match(query, file_path, text)
                matches.append((file_path, int(line_num), text.strip(), score))
            except ValueError:
                continue

        # Sort by score (highest first)
        return sorted(matches, key=lambda x: x[3], reverse=True)

    def _score_match(self, query: str, file_path: str, text: str) -> int:
        """Rank match relevance."""
        score = 0

        # Exact match higher than partial
        if query in text:
            score += 10

        # Function/class definitions score higher
        if re.match(r"\s*(def|class)\s+", text):
            score += 5

        # Matches in domains/ or connectors/ more relevant
        if "domains/" in file_path or "connectors/" in file_path:
            score += 3

        # Test files score lower
        if "test" in file_path.lower():
            score -= 5

        return score


def main():
    if len(sys.argv) < 2:
        print("Usage: search_repo.py 'query' [file_pattern]")
        print("\nExamples:")
        print("  search_repo.py 'health_check'")
        print("  search_repo.py 'def execute' '*.py'")
        return 1

    query = sys.argv[1]
    pattern = sys.argv[2] if len(sys.argv) > 2 else "*.py"

    searcher = RepoSearch(Path.cwd())
    results = searcher.search(query, pattern)

    if not results:
        print(f"No matches found for '{query}'")
        return 1

    print(f"Found {len(results)} matches for '{query}':\n")

    # Group by file
    by_file = defaultdict(list)
    for file_path, line_num, text, score in results[:20]:  # Top 20
        by_file[file_path].append((line_num, text, score))

    for file_path in sorted(by_file.keys()):
        print(f"\n📄 {file_path}")
        for line_num, text, score in sorted(by_file[file_path], key=lambda x: x[2], reverse=True)[:5]:  # Top 5 per file
            print(f"   {line_num:4d}: {text[:80]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
