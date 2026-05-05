"""tests/unit/test_router.py

Unit tests for domains/router.py task-complexity classification.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from domains.router import ExecutorType, TaskRouter, classify_task_complexity


def _router() -> TaskRouter:
    router = TaskRouter.__new__(TaskRouter)
    router.repo_root = Path.cwd()
    router.learning = None
    return router


def _write_small_py(tmp_path: Path, text: str = "def f():\n    return 1\n") -> Path:
    path = tmp_path / "sample.py"
    path.write_text(text, encoding="utf-8")
    return path


class TestTaskComplexityClassifier:
    @pytest.mark.unit
    def test_mechanical_patterns_classify_as_mechanical(self) -> None:
        assert classify_task_complexity("Add docstring to every function") == "mechanical"
        assert classify_task_complexity("Replace bare except with Exception") == "mechanical"

    @pytest.mark.unit
    def test_inference_heavy_patterns_classify_as_inference_heavy(self) -> None:
        assert classify_task_complexity("Add type hints to all function signatures") == "inference_heavy"
        assert classify_task_complexity("Extract function for long block") == "inference_heavy"

    @pytest.mark.unit
    def test_ambiguous_patterns_classify_as_ambiguous(self) -> None:
        assert classify_task_complexity("Update the file") == "ambiguous"
        assert classify_task_complexity("Add docstring and type hints") == "ambiguous"


class TestRouterComplexityRouting:
    @pytest.mark.unit
    def test_mechanical_task_routes_local_on_small_file(self, tmp_path: Path) -> None:
        path = _write_small_py(tmp_path)
        router = _router()

        route = router.classify("Add docstring to every function", [str(path)])

        assert route.executor == ExecutorType.LOCAL_AIDER
        assert route.model == "qwen2.5-coder:7b"

    @pytest.mark.unit
    def test_inference_heavy_forces_tier2_on_tiny_file(self, tmp_path: Path) -> None:
        path = _write_small_py(tmp_path)
        router = _router()

        route = router.classify("Add type hints to all function signatures", [str(path)])

        assert route.executor == ExecutorType.CLAUDE_CODE
        assert route.model == "sonnet-4"

    @pytest.mark.unit
    def test_ambiguous_pattern_preserves_existing_behavior(self, tmp_path: Path) -> None:
        path = _write_small_py(tmp_path)
        router = _router()

        route = router.classify("Update this function", [str(path)])

        assert route.executor == ExecutorType.LOCAL_AIDER
        assert route.model == "qwen2.5-coder:7b"

    @pytest.mark.unit
    def test_override_complexity_forces_tier2(self, tmp_path: Path) -> None:
        path = _write_small_py(tmp_path)
        router = _router()

        route = router.classify(
            "Add docstring to every function",
            [str(path)],
            override_complexity="inference_heavy",
        )

        assert route.executor == ExecutorType.CLAUDE_CODE
        assert route.model == "sonnet-4"
