"""Tests for _typed_tool_probe_template and build_job probe wiring."""

from __future__ import annotations

import argparse
import queue
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bin.framework_control_plane import _typed_tool_probe_template, build_job

REPO_ROOT = Path(__file__).resolve().parents[1]


def _probe_args(**overrides) -> argparse.Namespace:
    defaults = dict(
        task_template="typed_tool_probe",
        shell_command="",
        requested_output=[],
        artifact_input=[],
        priority="p1",
        inference_prompt="",
        inference_mode="heuristic",
        inference_replay="",
        retry_budget=0,
        retry_backoff_seconds=0,
        auto_escalate=False,
        task_portfolio="none",
        task_class="validation_check_execution",
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class TestTypedToolProbeTemplate(unittest.TestCase):
    def test_returns_phase2_typed_tools_list(self):
        t = _typed_tool_probe_template()
        self.assertIsInstance(t.get("phase2_typed_tools"), list)
        self.assertTrue(t["phase2_typed_tools"], "phase2_typed_tools must be non-empty")

    def test_contains_read_file_and_apply_patch(self):
        t = _typed_tool_probe_template()
        names = {spec["contract_name"] for spec in t["phase2_typed_tools"]}
        self.assertIn("read_file", names)
        self.assertIn("apply_patch", names)

    def test_requested_outputs_non_empty(self):
        t = _typed_tool_probe_template()
        self.assertTrue(t.get("requested_outputs"))


class TestBuildJobTypedToolProbeMetadata(unittest.TestCase):
    def test_probe_template_passes_phase2_typed_tools(self):
        job = build_job(_probe_args())
        tools = job.metadata.get("phase2_typed_tools")
        self.assertIsInstance(tools, list)
        self.assertTrue(tools, "phase2_typed_tools must be non-empty")

    def test_none_template_has_empty_phase2_typed_tools(self):
        job = build_job(_probe_args(task_template="none"))
        self.assertEqual(job.metadata.get("phase2_typed_tools"), [])

    def test_probe_requested_outputs_wired(self):
        job = build_job(_probe_args())
        self.assertTrue(job.requested_outputs)


class TestTypedToolProbeEndToEnd(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="probe_wire_e2e_")
        self._tmp_path = Path(self._tmp)

    def _make_runtime(self):
        from framework.backend_profiles import get_backend_profile
        from framework.inference_adapter import LocalHeuristicInferenceAdapter
        from framework.learning_hooks import LearningHooks
        from framework.permission_engine import PermissionEngine
        from framework.sandbox import LocalSandboxRunner
        from framework.state_store import StateStore
        from framework.worker_runtime import WorkerRuntime
        from framework.workspace import WorkspaceController

        artifact_root = self._tmp_path / "artifacts"
        artifact_root.mkdir(parents=True, exist_ok=True)

        store = StateStore(artifact_root)
        learning = LearningHooks(
            store=store,
            learning_latest_path=artifact_root / "learning" / "latest.json",
        )
        from framework.backend_profiles import BACKEND_PROFILES
        profile_name = next(iter(BACKEND_PROFILES))
        profile = get_backend_profile(profile_name)
        inference = LocalHeuristicInferenceAdapter(profile=profile)
        workspace_controller = WorkspaceController(artifact_root)
        sandbox_runner = LocalSandboxRunner()
        permission_engine = PermissionEngine()
        stop_event = threading.Event()

        return WorkerRuntime(
            worker_id="probe-wire-e2e-worker",
            queue_ref=queue.PriorityQueue(),
            inference=inference,
            store=store,
            learning=learning,
            stop_event=stop_event,
            context_release_callback=lambda _job: None,
            permission_engine=permission_engine,
            workspace_controller=workspace_controller,
            sandbox_runner=sandbox_runner,
        )

    def test_probe_enters_typed_tool_branch_and_completes(self):
        runtime = self._make_runtime()
        job = build_job(_probe_args())
        payload = runtime._execute_job(job)

        status = payload.get("status") or payload.get("final_outcome") or ""
        self.assertIn(status, {"completed"}, f"Expected completed, got status={status!r}, payload keys={list(payload)}")

        trace = payload.get("typed_tool_trace") or []
        read_file_entries = [
            e for e in trace
            if e.get("tool_name") == "read_file" or e.get("contract_name") == "read_file"
        ]
        self.assertGreaterEqual(
            len(read_file_entries), 1,
            f"Expected at least one read_file entry in typed_tool_trace, got: {trace}",
        )

    def test_probe_write_produced_output_file(self):
        runtime = self._make_runtime()
        job = build_job(_probe_args())
        runtime._execute_job(job)

        output_path = REPO_ROOT / "artifacts" / "framework" / "typed_tool_probe_output.txt"
        self.assertTrue(output_path.exists(), f"Expected {output_path} to exist after probe run")
        content = output_path.read_text(encoding="utf-8")
        self.assertIn("phase2_typed_tool_probe_ok", content, f"Unexpected content: {content!r}")


if __name__ == "__main__":
    unittest.main()
