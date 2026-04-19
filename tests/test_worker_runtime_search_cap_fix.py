"""Tests for PHASE3-SEARCH-CAP-FIX-1: per-file max-count and raised total cap."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.worker_runtime import (
    _PHASE2_SEARCH_MAX_MATCHES,
    _tool_search_ripgrep,
)


class TestSearchCapConstants(unittest.TestCase):
    def test_max_matches_at_least_2000(self):
        self.assertGreaterEqual(_PHASE2_SEARCH_MAX_MATCHES, 2000)

    def test_max_matches_not_200(self):
        self.assertNotEqual(_PHASE2_SEARCH_MAX_MATCHES, 200)


class TestRipgrepNoDashMFlag(unittest.TestCase):
    """Verify the ripgrep call no longer passes -m (which overrides --max-count)."""

    def _src(self) -> str:
        return (REPO_ROOT / "framework" / "worker_runtime.py").read_text()

    def test_no_dash_m_str_max_matches_in_source(self):
        src = self._src()
        self.assertNotIn('"-m", str(max_matches)', src)

    def test_max_count_3_still_present(self):
        src = self._src()
        self.assertIn('"--max-count", "3"', src)

    def test_rg_call_has_no_bare_dash_m_arg(self):
        src = self._src()
        idx = src.find("_tool_search_ripgrep")
        block = src[idx : idx + 600]
        self.assertNotIn('"-m"', block)


class TestRipgrepReturnsManyFiles(unittest.TestCase):
    """Integration: with --max-count 3, a broad query returns results from many files."""

    def test_broad_query_returns_multiple_files(self):
        matches = _tool_search_ripgrep("def ", REPO_ROOT, max_matches=_PHASE2_SEARCH_MAX_MATCHES)
        files = {m["path"] for m in matches}
        self.assertGreater(len(files), 10, "Expected hits across many files")

    def test_framework_files_present_in_broad_search(self):
        matches = _tool_search_ripgrep("def ", REPO_ROOT, max_matches=_PHASE2_SEARCH_MAX_MATCHES)
        paths = {m["path"] for m in matches}
        framework_paths = {p for p in paths if "framework" in p}
        self.assertTrue(framework_paths, "Expected framework/ files in results")

    def test_per_file_cap_respected(self):
        """No single file should contribute more than 3 matches (--max-count 3)."""
        matches = _tool_search_ripgrep("def ", REPO_ROOT, max_matches=_PHASE2_SEARCH_MAX_MATCHES)
        from collections import Counter
        counts = Counter(m["path"] for m in matches)
        for path, count in counts.items():
            self.assertLessEqual(count, 3, f"{path} has {count} matches, expected <= 3")

    def test_worker_runtime_in_def_search(self):
        matches = _tool_search_ripgrep("WorkerRuntime", REPO_ROOT, max_matches=_PHASE2_SEARCH_MAX_MATCHES)
        paths = {m["path"] for m in matches}
        self.assertTrue(
            any("worker_runtime" in p for p in paths),
            f"worker_runtime.py not found in paths: {list(paths)[:10]}",
        )


if __name__ == "__main__":
    unittest.main()
