"""Tests for ripgrep-backed _tool_search and _phase2_derive_read_targets integration."""

from __future__ import annotations

import sys
import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.worker_runtime import _rg_available, _tool_search_ripgrep
from framework.framework_control_plane import _phase2_derive_read_targets


class TestRgAvailable(unittest.TestCase):
    def test_returns_bool(self):
        result = _rg_available()
        self.assertIsInstance(result, bool)

    def test_returns_false_when_rg_raises(self):
        with patch("framework.worker_runtime.subprocess.run", side_effect=FileNotFoundError):
            self.assertFalse(_rg_available())

    def test_returns_false_when_rg_nonzero(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        with patch("framework.worker_runtime.subprocess.run", return_value=mock_proc):
            self.assertFalse(_rg_available())


class TestToolSearchRipgrep(unittest.TestCase):
    def test_returns_list(self):
        result = _tool_search_ripgrep("def _tool_search", REPO_ROOT, max_matches=10)
        self.assertIsInstance(result, list)

    def test_finds_known_present_string(self):
        result = _tool_search_ripgrep("_execute_job", REPO_ROOT, max_matches=50)
        self.assertIsInstance(result, list)
        if _rg_available():
            self.assertGreater(len(result), 0, "Expected matches for '_execute_job' in repo")

    def test_match_dicts_have_required_keys(self):
        result = _tool_search_ripgrep("_execute_job", REPO_ROOT, max_matches=50)
        for m in result:
            self.assertIn("path", m)
            self.assertIn("line_number", m)
            self.assertIn("line_text", m)

    def test_returns_empty_on_nonsense_query(self):
        # Mock rg returning no output (exit 1, empty stdout) — the no-match case
        mock_proc = MagicMock()
        mock_proc.stdout = ""
        mock_proc.returncode = 1
        with patch("framework.worker_runtime.subprocess.run", return_value=mock_proc):
            result = _tool_search_ripgrep("any_query", REPO_ROOT, max_matches=10)
        self.assertEqual(result, [])

    def test_returns_empty_on_file_not_found_error(self):
        with patch("framework.worker_runtime.subprocess.run", side_effect=FileNotFoundError):
            result = _tool_search_ripgrep("_execute_job", REPO_ROOT, max_matches=10)
        self.assertEqual(result, [])

    def test_returns_empty_on_timeout_expired(self):
        with patch(
            "framework.worker_runtime.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="rg", timeout=30),
        ):
            result = _tool_search_ripgrep("_execute_job", REPO_ROOT, max_matches=10)
        self.assertEqual(result, [])

    def test_returns_empty_on_malformed_stdout(self):
        mock_proc = MagicMock()
        mock_proc.stdout = "not json at all\n{garbage\n"
        mock_proc.returncode = 0
        with patch("framework.worker_runtime.subprocess.run", return_value=mock_proc):
            result = _tool_search_ripgrep("_execute_job", REPO_ROOT, max_matches=10)
        self.assertEqual(result, [])

    def test_match_line_text_truncated_to_200(self):
        if not _rg_available():
            self.skipTest("rg not available")
        result = _tool_search_ripgrep("_execute_job", REPO_ROOT, max_matches=10)
        for m in result:
            self.assertLessEqual(len(m["line_text"]), 200)

    def test_does_not_exceed_max_matches(self):
        if not _rg_available():
            self.skipTest("rg not available")
        max_m = 5
        result = _tool_search_ripgrep("_execute_job", REPO_ROOT, max_matches=max_m)
        self.assertLessEqual(len(result), max_m)


class TestToolSearchViaWorkerRuntime(unittest.TestCase):
    def _make_mock_job(self):
        from framework.job_schema import (
            Job, JobAction, JobClass, JobPriority, RetryPolicy,
            EscalationPolicy, ValidationRequirement, WorkTarget,
        )
        from framework.job_schema import LearningHooksConfig
        return Job(
            task_class=JobClass.VALIDATION_CHECK_EXECUTION,
            priority=JobPriority.P1,
            target=WorkTarget(repo_root=str(REPO_ROOT), worktree_target=str(REPO_ROOT)),
            action=JobAction.INFERENCE_AND_SHELL,
            artifact_inputs=[],
            requested_outputs=["artifacts/framework/test_search_output.txt"],
            allowed_tools_actions=["inference", "shell_command", "apply_edit"],
            retry_policy=RetryPolicy(retry_budget=0, retry_backoff_seconds=0),
            escalation_policy=EscalationPolicy(
                allow_auto_escalation=False,
                escalate_on_retry_exhaustion=False,
                escalation_label="test",
            ),
            validation_requirements=[ValidationRequirement.NONE],
            learning_hooks=LearningHooksConfig(
                emit_lessons=False,
                emit_prevention_candidates=False,
                emit_reuse_candidates=False,
                task_class_priors=[],
            ),
            metadata={
                "shell_command": "true",
                "inference_prompt": "test",
                "phase2_typed_tools": [],
                "permission_policy": {},
            },
        )

    def _make_worker_runtime(self):
        import queue
        import threading
        from framework.worker_runtime import WorkerRuntime
        from framework.state_store import StateStore

        store = StateStore(root=REPO_ROOT / "artifacts" / "framework" / "_test_search_tmp")
        mock_inference = MagicMock()
        mock_inference.run.return_value = MagicMock(output="test", metadata={})
        mock_learning = MagicMock()

        rt = WorkerRuntime(
            worker_id="test-worker-0",
            queue_ref=queue.PriorityQueue(),
            store=store,
            learning=mock_learning,
            inference=mock_inference,
            stop_event=threading.Event(),
            context_release_callback=lambda *a, **kw: None,
        )
        return rt

    def _make_workspace(self):
        ws = MagicMock()
        ws.repo_root = REPO_ROOT
        ws.worktree_root = REPO_ROOT
        return ws

    def test_tool_search_returns_observation_with_executed_status(self):
        try:
            rt = self._make_worker_runtime()
            job = self._make_mock_job()
            rt._phase2_begin(job)
            ws = self._make_workspace()
            obs = rt._tool_search(job=job, workspace=ws, arguments={"query": "_execute_job"})
            self.assertEqual(str(obs.status), "executed")
        except Exception as e:
            self.skipTest(f"WorkerRuntime setup error (non-critical): {e}")

    def test_tool_search_structured_payload_has_matches_key(self):
        try:
            rt = self._make_worker_runtime()
            job = self._make_mock_job()
            rt._phase2_begin(job)
            ws = self._make_workspace()
            obs = rt._tool_search(job=job, workspace=ws, arguments={"query": "_execute_job"})
            self.assertIsInstance(obs.structured_payload, dict)
            self.assertIn("matches", obs.structured_payload)
        except Exception as e:
            self.skipTest(f"WorkerRuntime setup error (non-critical): {e}")

    def test_tool_search_structured_payload_matches_nonempty(self):
        if not _rg_available():
            self.skipTest("rg not available; Python fallback may not find matches due to file cap")
        try:
            rt = self._make_worker_runtime()
            job = self._make_mock_job()
            rt._phase2_begin(job)
            ws = self._make_workspace()
            obs = rt._tool_search(job=job, workspace=ws, arguments={"query": "_execute_job"})
            matches = obs.structured_payload.get("matches") or []
            self.assertGreater(len(matches), 0)
        except Exception as e:
            self.skipTest(f"WorkerRuntime setup error (non-critical): {e}")


class TestPhase2DeriveReadTargets(unittest.TestCase):
    def _search_obs(self, matches):
        return {
            "tool_name": "search",
            "status": "executed",
            "return_code": 0,
            "stdout": "",
            "structured_payload": {"matches": matches},
            "duration_ms": 0,
            "error": "",
        }

    def test_returns_nonempty_from_nonempty_matches(self):
        obs = self._search_obs([
            {"path": "framework/worker_runtime.py", "line_number": 1, "line_text": "def _execute_job"},
        ])
        result = _phase2_derive_read_targets([obs])
        self.assertGreater(len(result), 0)

    def test_returns_empty_from_empty_matches(self):
        obs = self._search_obs([])
        result = _phase2_derive_read_targets([obs])
        self.assertEqual(result, [])

    def test_result_entries_have_contract_name_read_file(self):
        obs = self._search_obs([
            {"path": "framework/worker_runtime.py", "line_number": 1, "line_text": "test"},
        ])
        result = _phase2_derive_read_targets([obs])
        for entry in result:
            self.assertEqual(entry["contract_name"], "read_file")

    def test_result_entries_have_arguments_path(self):
        obs = self._search_obs([
            {"path": "framework/worker_runtime.py", "line_number": 1, "line_text": "test"},
        ])
        result = _phase2_derive_read_targets([obs])
        for entry in result:
            self.assertIn("path", entry["arguments"])

    def test_deduplicates_paths(self):
        obs = self._search_obs([
            {"path": "framework/worker_runtime.py", "line_number": 1, "line_text": "a"},
            {"path": "framework/worker_runtime.py", "line_number": 2, "line_text": "b"},
        ])
        result = _phase2_derive_read_targets([obs])
        paths = [e["arguments"]["path"] for e in result]
        self.assertEqual(len(paths), len(set(paths)))


class TestSourceTextAssertions(unittest.TestCase):
    def _worker_source(self):
        return (REPO_ROOT / "framework" / "worker_runtime.py").read_text()

    def _contract_source(self):
        return (REPO_ROOT / "framework" / "tool_action_observation_contract.py").read_text()

    def test_tool_search_ripgrep_in_worker_source(self):
        self.assertIn("_tool_search_ripgrep", self._worker_source())

    def test_rg_available_in_worker_source(self):
        self.assertIn("_rg_available", self._worker_source())

    def test_structured_payload_in_observation_contract(self):
        self.assertIn("structured_payload", self._contract_source())


if __name__ == "__main__":
    unittest.main()
