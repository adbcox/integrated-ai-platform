"""Tests for the Phase 2 tool-impl-2 dispatcher extension (SEARCH, REPO_MAP)."""

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
from framework.worker_runtime import WorkerRuntime
from framework.workspace import WorkspaceController


def _make_runtime_with_repo(tmp_root: Path, *, allowed_tools: list[str]) -> tuple[WorkerRuntime, Job]:
    artifact_root = tmp_root / "artifacts"
    artifact_root.mkdir(parents=True, exist_ok=True)
    repo_root = tmp_root / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)

    (repo_root / "alpha.txt").write_text("needle line one\nanother line\n", encoding="utf-8")
    nested = repo_root / "nested"
    nested.mkdir(parents=True, exist_ok=True)
    (nested / "beta.py").write_text(
        'def needle_function():\n    return "needle"\n', encoding="utf-8"
    )

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
        metadata={
            "session_id": "test-dispatcher-impl2",
            "inference_prompt": "dispatcher-impl2-test",
        },
        job_id="test-dispatcher-impl2-job",
    )

    stop_event = threading.Event()
    runtime = WorkerRuntime(
        worker_id="test-dispatcher-impl2-worker",
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


class TestTypedToolDispatcherImpl2(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="p2_dispatcher_impl2_")
        self._tmp_path = Path(self._tmp)

    def test_allowed_payload_contains_search_and_repo_map(self):
        runtime, job = _make_runtime_with_repo(self._tmp_path, allowed_tools=["run_command"])
        job.metadata["phase2_typed_tools"] = [
            {"tool_name": "search", "arguments": {"query": "needle"}},
            {"tool_name": "repo_map", "arguments": {"path": "."}},
        ]

        result = runtime._execute_job(job)

        typed_trace = result.get("typed_tool_trace", [])
        observed_names = {
            e["tool_name"]
            for e in typed_trace
            if e.get("kind") == "tool_observation"
        }
        self.assertIn("search", observed_names)
        self.assertIn("repo_map", observed_names)

    def test_session_bundle_tool_trace_contains_search_and_repo_map(self):
        runtime, job = _make_runtime_with_repo(self._tmp_path, allowed_tools=["run_command"])
        job.metadata["phase2_typed_tools"] = [
            {"tool_name": "search", "arguments": {"query": "needle"}},
            {"tool_name": "repo_map", "arguments": {"path": "."}},
        ]

        result = runtime._execute_job(job)

        bundle = result.get("session_bundle")
        self.assertIsNotNone(bundle)
        bundle_trace = bundle.get("tool_trace", []) if isinstance(bundle, dict) else []
        trace_names = {e.get("tool_name") for e in bundle_trace}
        self.assertIn("search", trace_names)
        self.assertIn("repo_map", trace_names)

    def test_canonical_session_tool_trace_contains_search_and_repo_map(self):
        runtime, job = _make_runtime_with_repo(self._tmp_path, allowed_tools=["run_command"])
        job.metadata["phase2_typed_tools"] = [
            {"tool_name": "search", "arguments": {"query": "needle"}},
            {"tool_name": "repo_map", "arguments": {"path": "."}},
        ]

        result = runtime._execute_job(job)

        canonical = result.get("canonical_session")
        self.assertIsNotNone(canonical)
        canon_trace = canonical.get("tool_trace", []) if isinstance(canonical, dict) else []
        trace_names = {e.get("tool_name") for e in canon_trace}
        self.assertIn("search", trace_names)
        self.assertIn("repo_map", trace_names)


if __name__ == "__main__":
    unittest.main()
