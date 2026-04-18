"""Tests for WorkerRuntime _execute_job dispatching APPLY_PATCH + PUBLISH_ARTIFACT."""

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
from framework.tool_action_observation_contract import ToolContractStatus
from framework.worker_runtime import WorkerRuntime
from framework.workspace import WorkspaceController


def _make_job_and_runtime(tmp_root: Path) -> tuple[WorkerRuntime, Job]:
    artifact_root = tmp_root / "artifacts"
    artifact_root.mkdir(parents=True, exist_ok=True)
    repo_root = tmp_root / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)

    (repo_root / "patch_me.txt").write_text("alpha\nbeta\n", encoding="utf-8")
    (repo_root / "artifact_source.txt").write_text("artifact-body\n", encoding="utf-8")

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

    phase2_typed_tools = [
        {
            "tool_name": "apply_patch",
            "arguments": {
                "path": "patch_me.txt",
                "mode": "replace_text",
                "find": "beta",
                "replace": "gamma",
            },
        },
        {
            "tool_name": "publish_artifact",
            "arguments": {
                "source": "artifact_source.txt",
                "artifact_path": "reports/copied_artifact.txt",
            },
        },
    ]

    job = Job(
        task_class=JobClass.VALIDATION_CHECK_EXECUTION,
        priority=JobPriority.P2,
        target=WorkTarget(repo_root=str(repo_root), worktree_target=str(repo_root)),
        action=JobAction.INFERENCE_ONLY,
        requested_outputs=[],
        allowed_tools_actions=["apply_edit", "run_command"],
        retry_policy=RetryPolicy(retry_budget=0, retry_backoff_seconds=0),
        escalation_policy=EscalationPolicy(
            allow_auto_escalation=False,
            escalate_on_retry_exhaustion=False,
        ),
        validation_requirements=[],
        metadata={
            "session_id": "test-dispatcher-impl3",
            "task_id": "test-dispatcher-impl3-task",
            "inference_prompt": "dispatcher impl3 test",
            "risk_tier": "standard",
            "selected_model_profile": "mac_local",
            "model_profile": "mac_local",
            "phase2_typed_tools": phase2_typed_tools,
        },
        job_id="test-dispatcher-impl3-job",
    )

    stop_event = threading.Event()
    runtime = WorkerRuntime(
        worker_id="test-dispatcher-impl3-worker",
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
    return runtime, job


class TestDispatcherPhase2ToolImpl3(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="p2_dispatcher_impl3_")
        self._tmp_path = Path(self._tmp)

    def test_allowed_payload_has_apply_patch_and_publish_artifact(self):
        runtime, job = _make_job_and_runtime(self._tmp_path)
        result = runtime._execute_job(job)
        trace = (result.get("session_bundle") or {}).get("tool_trace") or []
        tool_names = [r.get("tool_name") or r.get("contract_name") for r in trace]
        self.assertIn("apply_patch", tool_names, f"apply_patch not in trace: {tool_names}")
        self.assertIn("publish_artifact", tool_names, f"publish_artifact not in trace: {tool_names}")

    def test_session_bundle_tool_trace_has_both_tools(self):
        runtime, job = _make_job_and_runtime(self._tmp_path)
        result = runtime._execute_job(job)
        bundle = result.get("session_bundle") or {}
        trace = bundle.get("tool_trace") or []
        statuses = {
            (r.get("tool_name") or r.get("contract_name")): r.get("status")
            for r in trace
        }
        self.assertIn("apply_patch", statuses)
        self.assertIn("publish_artifact", statuses)
        self.assertEqual(statuses.get("apply_patch"), ToolContractStatus.EXECUTED.value)
        self.assertEqual(statuses.get("publish_artifact"), ToolContractStatus.EXECUTED.value)

    def test_canonical_session_tool_trace_has_both_tools(self):
        runtime, job = _make_job_and_runtime(self._tmp_path)
        result = runtime._execute_job(job)
        canonical = result.get("canonical_session") or {}
        trace = canonical.get("tool_trace") or []
        tool_names = [r.get("tool_name") or r.get("contract_name") for r in trace]
        self.assertIn("apply_patch", tool_names, f"apply_patch not in canonical trace: {tool_names}")
        self.assertIn("publish_artifact", tool_names, f"publish_artifact not in canonical trace: {tool_names}")


if __name__ == "__main__":
    unittest.main()
