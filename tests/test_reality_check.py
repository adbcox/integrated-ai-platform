#!/usr/bin/env python3
"""
Reality check: zero mocks. Every test hits real systems.

Tests prove the production path works end-to-end:
  test_ollama_api_responds        → Ollama can generate text (not just list models)
  test_aider_can_modify_file      → Aider makes a real file change on disk
  test_executor_completes_one_item_for_real → Executor makes a real git commit

Run all three:
  pytest tests/test_reality_check.py -v -s

Run just the fast one:
  pytest tests/test_reality_check.py::test_ollama_api_responds -v -s
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ─────────────────────────────────────────────────────────────────────────────
# REALITY CHECK 1: Ollama actually generates text
# ─────────────────────────────────────────────────────────────────────────────

def test_ollama_api_responds():
    """
    Ollama must:
    1. Accept /api/tags  (model is loaded)
    2. Accept /api/generate with a trivial prompt and return non-empty content

    This catches: Ollama down, model not pulled, model stuck in loading state.
    """
    # Step 1: model is listed
    tags = subprocess.run(
        ["curl", "-sf", "http://127.0.0.1:11434/api/tags"],
        capture_output=True, text=True, timeout=10,
    )
    assert tags.returncode == 0, (
        "Ollama /api/tags failed — is Ollama running?\n"
        f"stderr: {tags.stderr}"
    )
    models = [m["name"] for m in json.loads(tags.stdout).get("models", [])]
    assert any("qwen2.5-coder" in m for m in models), (
        f"qwen2.5-coder model not in Ollama. Available: {models}\n"
        "Run: ollama pull qwen2.5-coder:7b"
    )
    print(f"\n✓ Ollama up, model found: {[m for m in models if 'qwen2.5-coder' in m]}")

    # Step 2: model generates text
    model = next(m for m in models if "qwen2.5-coder" in m)
    payload = json.dumps({
        "model": model,
        "prompt": "Reply with the single word: WORKING",
        "stream": False,
        "options": {"num_predict": 10},
    })

    start = time.time()
    generate = subprocess.run(
        ["curl", "-sf", "-X", "POST", "http://127.0.0.1:11434/api/generate",
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True, timeout=300,
    )
    elapsed = time.time() - start

    assert generate.returncode == 0, (
        f"Ollama /api/generate failed after {elapsed:.1f}s\n"
        f"stderr: {generate.stderr}"
    )

    body = json.loads(generate.stdout)
    response_text = body.get("response", "").strip()

    assert response_text, (
        f"Ollama returned empty response after {elapsed:.1f}s.\n"
        f"Full body: {generate.stdout[:500]}"
    )

    print(f"✓ Ollama generated response in {elapsed:.1f}s: {response_text!r}")
    assert body.get("done"), f"done=false — model may have been truncated: {body}"


# ─────────────────────────────────────────────────────────────────────────────
# REALITY CHECK 2: Aider makes a real file change
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.slow
def test_aider_can_modify_file():
    """
    Run real aider against a tiny canary file. Verify the file changes.

    Uses a 1-line canary file (tests/_aider_canary.py) so the model's required
    response is exactly 2 lines — impossible to truncate mid-block. Under concurrent
    Ollama load, larger files cause the model to truncate SEARCH/REPLACE blocks,
    making aider exit 0 without writing. The canary sidesteps this.

    Uses --no-auto-commits so we control cleanup (delete canary file after).
    Uses --map-tokens 0 to skip repo-map (saves ~140s per run).
    Uses --edit-format whole: model returns complete file (2 lines), reliable at any size.

    Timeout: 900s — handles Ollama queue contention. With 3 concurrent aider processes,
    each waits in queue: 3 × 217s = 651s. 900s gives a 249s margin.

    Cleanup: delete tests/_aider_canary.py.
    """
    marker = "# reality-check-test-marker"
    canary = REPO_ROOT / "tests" / "_aider_canary.py"

    # Report concurrent Ollama competition (key signal for timeout root cause)
    aider_procs = subprocess.run(
        ["pgrep", "-lf", "aider"],
        capture_output=True, text=True
    ).stdout.strip()
    if aider_procs:
        print(f"\n⚠️  Concurrent aider processes detected (may slow Ollama):")
        print(aider_procs[:400])
        print(f"  Ollama will queue requests — expect {len(aider_procs.splitlines()) * 217}s+ latency")
    else:
        print(f"\nNo competing aider processes found — expect ~217s for 7b model")

    # Create a fresh 1-line canary file (tiny so model can't truncate the response)
    if canary.exists():
        canary.unlink()
    canary.write_text("x = 1\n")
    before = canary.read_text()
    print(f"\nCanary file created: {canary.relative_to(REPO_ROOT)} — content: {before!r}")

    cmd = [
        "aider",
        "--no-auto-commits",
        "--model=ollama/qwen2.5-coder:7b",
        "--yes",
        "--no-show-model-warnings",
        "--no-auto-lint",
        "--map-tokens", "0",
        "--edit-format", "whole",
        "--message",
        f"Add the comment '{marker}' as the very first line of the file.",
        str(canary.relative_to(REPO_ROOT)),
    ]

    print(f"\nRunning aider (--edit-format whole, --map-tokens 0, timeout=900s)...")
    start = time.time()

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True, text=True,
            timeout=900,
            cwd=REPO_ROOT,
        )
        elapsed = time.time() - start
    except subprocess.TimeoutExpired as e:
        elapsed = time.time() - start
        canary.unlink(missing_ok=True)
        stdout = e.stdout.decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        competing = subprocess.run(
            ["pgrep", "-lf", "aider"], capture_output=True, text=True
        ).stdout.strip()
        print(f"\nAider TIMED OUT after {elapsed:.1f}s")
        print(f"stdout:\n{stdout[:800]}")
        print(f"stderr:\n{stderr[:400]}")
        print(f"Competing aider processes at timeout:\n{competing[:400]}")
        pytest.fail(
            f"Aider timed out after {elapsed:.1f}s (limit=900s).\n"
            f"Root cause: Ollama queue contention. Competing aider procs:\n{competing}\n\n"
            f"stdout: {stdout[-400:]}\n"
            "This is the real production failure: executor also times out under concurrent load."
        )

    print(f"\nAider exit code: {proc.returncode} (elapsed {elapsed:.1f}s, timeout=900s)")
    print(f"stdout:\n{proc.stdout[:1200]}")
    if proc.stderr:
        print(f"stderr:\n{proc.stderr[:400]}")

    # Verify the file actually changed
    after = canary.read_text() if canary.exists() else ""

    # Cleanup before asserting (so dirty state is never left behind)
    canary.unlink(missing_ok=True)
    print(f"\nCleanup: deleted {canary.relative_to(REPO_ROOT)}")

    assert proc.returncode == 0, (
        f"Aider exited {proc.returncode} after {elapsed:.1f}s.\n"
        f"stdout: {proc.stdout}\n"
        f"stderr: {proc.stderr}"
    )

    assert after != before, (
        f"Aider exited 0 in {elapsed:.1f}s but canary file was NOT modified.\n"
        f"before: {before!r}\n"
        f"after:  {after!r}\n"
        "Aider may have decided no changes were needed (check stdout above)."
    )
    assert marker in after, (
        f"Aider ran and file changed, but the marker '{marker}' is not in the file.\n"
        f"File content: {after!r}"
    )

    print(f"✓ Aider modified canary file in {elapsed:.1f}s — marker present")


# ─────────────────────────────────────────────────────────────────────────────
# REALITY CHECK 3: Executor completes an item and commits
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.slow
def test_executor_completes_one_item_for_real():
    """
    Run auto_execute_roadmap.py --max-items 1 with NO --dry-run.
    This is the production path. Verify it makes a git commit.

    WARNING: This test makes real git commits to the repository.
    Expected runtime: 5-30 minutes (decomposition + aider execution).

    Timeout: 1800s (30 min). If aider has 2 subtasks × 3 retries × 360s each = 2160s worst case.
    If this test hits the timeout, the executor is too slow for the configured timeout.
    """
    # Capture git HEAD before
    log_before = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        capture_output=True, text=True, cwd=REPO_ROOT
    ).stdout.strip()
    print(f"\nGit HEAD before: {log_before}")

    # Capture working tree state — must be clean (or at least not staged)
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=REPO_ROOT
    ).stdout.strip()
    print(f"Working tree status: {status[:300] or '(clean)'}")

    print(f"\nRunning executor --max-items 1 (real mode, no --dry-run)...")
    print(f"This will decompose a roadmap item, run aider, and commit.")
    print(f"Timeout: 1800s (30 minutes)\n")

    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, "bin/auto_execute_roadmap.py", "--max-items", "1"],
            capture_output=True, text=True,
            timeout=1800,
            cwd=REPO_ROOT,
        )
        elapsed = time.time() - start
        timed_out = False
    except subprocess.TimeoutExpired as e:
        elapsed = time.time() - start
        stdout = e.stdout.decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        print(f"\n=== EXECUTOR TIMED OUT after {elapsed:.0f}s ===")
        print(f"stdout (last 2000 chars):\n{stdout[-2000:]}")
        print(f"stderr:\n{stderr[:500]}")
        pytest.fail(
            f"Executor timed out after {elapsed:.0f}s (limit=1800s).\n"
            f"Last stdout: {stdout[-1000:]}"
        )

    print(f"\n=== Executor finished in {elapsed:.0f}s ===")
    print(f"Exit code: {result.returncode}")
    print(f"stdout (last 3000 chars):\n{result.stdout[-3000:]}")
    if result.stderr:
        print(f"stderr:\n{result.stderr[:500]}")

    # Check git HEAD after
    log_after = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        capture_output=True, text=True, cwd=REPO_ROOT
    ).stdout.strip()
    print(f"\nGit HEAD after: {log_after}")

    assert result.returncode == 0, (
        f"Executor exited {result.returncode} after {elapsed:.0f}s.\n"
        f"stdout: {result.stdout[-2000:]}\n"
        f"stderr: {result.stderr[:500]}"
    )

    assert log_before != log_after, (
        f"Executor exited 0 in {elapsed:.0f}s but made NO git commit.\n"
        f"Either no executable items exist or item was marked complete without committing.\n"
        f"stdout: {result.stdout[-2000:]}"
    )

    print(f"\n✓ Real execution complete in {elapsed:.0f}s")
    print(f"✓ New commit: {log_after}")
