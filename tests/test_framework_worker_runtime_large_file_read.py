"""Tests for PHASE3-LARGE-FILE-PARTIAL-READ-1: truncate-and-continue for oversized files."""

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
from framework.worker_runtime import WorkerRuntime, _PHASE2_READ_FILE_MAX_BYTES
from framework.workspace import WorkspaceController


def _make_runtime(tmp_root: Path) -> tuple[WorkerRuntime, Job]:
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
        allowed_tools_actions=["apply_edit"],
        retry_policy=RetryPolicy(retry_budget=0, retry_backoff_seconds=0),
        escalation_policy=EscalationPolicy(
            allow_auto_escalation=False, escalate_on_retry_exhaustion=False
        ),
        validation_requirements=[],
        metadata={"session_id": "test-large-read"},
        job_id="test-large-read-job",
    )

    stop_event = threading.Event()
    runtime = WorkerRuntime(
        worker_id="test-large-read-worker",
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


def _write_file(repo_root: Path, name: str, size_bytes: int) -> Path:
    p = repo_root / name
    data = ("x" * 79 + "\n") * (size_bytes // 80 + 1)
    p.write_bytes(data[:size_bytes].encode("utf-8"))
    return p


class TestReadFileAtCap(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="p3_large_read_"))

    def _workspace(self, runtime, job):
        return runtime._workspace_controller.for_job(job)

    def test_file_exactly_at_cap_succeeds(self):
        runtime, job = _make_runtime(self._tmp)
        ws = self._workspace(runtime, job)
        f = _write_file(ws.repo_root, "at_cap.txt", _PHASE2_READ_FILE_MAX_BYTES)
        obs = runtime._tool_read_file(job=job, workspace=ws, arguments={"path": f.name})
        self.assertEqual(obs.status, "executed")

    def test_file_one_byte_over_cap_succeeds_not_fails(self):
        runtime, job = _make_runtime(self._tmp)
        ws = self._workspace(runtime, job)
        f = _write_file(ws.repo_root, "over_cap.txt", _PHASE2_READ_FILE_MAX_BYTES + 1)
        obs = runtime._tool_read_file(job=job, workspace=ws, arguments={"path": f.name})
        self.assertEqual(obs.status, "executed")
        self.assertNotIn("file_too_large", obs.error or "")

    def test_file_101832_bytes_succeeds(self):
        runtime, job = _make_runtime(self._tmp)
        ws = self._workspace(runtime, job)
        f = _write_file(ws.repo_root, "large.txt", 101832)
        obs = runtime._tool_read_file(job=job, workspace=ws, arguments={"path": f.name})
        self.assertEqual(obs.status, "executed")


class TestTruncatedPayload(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="p3_trunc_"))

    def _workspace(self, runtime, job):
        return runtime._workspace_controller.for_job(job)

    def _oversized_obs(self):
        runtime, job = _make_runtime(self._tmp)
        ws = self._workspace(runtime, job)
        f = _write_file(ws.repo_root, "big.txt", 101832)
        return runtime._tool_read_file(job=job, workspace=ws, arguments={"path": f.name})

    def test_oversized_content_truncated_is_true(self):
        obs = self._oversized_obs()
        self.assertTrue(obs.structured_payload.get("content_truncated"))

    def test_oversized_original_size_bytes_equals_full_size(self):
        obs = self._oversized_obs()
        self.assertEqual(obs.structured_payload.get("original_size_bytes"), 101832)

    def test_oversized_stdout_length_approx_cap(self):
        obs = self._oversized_obs()
        # decoded char count ≈ cap bytes (ASCII content, so 1:1)
        self.assertLessEqual(len(obs.stdout), _PHASE2_READ_FILE_MAX_BYTES + 4)
        self.assertGreater(len(obs.stdout), _PHASE2_READ_FILE_MAX_BYTES // 2)

    def test_content_is_valid_string_no_unicode_error(self):
        runtime, job = _make_runtime(self._tmp)
        ws = self._workspace(runtime, job)
        f = _write_file(ws.repo_root, "big2.txt", 101832)
        try:
            obs = runtime._tool_read_file(job=job, workspace=ws, arguments={"path": f.name})
            _ = obs.stdout.encode("utf-8")  # must be re-encodable
        except UnicodeDecodeError as e:
            self.fail(f"UnicodeDecodeError: {e}")


class TestNonTruncatedPayload(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="p3_small_"))

    def _workspace(self, runtime, job):
        return runtime._workspace_controller.for_job(job)

    def _small_obs(self):
        runtime, job = _make_runtime(self._tmp)
        ws = self._workspace(runtime, job)
        f = ws.repo_root / "small.txt"
        f.write_text("hello world\n", encoding="utf-8")
        return runtime._tool_read_file(job=job, workspace=ws, arguments={"path": "small.txt"})

    def test_undersized_content_truncated_is_false(self):
        obs = self._small_obs()
        self.assertFalse(obs.structured_payload.get("content_truncated"))

    def test_undersized_original_size_bytes_equals_size_bytes(self):
        obs = self._small_obs()
        self.assertEqual(
            obs.structured_payload.get("original_size_bytes"),
            obs.structured_payload.get("size_bytes"),
        )

    def test_small_file_behavior_unchanged(self):
        obs = self._small_obs()
        self.assertEqual(obs.status, "executed")
        self.assertIn("hello world", obs.stdout)


class TestBinaryFileGuardPreserved(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="p3_binary_"))

    def _workspace(self, runtime, job):
        return runtime._workspace_controller.for_job(job)

    def test_binary_file_still_fails_before_truncation(self):
        runtime, job = _make_runtime(self._tmp)
        ws = self._workspace(runtime, job)
        # \x80 is a lone UTF-8 continuation byte — invalid as standalone UTF-8
        binary_file = ws.repo_root / "binary.bin"
        binary_file.write_bytes(b"\x80\x81\x82\x83" * 100)
        obs = runtime._tool_read_file(
            job=job, workspace=ws, arguments={"path": "binary.bin"}
        )
        self.assertEqual(obs.status, "failed")
        self.assertIn("binary_file_not_supported", obs.error or "")


if __name__ == "__main__":
    unittest.main()
