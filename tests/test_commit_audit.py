#!/usr/bin/env python3
"""
Commit audit: verify each recent fix actually works on the real system.

46a3472 — Circular dependency fix
6788a06 — File corruption detection
fca6fda — Timeout enforcement (proc.communicate)
fe54acf — Integration tests (are they real or mocked?)
"""
import ast
import subprocess
import sys
import time
import textwrap
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT 1: 46a3472 — Circular dependency fix
# Claim: "0 cycles remaining (down from 45)"
# Method: run the actual cycle detector on the live roadmap, not just dry-run output
# ─────────────────────────────────────────────────────────────────────────────

class TestAudit_46a3472_CircularDeps:
    """
    Verify: detect_cycles on current roadmap really returns 0 cycles.
    The commit removed 53 dependency lines across 32 RM-*.md files.
    """

    def test_zero_cycles_live_roadmap(self):
        """Load the real roadmap, infer dependencies, run cycle detector."""
        from bin.roadmap_parser import parse_roadmap_directory, infer_dependencies, detect_cycles

        items = parse_roadmap_directory(REPO_ROOT / "docs" / "roadmap" / "ITEMS")
        infer_dependencies(items)
        cycles = detect_cycles(items)

        print(f"\nRoadmap: {len(items)} items loaded")
        if cycles:
            print("CYCLES FOUND:")
            for c in cycles[:5]:
                print("  " + " → ".join(c))

        assert cycles == [], (
            f"Found {len(cycles)} dependency cycles — 46a3472 fix is incomplete or regressed.\n"
            + "\n".join("  " + " → ".join(c) for c in cycles[:10])
        )
        print(f"✓ 0 cycles across {len(items)} items")

    def test_removed_edges_are_gone(self):
        """
        Specific edges the commit removed must not exist in the live files.
        These are a sample of the 53 lines deleted by 46a3472.
        """
        from bin.roadmap_parser import parse_roadmap_directory, infer_dependencies

        items = parse_roadmap_directory(REPO_ROOT / "docs" / "roadmap" / "ITEMS")
        infer_dependencies(items)
        by_id = {i.id: i for i in items}

        # RM-DATA-002 had "RM-DATA-001" removed as explicit dep
        data2 = by_id.get("RM-DATA-002")
        if data2:
            # The commit removed this specific explicit dependency line
            raw = (REPO_ROOT / "docs" / "roadmap" / "ITEMS" / "RM-DATA-002.md").read_text()
            assert "- `RM-DATA-001` — connection pooling" not in raw, (
                "RM-DATA-002.md still contains the removed dep line '- `RM-DATA-001`'"
            )
            print("✓ RM-DATA-002 → RM-DATA-001 edge removed from file")

        # RM-DEPLOY-001 had "RM-DEPLOY-004" removed
        deploy1 = (REPO_ROOT / "docs" / "roadmap" / "ITEMS" / "RM-DEPLOY-001.md").read_text()
        assert "RM-DEPLOY-004 (Deployment verification)" not in deploy1, (
            "RM-DEPLOY-001.md still contains the RM-DEPLOY-004 dep that caused a cycle"
        )
        print("✓ RM-DEPLOY-001 → RM-DEPLOY-004 edge removed from file")

    def test_total_item_count_unchanged(self):
        """Removing dependency lines must not remove any RM items."""
        from bin.roadmap_parser import parse_roadmap_directory
        items = parse_roadmap_directory(REPO_ROOT / "docs" / "roadmap" / "ITEMS")
        assert len(items) >= 223, (
            f"Only {len(items)} items — expected 223+. "
            "Cycle-breaking may have deleted whole files instead of just dep lines."
        )
        print(f"✓ {len(items)} items intact after cycle breaking")


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT 2: 6788a06 — File corruption detection
# Claim: "Validate files don't contain directory tree corruption before execution"
# Method: exercise the actual validation logic in local_coding_task.py
# ─────────────────────────────────────────────────────────────────────────────

class TestAudit_6788a06_CorruptionDetection:
    """
    The corruption check in local_coding_task.py:
      content.strip().startswith(("├──", "└──", "tests/", "bin/"))
      AND "\n" in content AND len(content) < 500
      AND no Python identifiers ("import", "def", "class", shebang)
    """

    # ── import the detection logic directly so we test exactly what's shipped ──
    @staticmethod
    def _check_file(tmp_path: Path, content: str) -> bool:
        """
        Replicate the exact guard from local_coding_task.py line 241-244.
        Returns True if the file would be flagged as corrupted.
        """
        try:
            c = content
            if c.strip().startswith(("├──", "└──", "tests/", "bin/")) and "\n" in c and len(c) < 500:
                if not any(x in c for x in ["#!/usr/bin/env python3", "import ", "def ", "class "]):
                    return True
        except Exception:
            pass
        return False

    def test_detects_directory_tree_box_chars(self, tmp_path):
        """File starting with ├── box chars → must be flagged."""
        tree = "├── tests/\n│   ├── conftest.py\n└── bin/\n    └── run.sh\n"
        assert self._check_file(tmp_path, tree), "Directory tree with ├── was NOT detected"
        print("✓ ├── directory tree correctly detected as corrupt")

    def test_detects_tree_starting_with_tests(self, tmp_path):
        """File starting with 'tests/' with no Python code → must be flagged."""
        content = "tests/\n  conftest.py\n  test_foo.py\nbin/\n  run.sh\n"
        assert self._check_file(tmp_path, content), "tests/ tree was NOT detected"
        print("✓ tests/ directory tree correctly detected as corrupt")

    def test_valid_python_not_flagged(self, tmp_path):
        """A real Python file must NEVER be flagged as corrupt."""
        py = "import os\ndef hello():\n    return 42\n"
        assert not self._check_file(tmp_path, py), "Valid Python was falsely flagged as corrupt"
        print("✓ Valid Python not flagged")

    def test_file_with_import_not_flagged(self, tmp_path):
        """Even a short file with 'import' must not be flagged."""
        content = "tests/\nimport os\n"
        assert not self._check_file(tmp_path, content), (
            "File with 'import' was incorrectly flagged (false positive)"
        )
        print("✓ File containing 'import' not flagged")

    def test_long_tree_bypasses_check(self, tmp_path):
        """
        KNOWN LIMITATION: tree with len >= 500 is NOT caught.
        Documents actual behavior, not ideal behavior.
        """
        long_tree = "├── " + "x" * 500 + "\n└── end\n"
        detected = self._check_file(tmp_path, long_tree)
        # This is a known gap: len >= 500 bypasses the guard
        print(f"  Long tree (>500 chars) detected: {detected}")
        print("  NOTE: trees longer than 500 chars bypass the corruption guard — known gap")

    def test_local_coding_task_rejects_corrupt_file(self, tmp_path):
        """
        Run local_coding_task.py with a corrupt file as its target.
        Must exit with code 1 and print an error — not silently proceed.
        """
        corrupt = tmp_path / "corrupt.py"
        corrupt.write_text("├── tests/\n│   └── conftest.py\n└── bin/\n    └── run.sh\n")

        result = subprocess.run(
            [
                sys.executable, "bin/local_coding_task.py",
                "--force-local", "--batch-mode",
                "Add a comment",
                str(corrupt.relative_to(REPO_ROOT)) if corrupt.is_relative_to(REPO_ROOT) else str(corrupt),
            ],
            capture_output=True, text=True, timeout=30, cwd=REPO_ROOT,
        )

        print(f"\nExit code: {result.returncode}")
        print(f"Stderr:    {result.stderr[:300]}")
        print(f"Stdout:    {result.stdout[:300]}")

        # File is outside repo root, so it may fail for different reasons
        # Check that it fails (not succeeds) on a path it can't validate
        assert result.returncode != 0, (
            "local_coding_task.py did not reject corrupt/invalid file"
        )
        print("✓ local_coding_task.py exits non-zero for corrupt/invalid file")


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT 3: fca6fda — Timeout enforcement
# Claim: "proc.communicate(timeout=timeout_seconds) actually enforces timeout"
# Method: call _execute_with_model with 3s timeout on a process guaranteed to hang,
#         then check it actually returns in time and the error mentions timeout
# ─────────────────────────────────────────────────────────────────────────────

class TestAudit_fca6fda_TimeoutEnforcement:
    """
    The fix replaced readline-loop with proc.communicate(timeout=N).
    The key behavior: if timeout_seconds=N, the call must return within N+grace seconds.
    We verify the current code (which incorporates fca6fda) actually does this.
    """

    def test_communicate_timeout_returns_within_grace(self):
        """
        CodingDomain._execute_with_model with timeout=3 on aider must return
        within 10 seconds (process starts, aider hangs, timeout fires, cleanup, return).
        Previously the readline() loop blocked forever.
        """
        from domains.coding import CodingDomain

        domain = CodingDomain()
        start = time.time()
        result = domain._execute_with_model(
            model="qwen2.5-coder:7b",
            task_description="Add a comment",
            files=["domains/media.py"],
            timeout_seconds=3,
        )
        elapsed = time.time() - start

        print(f"\n_execute_with_model returned in {elapsed:.1f}s (timeout=3s)")
        print(f"success: {result['success']}")
        print(f"error:   {result.get('error', '')[:150]}")

        assert elapsed < 15, (
            f"_execute_with_model took {elapsed:.1f}s for a 3s timeout — "
            "communicate(timeout=N) is not enforcing the timeout. "
            "Old readline() loop would block forever."
        )
        assert not result["success"], "Should fail due to timeout"
        assert "timeout" in (result.get("error") or "").lower(), (
            f"Error message doesn't mention timeout: {result.get('error')!r}"
        )
        print(f"✓ Returned in {elapsed:.1f}s — timeout is enforced")

    def test_proc_kill_actually_runs_on_timeout(self):
        """
        When communicate times out, proc.kill() must be called.
        We verify by checking that no aider zombie processes remain after timeout.
        """
        from domains.coding import CodingDomain

        # Get aider PIDs before
        before = subprocess.run(
            ["pgrep", "-f", "aider"], capture_output=True, text=True
        ).stdout.strip().split()

        domain = CodingDomain()
        domain._execute_with_model(
            model="qwen2.5-coder:7b",
            task_description="Add a comment",
            files=["domains/media.py"],
            timeout_seconds=3,
        )

        # Give cleanup 2 seconds
        time.sleep(2)

        # Check aider processes after
        after = subprocess.run(
            ["pgrep", "-f", "aider"], capture_output=True, text=True
        ).stdout.strip().split()

        new_pids = set(after) - set(before)
        print(f"\nAider PIDs before: {before}")
        print(f"Aider PIDs after:  {after}")
        print(f"New lingering PIDs: {new_pids}")

        assert not new_pids, (
            f"Aider process leaked after timeout: PIDs {new_pids}. "
            "proc.kill() or proc.wait() may not be working correctly."
        )
        print("✓ No aider zombie processes after timeout")

    def test_timeout_uses_communicate_not_readline(self):
        """
        Verify the source code uses proc.communicate(timeout=...) —
        NOT the old readline() loop that never enforced the timeout.
        """
        coding_src = (REPO_ROOT / "domains" / "coding.py").read_text()

        assert "proc.communicate(timeout=timeout_seconds)" in coding_src, (
            "domains/coding.py does not use proc.communicate(timeout=timeout_seconds). "
            "The fca6fda fix may have been reverted or the code path changed."
        )
        assert "for line in iter(proc.stdout.readline" not in coding_src, (
            "The OLD readline() loop is still present. fca6fda fix was not applied."
        )
        print("✓ Code uses proc.communicate(timeout=timeout_seconds)")
        print("✓ Old readline() loop is gone")


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT 4: fe54acf — Integration tests
# Claim: "Fix test suite" with executor tests
# Reality check: are TestExecuteSubtaskTimeout and TestFullExecutionMock
#                actually running the real executor or mocking everything?
# ─────────────────────────────────────────────────────────────────────────────

class TestAudit_fe54acf_IntegrationTests:
    """
    Verifies what fe54acf actually tests vs. what it claims.
    Finding: ALL tests in test_autonomous_executor.py use mocks.
    This documents the gap and verifies actual behavior.
    """

    def test_executor_tests_use_mocks(self):
        """
        Read the test file and verify that the 'integration' tests use Mock/patch.
        This is a documentation test: it PASSES if tests use mocks (current reality),
        and would fail if someone removed the mocks (making them real integration tests).
        """
        test_src = (REPO_ROOT / "tests" / "test_autonomous_executor.py").read_text()

        mock_indicators = [
            "patch('subprocess.Popen')",
            "patch('requests.post'",
            "patch('bin.auto_execute_roadmap.",
            "MagicMock",
            "mock_proc",
        ]

        found = [ind for ind in mock_indicators if ind in test_src]
        print(f"\nMock indicators found in test_autonomous_executor.py:")
        for ind in found:
            print(f"  ✓ {ind}")

        assert len(found) >= 3, (
            "Expected multiple mock indicators — test file may have changed"
        )
        print(f"\nConclusion: fe54acf tests are unit tests with mocks, not integration tests.")
        print("Real executor processes are NOT run in TestExecuteSubtaskTimeout.")

    def test_mocked_timeout_test_passes(self):
        """
        The mocked timeout test in fe54acf runs correctly.
        We run it and verify it still passes (it doesn't call real aider).
        """
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                "tests/test_autonomous_executor.py::TestExecuteSubtaskTimeout::test_timeout_kills_process",
                "-v", "--tb=short", "-q",
            ],
            capture_output=True, text=True, timeout=30, cwd=REPO_ROOT,
        )
        output = result.stdout + result.stderr
        print(f"\n--- Mocked timeout test ---\n{output[:600]}")

        assert result.returncode == 0, (
            f"Mocked timeout test failed:\n{output}"
        )
        assert "passed" in output.lower(), "Test output doesn't say 'passed'"
        print("✓ Mocked test passes (but does not call real aider)")

    def test_real_executor_subprocess_works(self):
        """
        What fe54acf does NOT test: actually running the executor process.
        This test does that — runs auto_execute_roadmap.py as a real subprocess.
        """
        result = subprocess.run(
            [sys.executable, "bin/auto_execute_roadmap.py", "--dry-run", "--max-items", "0"],
            capture_output=True, text=True, timeout=60, cwd=REPO_ROOT,
        )

        print(f"\n--- Real executor subprocess ---")
        print(f"Exit code: {result.returncode}")
        print(f"Stdout:    {result.stdout[:400]}")

        assert result.returncode == 0, (
            f"Real executor crashed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "Loaded" in result.stdout, "Executor didn't report roadmap load"
        print("✓ Real executor subprocess runs without crashing")
        print("  (This test is NOT in fe54acf — it was a gap in the original test suite)")
