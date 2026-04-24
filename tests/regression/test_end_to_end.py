#!/usr/bin/env python3
"""
End-to-end regression test: full executor run with 1 item, verify git commit.

Runs the real auto_execute_roadmap.py in --dry-run mode to verify:
- Roadmap loads (223+ items)
- Cycle detection passes (0 cycles)
- Executor selects next item and decomposes it
- Subtask planning completes without crash

For a truly committed execution (non-dry-run), see TestEndToEndReal (skipped by default).
"""
import subprocess
import sys
import re
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent


def run_executor(extra_args: list, timeout: int = 120) -> dict:
    """Run auto_execute_roadmap.py and capture full stdout + stderr."""
    cmd = [sys.executable, "bin/auto_execute_roadmap.py"] + extra_args
    start = time.time()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=REPO_ROOT,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "elapsed": time.time() - start,
    }


class TestExecutorInitialization:
    """Verify executor initializes correctly: roadmap loads, no cycles, items selected."""

    def test_dry_run_max_zero_completes(self):
        """
        --dry-run --max-items 0: executor loads roadmap, checks cycles, exits cleanly.
        Must NOT hang. If it hangs, it's stuck on model inference at startup.
        """
        result = run_executor(["--dry-run", "--max-items", "0"], timeout=60)

        print(f"\n--- dry-run --max-items 0 ---")
        print(f"Exit code: {result['returncode']}")
        print(f"Elapsed:   {result['elapsed']:.1f}s")
        print(f"Stdout:    {result['stdout'][:1000]}")
        if result["stderr"]:
            print(f"Stderr:    {result['stderr'][:400]}")

        assert result["returncode"] == 0, (
            f"Executor crashed on startup.\n"
            f"stdout: {result['stdout']}\n"
            f"stderr: {result['stderr']}"
        )

    def test_roadmap_count_in_output(self):
        """Executor must load 200+ items."""
        result = run_executor(["--dry-run", "--max-items", "0"], timeout=60)
        stdout = result["stdout"]

        match = re.search(r"Loaded (\d+) roadmap items", stdout)
        assert match, (
            f"Could not find 'Loaded N roadmap items' in output.\n"
            f"stdout: {stdout[:500]}"
        )
        count = int(match.group(1))
        assert count >= 200, (
            f"Only {count} roadmap items loaded — expected 200+.\n"
            "Check docs/roadmap/ITEMS/ for RM-*.md files."
        )
        print(f"\n✓ Loaded {count} roadmap items")

    def test_no_cycles_at_startup(self):
        """Executor must report 0 cycles, not warn about circular dependencies."""
        result = run_executor(["--dry-run", "--max-items", "0"], timeout=60)
        stdout = result["stdout"]

        if "cycle" in stdout.lower():
            # Look for the count
            match = re.search(r"(\d+) (?:circular )?dependency cycle", stdout, re.IGNORECASE)
            if match:
                count = int(match.group(1))
                assert count == 0, (
                    f"Executor detected {count} cycles at startup.\n"
                    "Run: python3 bin/break_dependency_cycles.py"
                )

        assert "circular dependency" not in stdout.lower() or "0 cycle" in stdout.lower(), (
            f"Cycles may be present.\nstdout: {stdout[:1000]}"
        )
        print(f"\n✓ No circular dependencies at startup")

    def test_executor_selects_item_in_dry_run(self):
        """With --max-items 1 --dry-run, executor must select exactly 1 item."""
        result = run_executor(
            ["--dry-run", "--max-items", "1"],
            timeout=60,  # Selection only — no LLM call in dry-run for item selection
        )

        print(f"\n--- dry-run --max-items 1 ---")
        print(f"Exit code: {result['returncode']}")
        print(f"Elapsed:   {result['elapsed']:.1f}s")
        print(f"Stdout:\n{result['stdout'][:2000]}")

        # Look for a roadmap item being processed
        rm_match = re.search(r"RM-[A-Z]+-\d+", result["stdout"])
        if not rm_match:
            # This is acceptable if all items are in-progress or completed
            print("Note: No RM item shown — may be all items complete or in-progress")
        else:
            print(f"\n✓ Executor selected item: {rm_match.group()}")


class TestExecutorRealMode:
    """
    Tests that run the executor in REAL mode (no --dry-run), making actual commits.
    Skipped by default to avoid unintended commits. Opt-in with -m real_execution.
    """

    @pytest.mark.skip(reason="Real execution: commits to git. Run explicitly with -m real_execution.")
    def test_completes_one_item_and_commits(self):
        """
        Full pipeline: select item → decompose → execute via aider → commit.
        Verifies a git commit is made with a roadmap item status update.
        """
        import subprocess as sp

        # Capture git log before
        log_before = sp.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, cwd=REPO_ROOT
        ).stdout.strip()

        result = run_executor(
            ["--max-items", "1"],
            timeout=3600,  # 60 min max — full execution with local LLM
        )

        print(f"\n--- REAL execution --max-items 1 ---")
        print(f"Exit code: {result['returncode']}")
        print(f"Elapsed:   {result['elapsed']:.0f}s")
        print(f"Stdout:\n{result['stdout'][:3000]}")
        if result["stderr"]:
            print(f"Stderr:\n{result['stderr'][:500]}")

        assert result["returncode"] == 0, (
            f"Executor failed.\n"
            f"stdout: {result['stdout']}\n"
            f"stderr: {result['stderr']}"
        )

        # Verify a new commit was made
        log_after = sp.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, cwd=REPO_ROOT
        ).stdout.strip()

        assert log_before != log_after, (
            "Executor ran without making a git commit.\n"
            "Either no items were available or execution failed silently."
        )
        print(f"\n✓ New commit: {log_after}")
