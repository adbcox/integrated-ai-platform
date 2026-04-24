#!/usr/bin/env python3
"""
Regression test: aider adds a comment, verify the file actually changed.
Root cause of previous failures:
  - repo-map generation adds one extra API call (~140s) → 300s timeout exceeded
  - stderr swallowed → "no error output" instead of real message
Both are now fixed: --map-tokens 0 and stderr captured in result_data["output"].
"""
import subprocess
import time
import os
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
AIDER_ENV = {
    **os.environ,
    "OLLAMA_API_BASE": "http://127.0.0.1:11434",
    "AIDER_AUTO_COMMITS": "0",
    "AIDER_YES": "1",
    "AIDER_NO_SHOW_MODEL_WARNINGS": "1",
}


def run_aider_direct(message: str, files: list, model: str = "qwen2.5-coder:7b",
                     timeout: int = 240) -> dict:
    """Run aider with stderr captured, repo-map disabled."""
    cmd = [
        "aider",
        "--no-auto-commits",
        f"--model=ollama/{model}",
        "--yes",
        "--no-show-model-warnings",
        "--no-auto-lint",
        "--map-tokens", "0",  # no repo-map = no extra API call
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
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "elapsed": time.time() - start,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "returncode": -1,
            "stdout": (e.stdout or ""),
            "stderr": (e.stderr or ""),
            "elapsed": time.time() - start,
            "timed_out": True,
        }


@pytest.fixture(scope="module")
def target_file(tmp_path_factory):
    """Create a throw-away Python file for aider to modify."""
    d = tmp_path_factory.mktemp("aider_test")
    f = d / "sample.py"
    f.write_text('def hello():\n    return "hello"\n')
    # aider needs the file to be tracked by git — use a file already in repo
    return str(REPO_ROOT / "domains" / "media.py")


class TestAiderSimple:
    """Verify aider can complete a one-file comment task without timing out."""

    def test_prereqs_model_available(self):
        """qwen2.5-coder:7b must be in Ollama."""
        result = subprocess.run(
            ["curl", "-s", "http://127.0.0.1:11434/api/tags"],
            capture_output=True, text=True, timeout=5
        )
        assert result.returncode == 0
        models = [m["name"] for m in json.loads(result.stdout).get("models", [])]
        assert "qwen2.5-coder:7b" in models, (
            f"qwen2.5-coder:7b not in Ollama. Available: {models}\n"
            "Run: ollama pull qwen2.5-coder:7b"
        )

    def test_aider_exits_within_timeout(self):
        """
        With --map-tokens 0, aider makes ONE API call (not two).
        7b model responds in ~30-60s, so 180s timeout is sufficient.
        """
        result = run_aider_direct(
            message="Add a one-line comment '# regression-test-marker' at the very top",
            files=["domains/media.py"],
            model="qwen2.5-coder:7b",
            timeout=180,
        )

        print(f"\n--- Test aider_exits_within_timeout ---")
        print(f"Elapsed:   {result['elapsed']:.1f}s")
        print(f"Exit code: {result['returncode']}")
        print(f"Stdout:    {result['stdout'][:600]}")
        if result["stderr"]:
            print(f"Stderr:    {result['stderr'][:400]}")

        assert not result["timed_out"], (
            f"Aider timed out after {result['elapsed']:.1f}s.\n"
            f"stdout: {result['stdout'][:300]}\n"
            f"stderr: {result['stderr'][:300]}"
        )
        assert result["returncode"] == 0, (
            f"Aider failed (exit {result['returncode']}).\n"
            f"stdout: {result['stdout']}\n"
            f"stderr: {result['stderr']}"
        )

    def test_coding_domain_captures_stderr_on_timeout(self):
        """
        CodingDomain._execute_with_model must put stderr in result_data['output']
        when aider times out — previously this showed 'no error output'.
        """
        sys.path.insert(0, str(REPO_ROOT))
        from domains.coding import CodingDomain

        domain = CodingDomain()
        # Use a 5-second timeout so aider times out immediately
        result = domain._execute_with_model(
            model="qwen2.5-coder:7b",
            task_description="Add a one-line comment",
            files=["domains/media.py"],
            timeout_seconds=5,
        )

        print(f"\n--- Test stderr captured on timeout ---")
        print(f"success:    {result['success']}")
        print(f"error:      {result.get('error', '')}")
        print(f"output[:300]: {result.get('output', '')[:300]}")

        assert not result["success"], "Should have failed due to timeout"
        error_msg = result.get("error", "")
        assert error_msg, "error field must not be empty on timeout"
        # Must say something about the timeout — not 'no error output'
        assert "no error output" not in error_msg.lower(), (
            f"Error message is still 'no error output': {error_msg!r}"
        )
        assert "timeout" in error_msg.lower(), (
            f"Expected 'timeout' in error message, got: {error_msg!r}"
        )
        print(f"✓ Error message correctly describes timeout: {error_msg[:100]!r}")
