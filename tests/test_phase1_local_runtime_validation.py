"""End-to-end offline test for the Phase 1 baseline local runtime validation pack."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from framework.runtime_validation_pack import (
    DEFAULT_TASK_CLASS,
    ValidationPackResult,
    run_baseline_validation,
)


def _fake_executor(request, profile):
    return f"stub-output profile={profile.profile_name} prompt_len={len(request.prompt)}"


class Phase1LocalRuntimeValidationTest(unittest.TestCase):
    def test_baseline_validation_succeeds_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as base:
            result = run_baseline_validation(
                source_root=Path(src),
                base_root=Path(base),
                run_id="phase1-run-1",
                session_id="phase1-test",
                executor=_fake_executor,
            )
            self.assertIsInstance(result, ValidationPackResult)
            self.assertTrue(result.success, msg=result.to_dict())
            self.assertTrue(result.manifest_path.exists())
            payload = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["run_id"], "phase1-run-1")
            self.assertEqual(payload["session_id"], "phase1-test")
            self.assertEqual(payload["final_outcome"], "completed")
            self.assertGreaterEqual(len(payload["command_records"]), 1)
            self.assertGreaterEqual(len(payload["validation_records"]), 2)
            self.assertGreaterEqual(len(payload["inference_records"]), 1)
            self.assertGreaterEqual(len(payload["workspace_side_effects"]), 1)

    def test_manifest_references_chosen_profile(self) -> None:
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as base:
            result = run_baseline_validation(
                source_root=Path(src),
                base_root=Path(base),
                run_id="phase1-run-2",
                session_id="phase1-test",
                task_class=DEFAULT_TASK_CLASS,
                executor=_fake_executor,
            )
            self.assertTrue(result.success)
            self.assertEqual(result.manifest.profile_name, result.inference.profile_name)

    def test_failing_command_marks_failure(self) -> None:
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as base:
            result = run_baseline_validation(
                source_root=Path(src),
                base_root=Path(base),
                run_id="phase1-run-3",
                session_id="phase1-test",
                command=["python3", "-c", "import sys; sys.exit(1)"],
                executor=_fake_executor,
            )
            self.assertFalse(result.success)
            self.assertEqual(result.manifest.final_outcome, "failed")

    def test_second_run_does_not_reuse_first_run_paths(self) -> None:
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as base:
            r1 = run_baseline_validation(
                source_root=Path(src),
                base_root=Path(base),
                run_id="phase1-run-A",
                session_id="phase1-test",
                executor=_fake_executor,
            )
            r2 = run_baseline_validation(
                source_root=Path(src),
                base_root=Path(base),
                run_id="phase1-run-B",
                session_id="phase1-test",
                executor=_fake_executor,
            )
            self.assertNotEqual(r1.manifest_path, r2.manifest_path)
            self.assertTrue(r1.success and r2.success)


if __name__ == "__main__":
    unittest.main()
