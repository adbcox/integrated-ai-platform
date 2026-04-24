#!/usr/bin/env python3
"""
Integration test for aider: runs real aider process, captures full stdout+stderr.
Shows the ACTUAL error message instead of 'no error output'.
"""
import subprocess
import time
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
DOMAINS_MEDIA = REPO_ROOT / "domains" / "media.py"

AIDER_ENV = {
    **os.environ,
    "OLLAMA_API_BASE": "http://127.0.0.1:11434",
    "AIDER_AUTO_COMMITS": "0",
    "AIDER_YES": "1",
    "AIDER_NO_SHOW_MODEL_WARNINGS": "1",
    "AIDER_DARK_MODE": "1",
}


def run_aider(message: str, files: list, model: str = "qwen2.5-coder:7b", timeout: int = 240) -> dict:
    """Run aider and capture ALL output including stderr."""
    cmd = [
        "aider",
        "--no-auto-commits",
        f"--model=ollama/{model}",
        "--yes",
        "--no-show-model-warnings",
        "--no-auto-lint",
        "--map-tokens", "0",  # disable repo-map to avoid extra API calls
        "--message", message,
        *files,
    ]

    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            cwd=REPO_ROOT,
            env=AIDER_ENV,
        )
        elapsed = time.time() - start
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "combined": proc.stdout + "\n--- STDERR ---\n" + proc.stderr,
            "elapsed": elapsed,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as e:
        elapsed = time.time() - start
        return {
            "returncode": -1,
            "stdout": (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""),
            "stderr": (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or ""),
            "combined": f"TIMED OUT after {elapsed:.1f}s",
            "elapsed": elapsed,
            "timed_out": True,
        }


class TestAiderDirect:
    """Test aider directly with minimal configuration to identify root cause of failures."""

    def test_aider_is_available(self):
        """Verify aider binary is on PATH."""
        result = subprocess.run(["aider", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, f"aider not available: {result.stderr}"
        print(f"\naider version: {result.stdout.strip()}")

    def test_ollama_connectivity(self):
        """Verify Ollama is running and has at least one model."""
        result = subprocess.run(
            ["curl", "-s", "http://127.0.0.1:11434/api/tags"],
            capture_output=True, text=True, timeout=5
        )
        assert result.returncode == 0, "Cannot reach Ollama at 127.0.0.1:11434"
        import json
        data = json.loads(result.stdout)
        models = [m["name"] for m in data.get("models", [])]
        assert models, "No models loaded in Ollama"
        print(f"\nAvailable models: {models}")

    def test_ollama_model_inference_speed(self):
        """Measure how long qwen2.5-coder:7b takes for a single token response."""
        import json
        start = time.time()
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", "http://127.0.0.1:11434/api/chat",
             "-H", "Content-Type: application/json",
             "-d", json.dumps({
                 "model": "qwen2.5-coder:7b",
                 "messages": [{"role": "user", "content": "Reply with the single word: OK"}],
                 "stream": False,
             })],
            capture_output=True, text=True, timeout=300
        )
        elapsed = time.time() - start
        assert result.returncode == 0, f"Curl failed: {result.stderr}"
        data = json.loads(result.stdout)
        content = data.get("message", {}).get("content", "")
        print(f"\nModel response in {elapsed:.1f}s: {content[:50]!r}")
        # Warn if single inference takes >60s (will cause timeout issues in aider)
        if elapsed > 60:
            print(f"WARNING: Model inference takes {elapsed:.1f}s — aider with 300s timeout will fail "
                  f"if it makes >4 API calls")

    def test_aider_simple_task_captures_real_error(self):
        """
        Run aider on simplest possible task.
        Captures FULL stdout AND stderr so the actual error is visible.
        This is the test that was previously showing 'no error output'.
        """
        if not DOMAINS_MEDIA.exists():
            pytest.skip("domains/media.py not found")

        result = run_aider(
            message="Add a one-line comment '# media module' at the top of this file",
            files=["domains/media.py"],
            model="qwen2.5-coder:7b",
            timeout=180,
        )

        print(f"\n{'='*60}")
        print(f"EXIT CODE: {result['returncode']}")
        print(f"ELAPSED: {result['elapsed']:.1f}s")
        print(f"TIMED OUT: {result['timed_out']}")
        print(f"\n--- STDOUT ---\n{result['stdout'][:2000]}")
        print(f"\n--- STDERR ---\n{result['stderr'][:2000]}")
        print(f"{'='*60}")

        if result["timed_out"]:
            pytest.fail(
                f"Aider timed out after {result['elapsed']:.1f}s.\n"
                f"stdout: {result['stdout'][:500]}\n"
                f"stderr: {result['stderr'][:500]}"
            )

        if result["returncode"] != 0:
            pytest.fail(
                f"Aider failed with exit code {result['returncode']}.\n"
                f"FULL stdout: {result['stdout']}\n"
                f"FULL stderr: {result['stderr']}"
            )


class TestLocalCodingTask:
    """Test local_coding_task.py wrapper — the actual script used by auto_execute_roadmap."""

    def test_local_coding_task_help(self):
        """Verify the script loads and shows help."""
        result = subprocess.run(
            [sys.executable, "bin/local_coding_task.py", "--help"],
            capture_output=True, text=True, timeout=10, cwd=REPO_ROOT
        )
        assert result.returncode == 0, f"--help failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        assert "Execute a coding task" in result.stdout or "Execute a local coding task" in result.stdout

    def test_local_coding_task_simple(self):
        """
        Run local_coding_task.py with simplest possible task.
        Captures stdout AND stderr to show the real error.
        """
        if not DOMAINS_MEDIA.exists():
            pytest.skip("domains/media.py not found")

        start = time.time()
        result = subprocess.run(
            [
                sys.executable, "bin/local_coding_task.py",
                "--force-local",
                "--batch-mode",
                "--single-model",
                "--timeout", "180",
                "Add a comment: # reviewed",
                "domains/media.py",
            ],
            capture_output=True,
            text=True,
            timeout=200,
            cwd=REPO_ROOT,
        )
        elapsed = time.time() - start

        print(f"\n{'='*60}")
        print(f"EXIT CODE: {result.returncode}")
        print(f"ELAPSED: {elapsed:.1f}s")
        print(f"\n--- STDOUT (FULL) ---")
        print(result.stdout or "(empty)")
        print(f"\n--- STDERR (FULL) ---")
        print(result.stderr or "(empty)")
        print(f"{'='*60}")

        assert result.returncode == 0, (
            f"local_coding_task.py failed with exit code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
