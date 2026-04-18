"""Tests for WorkerRuntime._tool_run_tests typed tool body."""

from __future__ import annotations

import queue
import tempfile
import threading
import unittest
from pathlib import Path

from framework.backend_profiles import get_backend_profile
from framework.inference_adapter import LocalHeuristicInferenceAdapter
from framework.job_schema import (
    EscalationPolicy,
    Job,
    JobAction,
    JobClass,
    JobPriority,
    RetryPolicy,
    WorkTarget,
)
from framework.learning_hooks import LearningHooks
from framework.permission_engine import PermissionEngine
from framework.sandbox import LocalSandboxRunner
from framework.state_store import StateStore
from framework.tool_action_observation_contract import (
    ToolContractName,
    ToolContractStatus,
)
from framework.worker_runtime import WorkerRuntime, _phase2_run_tests_head_allowed
from framework.workspace import WorkspaceController


def _make_runtime(tmp_root: Path, *, allowed_tools: list[str]) -> tuple[WorkerRuntime, Job]:
    artifact_root = tmp_root / "artifacts"
    artifact_root.mkdir(parents=True, exist_ok=True)
    repo_root = tmp_root / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)

    store = StateStore(artifact_root)
    learning = LearningHooks(
        store=store,
        learning_latest_path=artifact_root / "learning" / "latest.json",
    )
    profile = get_backend_profile("mac_local")
    inference = LocalHeuristicInferenceAdapter(profile=profile)
    workspace_controller = WorkspaceController(artifact_root)
    sandbox_runner = LocalSandboxRunner()
    permission_engine = PermissionEngine()

    job = Job(
        task_class=JobClass.VALIDATION_CHECK_EXECUTION,
        priority=JobPriority.P2,
        target=WorkTarget(repo_root=str(repo_root), worktree_target=str(repo_root)),
        action=JobAction.INFERENCE_ONLY,
        requested_outputs=[],
        allowed_tools_actions=allowed_tools,
        retry_policy=RetryPolicy(retry_budget=0, retry_backoff_seconds=0),
        escalation_policy=EscalationPolicy(allow_auto_escalation=False, escalate_on_retry_exhaustion=False),
        validation_requirements=[],
        metadata={"session_id": "test-run-tests"},
        job_id="test-run-tests-job",
    )

    stop_event = threading.Event()
    runtime = WorkerRuntime(
        worker_id="test-run-tests-worker",
        queue_ref=queue.PriorityQueue(),
        inference=inference,
        store=store,
        learning=learning,
        stop_event=stop_event,
        context_release_callback=lambda _j: None,
        permission_engine=permission_engine,
        workspace_controller=workspace_controller,
        sandbox_runner=sandbox_runner,
    )
    runtime._phase2_begin(job)
    return runtime, job


class TestToolRunTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="p2_run_tests_")
        self._tmp_path = Path(self._tmp)

    def _workspace(self, runtime: WorkerRuntime, job: Job):
        return runtime._workspace_controller.for_job(job)

    def test_run_tests_allowed_head_recognized(self):
        self.assertTrue(_phase2_run_tests_head_allowed(["python3", "-m", "unittest", "--help"]))
        self.assertTrue(_phase2_run_tests_head_allowed(["python3", "-m", "pytest"]))
        self.assertTrue(_phase2_run_tests_head_allowed(["pytest", "tests/"]))
        self.assertTrue(_phase2_run_tests_head_allowed(["make", "test"]))
        self.assertTrue(_phase2_run_tests_head_allowed(["make", "check"]))
        self.assertTrue(_phase2_run_tests_head_allowed(["make", "quick"]))
        self.assertFalse(_phase2_run_tests_head_allowed(["ls", "-la"]))
        self.assertFalse(_phase2_run_tests_head_allowed([]))

    def test_run_tests_success(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["run_tests"])
        workspace = self._workspace(runtime, job)

        obs = runtime._tool_run_tests(
            job=job, workspace=workspace,
            arguments={"command": "python3 -m unittest --help"},
        )

        self.assertEqual(obs.tool_name, ToolContractName.RUN_TESTS)
        self.assertTrue(obs.allowed)

    def test_run_tests_blocked_no_permission(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["inference"])
        workspace = self._workspace(runtime, job)

        obs = runtime._tool_run_tests(
            job=job, workspace=workspace,
            arguments={"command": "python3 -m unittest --help"},
        )

        self.assertEqual(obs.tool_name, ToolContractName.RUN_TESTS)
        self.assertEqual(obs.status, ToolContractStatus.BLOCKED)
        self.assertFalse(obs.allowed)

    def test_run_tests_disallowed_head(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["run_tests"])
        workspace = self._workspace(runtime, job)

        obs = runtime._tool_run_tests(
            job=job, workspace=workspace,
            arguments={"command": "ls -la"},
        )

        self.assertEqual(obs.tool_name, ToolContractName.RUN_TESTS)
        self.assertEqual(obs.status, ToolContractStatus.FAILED)
        self.assertTrue(obs.allowed)
        self.assertIn("run_tests_head_not_allowed", obs.error)

    def test_run_tests_empty_command_blocked_by_engine(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["run_tests"])
        workspace = self._workspace(runtime, job)

        obs = runtime._tool_run_tests(
            job=job, workspace=workspace,
            arguments={"command": ""},
        )

        self.assertEqual(obs.tool_name, ToolContractName.RUN_TESTS)
        self.assertFalse(obs.allowed)


if __name__ == "__main__":
    unittest.main()
