"""Tests for WorkerRuntime._tool_repo_map typed tool body."""

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
        escalation_policy=EscalationPolicy(
            allow_auto_escalation=False,
            escalate_on_retry_exhaustion=False,
        ),
        validation_requirements=[],
        metadata={"session_id": "test-repo-map"},
        job_id="test-repo-map-job",
    )

    stop_event = threading.Event()
    runtime = WorkerRuntime(
        worker_id="test-repo-map-worker",
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


class TestToolRepoMap(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="p2_repo_map_")
        self._tmp_path = Path(self._tmp)

    def _workspace(self, runtime: WorkerRuntime, job: Job):
        return runtime._workspace_controller.for_job(job)

    def _populate_repo(self, repo_root: Path) -> None:
        (repo_root / "alpha.txt").write_text("needle line one\nanother line\n", encoding="utf-8")
        nested = repo_root / "nested"
        nested.mkdir(parents=True, exist_ok=True)
        (nested / "beta.py").write_text(
            'def needle_function():\n    return "needle"\n', encoding="utf-8"
        )

    def test_repo_map_allowed_emits_executed_observation(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["run_command"])
        workspace = self._workspace(runtime, job)
        self._populate_repo(workspace.repo_root)

        obs = runtime._tool_repo_map(
            job=job, workspace=workspace, arguments={"path": "."}
        )

        self.assertEqual(obs.tool_name, ToolContractName.REPO_MAP)
        self.assertEqual(obs.status, ToolContractStatus.EXECUTED)
        self.assertTrue(obs.allowed)

    def test_repo_map_blocked_no_permission(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["inference"])
        workspace = self._workspace(runtime, job)
        self._populate_repo(workspace.repo_root)

        obs = runtime._tool_repo_map(
            job=job, workspace=workspace, arguments={"path": "."}
        )

        self.assertEqual(obs.tool_name, ToolContractName.REPO_MAP)
        self.assertEqual(obs.status, ToolContractStatus.BLOCKED)
        self.assertFalse(obs.allowed)

    def test_repo_map_payload_includes_expected_paths(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["run_command"])
        workspace = self._workspace(runtime, job)
        self._populate_repo(workspace.repo_root)

        obs = runtime._tool_repo_map(
            job=job, workspace=workspace, arguments={"path": "."}
        )

        self.assertEqual(obs.status, ToolContractStatus.EXECUTED)
        payload = obs.structured_payload or {}
        entry_paths = [e["path"] for e in payload.get("entries", [])]
        self.assertTrue(
            any("alpha.txt" in p for p in entry_paths),
            f"alpha.txt not found in entries: {entry_paths}",
        )
        self.assertTrue(
            any("beta.py" in p for p in entry_paths),
            f"beta.py not found in entries: {entry_paths}",
        )

    def test_repo_map_entry_count_ge_2(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["run_command"])
        workspace = self._workspace(runtime, job)
        self._populate_repo(workspace.repo_root)

        obs = runtime._tool_repo_map(
            job=job, workspace=workspace, arguments={"path": "."}
        )

        self.assertEqual(obs.status, ToolContractStatus.EXECUTED)
        payload = obs.structured_payload or {}
        self.assertIn("entries", payload)
        self.assertGreaterEqual(payload.get("entry_count", 0), 2)


if __name__ == "__main__":
    unittest.main()
