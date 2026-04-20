"""Offline tests for RuntimeWorkspace / RuntimeArtifactService wiring in the control plane.

All tests pass without live Ollama or running the control plane end to end.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _import_build_run_workspace():
    # Ensure bin/ is on path for module import
    bin_dir = str(REPO_ROOT / "bin")
    if bin_dir not in sys.path:
        sys.path.insert(0, bin_dir)
    from framework_control_plane import _build_run_workspace
    return _build_run_workspace


class BuildRunWorkspaceTest(unittest.TestCase):
    def setUp(self):
        self._build_run_workspace = _import_build_run_workspace()

    def _call(self, tmpdir, task_template="test_task", inference_mode="heuristic"):
        return self._build_run_workspace(
            state_root=Path(tmpdir),
            task_template=task_template,
            inference_mode=inference_mode,
        )

    def test_imports_from_control_plane(self):
        self.assertIsNotNone(self._build_run_workspace)

    def test_returns_runtime_workspace(self):
        from framework.runtime_workspace_contract import RuntimeWorkspace
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace, _ = self._call(tmpdir)
            self.assertIsInstance(workspace, RuntimeWorkspace)

    def test_returns_runtime_artifact_service(self):
        from framework.runtime_artifact_service import RuntimeArtifactService
        with tempfile.TemporaryDirectory() as tmpdir:
            _, artifact_service = self._call(tmpdir)
            self.assertIsInstance(artifact_service, RuntimeArtifactService)

    def test_creates_directories_on_disk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace, _ = self._call(tmpdir)
            self.assertTrue(workspace.scratch_root.is_dir())
            self.assertTrue(workspace.artifact_root.is_dir())

    def test_run_id_is_twelve_char_hex(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace, _ = self._call(tmpdir)
            self.assertEqual(len(workspace.run_id), 12)
            int(workspace.run_id, 16)  # raises if not hex

    def test_session_id_contains_task_template(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace, _ = self._call(tmpdir, task_template="my_template")
            self.assertIn("my_template", workspace.session_id)

    def test_session_id_contains_inference_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace, _ = self._call(tmpdir, inference_mode="gateway")
            self.assertIn("gateway", workspace.session_id)

    def test_repeated_calls_produce_different_run_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws1, _ = self._call(tmpdir)
            ws2, _ = self._call(tmpdir)
            self.assertNotEqual(ws1.run_id, ws2.run_id)

    def test_repeated_calls_with_same_inputs_keep_stable_session_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws1, _ = self._call(tmpdir, task_template="t", inference_mode="heuristic")
            ws2, _ = self._call(tmpdir, task_template="t", inference_mode="heuristic")
            self.assertEqual(ws1.session_id, ws2.session_id)


class ArtifactServiceManifestTest(unittest.TestCase):
    def _build(self, tmpdir):
        build_run_workspace = _import_build_run_workspace()
        return build_run_workspace(
            state_root=Path(tmpdir),
            task_template="manifest_test",
            inference_mode="heuristic",
        )

    def test_write_manifest_creates_run_bundle_manifest_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace, svc = self._build(tmpdir)
            manifest = svc.build_manifest(
                profile_name="mac_local",
                final_outcome="completed",
                artifact_bundle_ref="",
            )
            path = svc.write_manifest(manifest)
            self.assertTrue(path.exists())
            self.assertEqual(path.name, "run_bundle_manifest.json")

    def test_manifest_json_has_schema_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace, svc = self._build(tmpdir)
            path = svc.write_manifest(
                svc.build_manifest(profile_name="mac_local", final_outcome="completed", artifact_bundle_ref="")
            )
            data = json.loads(path.read_text())
            self.assertIn("schema_version", data)

    def test_manifest_json_contains_correct_run_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace, svc = self._build(tmpdir)
            path = svc.write_manifest(
                svc.build_manifest(profile_name="mac_local", final_outcome="completed", artifact_bundle_ref="")
            )
            data = json.loads(path.read_text())
            self.assertEqual(data["run_id"], workspace.run_id)

    def test_manifest_json_contains_correct_session_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace, svc = self._build(tmpdir)
            path = svc.write_manifest(
                svc.build_manifest(profile_name="mac_local", final_outcome="completed", artifact_bundle_ref="")
            )
            data = json.loads(path.read_text())
            self.assertEqual(data["session_id"], workspace.session_id)

    def test_manifest_profile_name_matches_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace, svc = self._build(tmpdir)
            path = svc.write_manifest(
                svc.build_manifest(profile_name="mac_local", final_outcome="completed", artifact_bundle_ref="")
            )
            data = json.loads(path.read_text())
            self.assertEqual(data["profile_name"], "mac_local")

    def test_manifest_source_root_equals_repo_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace, svc = self._build(tmpdir)
            path = svc.write_manifest(
                svc.build_manifest(profile_name="mac_local", final_outcome="completed", artifact_bundle_ref="")
            )
            data = json.loads(path.read_text())
            self.assertEqual(data["source_root"], str(REPO_ROOT))


if __name__ == "__main__":
    unittest.main()
