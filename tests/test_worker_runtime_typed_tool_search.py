"""Tests for WorkerRuntime._tool_search typed tool body."""

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
        metadata={"session_id": "test-search"},
        job_id="test-search-job",
    )

    stop_event = threading.Event()
    runtime = WorkerRuntime(
        worker_id="test-search-worker",
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


class TestToolSearch(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="p2_search_")
        self._tmp_path = Path(self._tmp)

    def _workspace(self, runtime: WorkerRuntime, job: Job):
        return runtime._workspace_controller.for_job(job)

    def test_search_allowed_emits_executed_observation(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["run_command"])
        workspace = self._workspace(runtime, job)
        (workspace.repo_root / "alpha.txt").write_text("needle line\n", encoding="utf-8")

        obs = runtime._tool_search(
            job=job, workspace=workspace, arguments={"query": "needle"}
        )

        self.assertEqual(obs.tool_name, ToolContractName.SEARCH)
        self.assertEqual(obs.status, ToolContractStatus.EXECUTED)
        self.assertTrue(obs.allowed)

    def test_search_blocked_no_permission(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["inference"])
        workspace = self._workspace(runtime, job)
        (workspace.repo_root / "alpha.txt").write_text("needle here\n", encoding="utf-8")

        obs = runtime._tool_search(
            job=job, workspace=workspace, arguments={"query": "needle"}
        )

        self.assertEqual(obs.tool_name, ToolContractName.SEARCH)
        self.assertEqual(obs.status, ToolContractStatus.BLOCKED)
        self.assertFalse(obs.allowed)

    def test_search_allowed_payload_contains_needle_match(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["run_command"])
        workspace = self._workspace(runtime, job)
        (workspace.repo_root / "alpha.txt").write_text(
            "needle line one\nanother line\n", encoding="utf-8"
        )
        nested = workspace.repo_root / "nested"
        nested.mkdir(parents=True, exist_ok=True)
        (nested / "beta.py").write_text(
            'def needle_function():\n    return "needle"\n', encoding="utf-8"
        )

        obs = runtime._tool_search(
            job=job, workspace=workspace, arguments={"query": "needle"}
        )

        self.assertEqual(obs.status, ToolContractStatus.EXECUTED)
        payload = obs.structured_payload or {}
        self.assertIn("matches", payload)
        self.assertGreater(payload.get("match_count", 0), 0)
        paths_found = [m["path"] for m in payload["matches"]]
        self.assertTrue(
            any("alpha.txt" in p for p in paths_found),
            f"Expected alpha.txt in matches, got: {paths_found}",
        )

    def test_search_missing_query_emits_failure(self):
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["run_command"])
        workspace = self._workspace(runtime, job)

        obs = runtime._tool_search(
            job=job, workspace=workspace, arguments={}
        )

        self.assertEqual(obs.tool_name, ToolContractName.SEARCH)
        self.assertIn("search_missing_query", obs.error)
        self.assertIn(obs.status, (ToolContractStatus.FAILED, ToolContractStatus.BLOCKED))


if __name__ == "__main__":
    unittest.main()
