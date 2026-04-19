"""Tests for _retrieval_probe_template and build_job retrieval probe wiring."""

from __future__ import annotations

import argparse
import queue
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bin.framework_control_plane import _retrieval_probe_template, build_job, parse_args

REPO_ROOT = Path(__file__).resolve().parents[1]


def _retrieval_args(**overrides) -> argparse.Namespace:
    defaults = dict(
        task_template="retrieval_probe",
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


def _find_result(results: list, tool_name: str) -> dict | None:
    for r in results:
        if r.get("tool_name") == tool_name:
            return r
    return None


class TestRetrievalProbeTemplate(unittest.TestCase):
    def test_has_phase2_typed_tools(self):
        t = _retrieval_probe_template()
        self.assertIsInstance(t.get("phase2_typed_tools"), list)
        self.assertTrue(t["phase2_typed_tools"])

    def test_contains_search_contract(self):
        t = _retrieval_probe_template()
        names = [e["contract_name"] for e in t["phase2_typed_tools"]]
        self.assertIn("search", names)

    def test_search_query_is_execute_job(self):
        t = _retrieval_probe_template()
        search = next(e for e in t["phase2_typed_tools"] if e["contract_name"] == "search")
        self.assertEqual(search["arguments"]["query"], "_execute_job")

    def test_contains_repo_map_contract(self):
        t = _retrieval_probe_template()
        names = [e["contract_name"] for e in t["phase2_typed_tools"]]
        self.assertIn("repo_map", names)

    def test_repo_map_path_is_framework(self):
        t = _retrieval_probe_template()
        repo_map = next(e for e in t["phase2_typed_tools"] if e["contract_name"] == "repo_map")
        self.assertEqual(repo_map["arguments"]["path"], "framework")

    def test_contains_apply_patch_contract(self):
        t = _retrieval_probe_template()
        names = [e["contract_name"] for e in t["phase2_typed_tools"]]
        self.assertIn("apply_patch", names)

    def test_requested_outputs_non_empty(self):
        t = _retrieval_probe_template()
        self.assertTrue(t.get("requested_outputs"))


class TestBuildJobRetrievalProbeMetadata(unittest.TestCase):
    def test_build_job_has_three_typed_tools(self):
        job = build_job(_retrieval_args())
        tools = job.metadata.get("phase2_typed_tools") or []
        self.assertEqual(len(tools), 3, f"Expected 3 tools, got {len(tools)}: {tools}")

    def test_contract_names_correct(self):
        job = build_job(_retrieval_args())
        names = {e["contract_name"] for e in job.metadata["phase2_typed_tools"]}
        self.assertEqual(names, {"search", "repo_map", "apply_patch"})

    def test_retrieval_probe_in_argparse_choices(self):
        with patch.object(sys, "argv", ["framework_control_plane.py", "--task-template", "retrieval_probe"]):
            args = parse_args()
        self.assertEqual(args.task_template, "retrieval_probe")


class TestRetrievalProbeEndToEnd(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="retrieval_probe_e2e_")
        self._tmp_path = Path(self._tmp)
        self._payload = None

    def _run(self):
        if self._payload is not None:
            return self._payload

        from framework.backend_profiles import BACKEND_PROFILES, get_backend_profile
        from framework.inference_adapter import LocalHeuristicInferenceAdapter
        from framework.learning_hooks import LearningHooks
        from framework.permission_engine import PermissionEngine
        from framework.sandbox import LocalSandboxRunner
        from framework.state_store import StateStore
        from framework.worker_runtime import WorkerRuntime
        from framework.workspace import WorkspaceController
        from framework.framework_control_plane import _phase2_extract_typed_results

        artifact_root = self._tmp_path / "artifacts"
        artifact_root.mkdir(parents=True, exist_ok=True)

        store = StateStore(artifact_root)
        learning = LearningHooks(
            store=store,
            learning_latest_path=artifact_root / "learning" / "latest.json",
        )
        profile_name = next(iter(BACKEND_PROFILES))
        inference = LocalHeuristicInferenceAdapter(profile=get_backend_profile(profile_name))
        workspace_controller = WorkspaceController(artifact_root)
        sandbox_runner = LocalSandboxRunner()
        permission_engine = PermissionEngine()
        stop_event = threading.Event()

        runtime = WorkerRuntime(
            worker_id="retrieval-probe-e2e-worker",
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

        job = build_job(_retrieval_args())
        raw_payload = runtime._execute_job(job)
        self._payload = {
            "raw": raw_payload,
            "results": _phase2_extract_typed_results(raw_payload),
        }
        return self._payload

    def test_search_executes_and_returns_structured_payload(self):
        data = self._run()
        search_result = _find_result(data["results"], "search")
        self.assertIsNotNone(search_result, "No search result in phase2_typed_tool_results")
        self.assertEqual(search_result.get("status"), "executed",
                         f"search status={search_result.get('status')!r}, expected 'executed'")
        payload = search_result.get("structured_payload") or {}
        self.assertIsInstance(payload, dict, "structured_payload is not a dict")
        self.assertIn("matches", payload, "structured_payload missing 'matches' key")

    def test_repo_map_returns_framework_entries(self):
        data = self._run()
        repo_map_result = _find_result(data["results"], "repo_map")
        self.assertIsNotNone(repo_map_result, "No repo_map result in phase2_typed_tool_results")
        entries = (repo_map_result.get("structured_payload") or {}).get("entries") or []
        self.assertGreater(len(entries), 0, "repo_map of framework/ returned zero entries")

    def test_apply_patch_wrote_artifact(self):
        self._run()
        output_path = REPO_ROOT / "artifacts" / "framework" / "retrieval_probe_output.txt"
        self.assertTrue(output_path.exists(), f"Expected {output_path} to exist")
        content = output_path.read_text(encoding="utf-8")
        self.assertIn("phase3_retrieval_probe_ok", content)

    def test_all_three_tools_executed(self):
        data = self._run()
        results = data["results"]
        for name in ("search", "repo_map", "apply_patch"):
            r = _find_result(results, name)
            self.assertIsNotNone(r, f"No result for {name}")
            self.assertEqual(
                r.get("status"), "executed",
                f"{name} status={r.get('status')!r}, expected 'executed'. full result: {r}",
            )


if __name__ == "__main__":
    unittest.main()
