"""Tests for WorkerRuntime._execute_phase2_typed_tool dispatcher."""

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
from framework.worker_runtime import WorkerRuntime
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
        metadata={"session_id": "test-dispatcher"},
        job_id="test-dispatcher-job",
    )

    stop_event = threading.Event()
    runtime = WorkerRuntime(
        worker_id="test-dispatcher-worker",
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


class TestTypedToolDispatcher(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="p2_dispatcher_")
        self._tmp_path = Path(self._tmp)

    def _workspace(self, runtime: WorkerRuntime, job: Job):
        return runtime._workspace_controller.for_job(job)

    def test_dispatch_read_file(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["apply_edit"])
        workspace = self._workspace(runtime, job)
        f = workspace.repo_root / "read_target.txt"
        f.write_text("dispatcher test\n", encoding="utf-8")

        obs = runtime._execute_phase2_typed_tool(
            job=job,
            workspace=workspace,
            contract_name=ToolContractName.READ_FILE,
            arguments={"path": "read_target.txt"},
        )

        self.assertEqual(obs.tool_name, ToolContractName.READ_FILE)

    def test_dispatch_list_dir(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["apply_edit"])
        workspace = self._workspace(runtime, job)

        obs = runtime._execute_phase2_typed_tool(
            job=job,
            workspace=workspace,
            contract_name=ToolContractName.LIST_DIR,
            arguments={"path": "."},
        )

        self.assertEqual(obs.tool_name, ToolContractName.LIST_DIR)

    def test_dispatch_run_tests(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["run_tests"])
        workspace = self._workspace(runtime, job)

        obs = runtime._execute_phase2_typed_tool(
            job=job,
            workspace=workspace,
            contract_name=ToolContractName.RUN_TESTS,
            arguments={"command": "python3 -m unittest --help"},
        )

        self.assertEqual(obs.tool_name, ToolContractName.RUN_TESTS)

    def test_dispatch_unregistered_contract_returns_synthetic_denied(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["apply_edit"])
        workspace = self._workspace(runtime, job)

        obs = runtime._execute_phase2_typed_tool(
            job=job,
            workspace=workspace,
            contract_name=ToolContractName.SEARCH,
            arguments={},
        )

        self.assertEqual(obs.status, ToolContractStatus.BLOCKED)
        self.assertFalse(obs.allowed)
        self.assertIn("unregistered_contract", obs.error)

    def test_dispatch_via_metadata_phase2_typed_tools(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["apply_edit", "run_tests"])
        workspace = self._workspace(runtime, job)
        f = workspace.repo_root / "meta_probe.txt"
        f.write_text("probe\n", encoding="utf-8")
        job.metadata["phase2_typed_tools"] = [
            {"contract_name": "read_file", "arguments": {"path": "meta_probe.txt"}},
            {"contract_name": "list_dir", "arguments": {"path": "."}},
        ]

        outcome = runtime._execute_attempt(job)

        self.assertEqual(outcome.status, "completed")
        self.assertEqual(outcome.return_code, 0)
        self.assertIn("read_file", outcome.output)
        self.assertIn("list_dir", outcome.output)


if __name__ == "__main__":
    unittest.main()
