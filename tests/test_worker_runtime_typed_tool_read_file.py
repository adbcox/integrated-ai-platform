"""Tests for WorkerRuntime._tool_read_file typed tool body."""

from __future__ import annotations

import queue
import tempfile
import threading
import unittest
from pathlib import Path

from framework.inference_adapter import LocalHeuristicInferenceAdapter
from framework.backend_profiles import get_backend_profile
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
        metadata={"session_id": "test-read-file"},
        job_id="test-read-file-job",
    )

    stop_event = threading.Event()
    runtime = WorkerRuntime(
        worker_id="test-read-file-worker",
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


class TestToolReadFile(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="p2_read_file_")
        self._tmp_path = Path(self._tmp)

    def _workspace(self, runtime: WorkerRuntime, job: Job):
        return runtime._workspace_controller.for_job(job)

    def test_read_file_success(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["apply_edit"])
        workspace = self._workspace(runtime, job)
        probe = workspace.repo_root / "probe.txt"
        probe.write_text("hello phase2\n", encoding="utf-8")

        obs = runtime._tool_read_file(
            job=job, workspace=workspace, arguments={"path": "probe.txt"}
        )

        self.assertEqual(obs.tool_name, ToolContractName.READ_FILE)
        self.assertEqual(obs.status, ToolContractStatus.EXECUTED)
        self.assertTrue(obs.allowed)
        self.assertIn("hello phase2", obs.stdout)

    def test_read_file_blocked_no_permission(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["inference"])
        workspace = self._workspace(runtime, job)
        probe = workspace.repo_root / "probe.txt"
        probe.write_text("should not read\n", encoding="utf-8")

        obs = runtime._tool_read_file(
            job=job, workspace=workspace, arguments={"path": "probe.txt"}
        )

        self.assertEqual(obs.tool_name, ToolContractName.READ_FILE)
        self.assertEqual(obs.status, ToolContractStatus.BLOCKED)
        self.assertFalse(obs.allowed)

    def test_read_file_nonexistent(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["apply_edit"])
        workspace = self._workspace(runtime, job)

        obs = runtime._tool_read_file(
            job=job, workspace=workspace, arguments={"path": "no_such_file.txt"}
        )

        self.assertEqual(obs.tool_name, ToolContractName.READ_FILE)
        self.assertEqual(obs.status, ToolContractStatus.FAILED)
        self.assertTrue(obs.allowed)
        self.assertIn("read_error", obs.error)

    def test_read_file_oversized_truncates_not_fails(self):
        from framework.worker_runtime import _PHASE2_READ_FILE_MAX_BYTES
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["apply_edit"])
        workspace = self._workspace(runtime, job)
        large = workspace.repo_root / "large.txt"
        large.write_bytes(b"x" * (_PHASE2_READ_FILE_MAX_BYTES + 1))

        obs = runtime._tool_read_file(
            job=job, workspace=workspace, arguments={"path": "large.txt"}
        )

        self.assertEqual(obs.tool_name, ToolContractName.READ_FILE)
        self.assertEqual(obs.status, ToolContractStatus.EXECUTED)
        self.assertTrue(obs.structured_payload.get("content_truncated"))
        self.assertEqual(obs.structured_payload.get("original_size_bytes"), _PHASE2_READ_FILE_MAX_BYTES + 1)

    def test_read_file_tool_name_is_read_file_not_apply_patch(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["apply_edit"])
        workspace = self._workspace(runtime, job)
        f = workspace.repo_root / "check.txt"
        f.write_text("content\n", encoding="utf-8")

        obs = runtime._tool_read_file(
            job=job, workspace=workspace, arguments={"path": "check.txt"}
        )

        self.assertNotEqual(obs.tool_name, ToolContractName.APPLY_PATCH)
        self.assertEqual(obs.tool_name, ToolContractName.READ_FILE)


if __name__ == "__main__":
    unittest.main()
