#!/usr/bin/env python3
"""
Regression test: Ollama decomposes a roadmap item into subtasks.
Calls the Ollama API directly (no aider), verifies quality of decomposition output.
"""
import json
import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent


def ollama_chat(model: str, prompt: str, timeout: int = 300) -> dict:
    """Call Ollama chat API and return parsed response."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", "http://127.0.0.1:11434/api/chat",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=timeout,
    )
    assert result.returncode == 0, f"curl failed: {result.stderr}"
    data = json.loads(result.stdout)
    return {
        "content": data.get("message", {}).get("content", ""),
        "total_duration_s": data.get("total_duration", 0) / 1e9,
        "raw": data,
    }


DECOMPOSE_PROMPT = """You are a software engineering assistant.
Break down this task into 3-5 concrete, actionable implementation subtasks.
Each subtask should name a specific file and action.

Task: Implement structured logging framework with JSON output and contextual fields.
Category: Observability

Return ONLY a JSON array of strings, like:
["Create framework/structured_logger.py with JSON formatter class", "Add log level filtering to structured_logger.py", "Write tests/test_logging.py with unit tests for JSON output"]
"""


class TestDecomposition:
    """Verify Ollama generates valid, useful subtask decompositions."""

    def test_ollama_returns_json_array(self):
        """Ollama must return a parseable JSON array of subtask strings."""
        start = time.time()
        resp = ollama_chat("qwen2.5-coder:7b", DECOMPOSE_PROMPT, timeout=300)
        elapsed = time.time() - start

        print(f"\n--- Decomposition test ---")
        print(f"Model response time: {elapsed:.1f}s")
        print(f"Content: {resp['content'][:800]}")

        assert resp["content"], "Ollama returned empty content"

        # Extract JSON array from the response
        content = resp["content"].strip()
        # Handle markdown code block wrapping
        if "```" in content:
            import re
            match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
            if match:
                content = match.group(1)
        # Find raw JSON array
        import re
        arr_match = re.search(r'\[.*\]', content, re.DOTALL)
        assert arr_match, (
            f"No JSON array found in response.\nFull content: {resp['content']}"
        )

        try:
            subtasks = json.loads(arr_match.group())
        except json.JSONDecodeError as e:
            pytest.fail(f"Failed to parse JSON array: {e}\nContent: {arr_match.group()}")

        assert isinstance(subtasks, list), f"Expected list, got {type(subtasks)}"
        assert len(subtasks) >= 2, (
            f"Expected at least 2 subtasks, got {len(subtasks)}: {subtasks}"
        )

        for task in subtasks:
            assert isinstance(task, str), f"Subtask must be a string, got {type(task)}: {task}"
            assert len(task) > 10, f"Subtask too short to be useful: {task!r}"

        print(f"\nGenerated {len(subtasks)} subtasks:")
        for i, t in enumerate(subtasks, 1):
            print(f"  [{i}] {t}")

    def test_subtasks_reference_files(self):
        """Good subtasks should mention specific file paths."""
        resp = ollama_chat("qwen2.5-coder:7b", DECOMPOSE_PROMPT, timeout=300)
        content = resp["content"]

        import re
        arr_match = re.search(r'\[.*\]', content, re.DOTALL)
        if not arr_match:
            pytest.skip("No JSON array — covered by test_ollama_returns_json_array")

        subtasks = json.loads(arr_match.group())
        file_pattern = re.compile(r'\b\w+/\w+\.py\b')
        tasks_with_files = [t for t in subtasks if file_pattern.search(t)]

        print(f"\nTasks referencing files: {len(tasks_with_files)}/{len(subtasks)}")
        for t in tasks_with_files:
            print(f"  ✓ {t}")

        assert len(tasks_with_files) >= 1, (
            f"No subtasks mention file paths — decomposition too vague.\n"
            f"Subtasks: {subtasks}"
        )

    def test_roadmap_parser_loads_items(self):
        """Roadmap parser must load 250+ items for decomposition to have input."""
        import sys
        sys.path.insert(0, str(REPO_ROOT))
        from bin.roadmap_parser import parse_roadmap_directory

        items = parse_roadmap_directory(REPO_ROOT / "docs" / "roadmap" / "ITEMS")
        assert len(items) >= 200, f"Expected 200+ roadmap items, got {len(items)}"

        accepted = [i for i in items if i.status == "Accepted"]
        assert accepted, "No Accepted items to decompose — executor has no work"
        print(f"\n{len(items)} total items, {len(accepted)} Accepted (ready to execute)")
