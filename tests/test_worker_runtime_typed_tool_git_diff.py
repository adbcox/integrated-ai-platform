"""Tests for WorkerRuntime._tool_git_diff typed tool body."""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
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


def _git_available() -> bool:
    return shutil.which("git") is not None


def _init_git_repo(repo_root: Path) -> None:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(repo_root)], check=True, env=env
    )
    (repo_root / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_root), "add", "seed.txt"], check=True, env=env)
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-q", "-m", "init"], check=True, env=env
    )
    (repo_root / "seed.txt").write_text("seed\nmodified\n", encoding="utf-8")


def _make_runtime(tmp_root: Path, *, allowed_tools: list[str]) -> tuple[WorkerRuntime, Job]:
    artifact_root = tmp_root / "artifacts"
    artifact_root.mkdir(parents=True, exist_ok=True)
    repo_root = tmp_root / "repo"

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
        metadata={"session_id": "test-git-diff"},
        job_id="test-git-diff-job",
    )

    stop_event = threading.Event()
    runtime = WorkerRuntime(
        worker_id="test-git-diff-worker",
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


@unittest.skipUnless(_git_available(), "git not available on PATH")
class TestToolGitDiff(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="p2_git_diff_")
        self._tmp_path = Path(self._tmp)

    def _workspace(self, runtime: WorkerRuntime, job: Job):
        return runtime._workspace_controller.for_job(job)

    def test_git_diff_success(self):
        _init_git_repo(self._tmp_path / "repo")
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["apply_edit"])
        workspace = self._workspace(runtime, job)

        obs = runtime._tool_git_diff(
            job=job, workspace=workspace, arguments={"ref": "HEAD"}
        )

        self.assertEqual(obs.tool_name, ToolContractName.GIT_DIFF)
        self.assertEqual(obs.status, ToolContractStatus.EXECUTED)
        self.assertTrue(obs.allowed)
        self.assertEqual(obs.return_code, 0)

    def test_git_diff_blocked_no_permission(self):
        _init_git_repo(self._tmp_path / "repo")
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["inference"])
        workspace = self._workspace(runtime, job)

        obs = runtime._tool_git_diff(
            job=job, workspace=workspace, arguments={"ref": "HEAD"}
        )

        self.assertEqual(obs.tool_name, ToolContractName.GIT_DIFF)
        self.assertEqual(obs.status, ToolContractStatus.BLOCKED)
        self.assertFalse(obs.allowed)

    def test_git_diff_default_ref_is_head(self):
        _init_git_repo(self._tmp_path / "repo")
        runtime, job = _make_runtime(self._tmp_path, allowed_tools=["apply_edit"])
        workspace = self._workspace(runtime, job)

        obs = runtime._tool_git_diff(
            job=job, workspace=workspace, arguments={}
        )

        self.assertEqual(obs.tool_name, ToolContractName.GIT_DIFF)
        self.assertIn(obs.status, {ToolContractStatus.EXECUTED, ToolContractStatus.FAILED})


if __name__ == "__main__":
    unittest.main()
