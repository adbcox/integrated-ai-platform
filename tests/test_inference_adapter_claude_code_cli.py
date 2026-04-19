"""Tests for PHASE3-INFERENCE-CLAUDE-CLI-1: ClaudeCodeCLIInferenceAdapter."""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.inference_adapter import (
    ClaudeCodeCLIInferenceAdapter,
    InferenceRequest,
    InferenceResponse,
    build_inference_adapter,
)
from framework.backend_profiles import get_backend_profile


def _profile():
    return get_backend_profile("mac_local")


def _request(prompt: str = "test prompt") -> InferenceRequest:
    return InferenceRequest(job_id="j1", prompt=prompt)


class TestClaudeCodeCLIAdapter(unittest.TestCase):
    def _adapter(self) -> ClaudeCodeCLIInferenceAdapter:
        return ClaudeCodeCLIInferenceAdapter(profile=_profile())

    def _mock_proc(self, stdout: str = "output text", returncode: int = 0):
        proc = MagicMock()
        proc.stdout = stdout
        proc.returncode = returncode
        return proc

    def test_returns_inference_response(self):
        adapter = self._adapter()
        with patch("subprocess.run", return_value=self._mock_proc("some output")):
            result = adapter.run(_request())
        self.assertIsInstance(result, InferenceResponse)

    def test_output_text_from_stdout(self):
        adapter = self._adapter()
        with patch("subprocess.run", return_value=self._mock_proc("hello world")):
            result = adapter.run(_request())
        self.assertEqual(result.output_text, "hello world")

    def test_backend_name_is_claude_code_cli(self):
        adapter = self._adapter()
        with patch("subprocess.run", return_value=self._mock_proc("x")):
            result = adapter.run(_request())
        self.assertEqual(result.backend, "claude_code_cli")

    def test_fallback_on_nonzero_returncode(self):
        adapter = self._adapter()
        with patch("subprocess.run", return_value=self._mock_proc("", returncode=1)):
            result = adapter.run(_request())
        self.assertNotEqual(result.backend, "claude_code_cli")

    def test_fallback_on_empty_stdout(self):
        adapter = self._adapter()
        with patch("subprocess.run", return_value=self._mock_proc("")):
            result = adapter.run(_request())
        self.assertNotEqual(result.backend, "claude_code_cli")

    def test_fallback_on_subprocess_exception(self):
        adapter = self._adapter()
        with patch("subprocess.run", side_effect=FileNotFoundError("claude not found")):
            result = adapter.run(_request())
        self.assertIsInstance(result, InferenceResponse)

    def test_fallback_on_timeout(self):
        import subprocess as sp
        adapter = self._adapter()
        with patch("subprocess.run", side_effect=sp.TimeoutExpired("claude", 120)):
            result = adapter.run(_request())
        self.assertIsInstance(result, InferenceResponse)

    def test_empty_prompt_falls_back(self):
        adapter = self._adapter()
        with patch("subprocess.run") as mock_run:
            result = adapter.run(_request(prompt=""))
        mock_run.assert_not_called()
        self.assertIsInstance(result, InferenceResponse)

    def test_metadata_contains_job_id(self):
        adapter = self._adapter()
        with patch("subprocess.run", return_value=self._mock_proc("x")):
            result = adapter.run(InferenceRequest(job_id="job-42", prompt="q"))
        self.assertEqual(result.metadata.get("job_id"), "job-42")

    def test_claude_is_called_with_print_flag(self):
        adapter = self._adapter()
        with patch("subprocess.run", return_value=self._mock_proc("x")) as mock_run:
            adapter.run(_request("my prompt"))
        cmd = mock_run.call_args[0][0]
        self.assertIn("-p", cmd)

    def test_dangerously_skip_permissions_flag_present(self):
        adapter = self._adapter()
        with patch("subprocess.run", return_value=self._mock_proc("x")) as mock_run:
            adapter.run(_request())
        cmd = mock_run.call_args[0][0]
        self.assertIn("--dangerously-skip-permissions", cmd)

    def test_output_format_text_flag_present(self):
        adapter = self._adapter()
        with patch("subprocess.run", return_value=self._mock_proc("x")) as mock_run:
            adapter.run(_request())
        cmd = mock_run.call_args[0][0]
        self.assertIn("text", cmd)


class TestBuildInferenceAdapterClaudeCLI(unittest.TestCase):
    def test_build_returns_claude_code_cli_adapter(self):
        adapter = build_inference_adapter(backend_profile="mac_local", mode="claude_code_cli")
        self.assertIsInstance(adapter, ClaudeCodeCLIInferenceAdapter)

    def test_build_heuristic_still_works(self):
        from framework.inference_adapter import LocalHeuristicInferenceAdapter
        adapter = build_inference_adapter(backend_profile="mac_local", mode="heuristic")
        self.assertIsInstance(adapter, LocalHeuristicInferenceAdapter)

    def test_build_claude_code_cli_has_profile(self):
        adapter = build_inference_adapter(backend_profile="mac_local", mode="claude_code_cli")
        self.assertIsNotNone(adapter.profile)


class TestSourceTextAssertions(unittest.TestCase):
    def _src(self) -> str:
        return (REPO_ROOT / "framework" / "inference_adapter.py").read_text()

    def test_claude_code_cli_adapter_in_source(self):
        self.assertIn("ClaudeCodeCLIInferenceAdapter", self._src())

    def test_claude_code_cli_mode_in_build_function(self):
        src = self._src()
        self.assertIn('mode == "claude_code_cli"', src)

    def test_dangerously_skip_permissions_in_source(self):
        self.assertIn("--dangerously-skip-permissions", self._src())


if __name__ == "__main__":
    unittest.main()
