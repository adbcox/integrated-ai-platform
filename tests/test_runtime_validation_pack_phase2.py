"""Tests for the Phase 2 runtime validation helper in runtime_validation_pack."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from framework.runtime_validation_pack import (
    REQUIRED_PHASE2_RUNTIME_KEYS,
    assert_phase2_runtime_keys_present,
    run_phase2_runtime_wire_validation,
)


class RuntimeValidationPackPhase2Test(unittest.TestCase):
    def test_required_keys_frozen_set_stable(self) -> None:
        self.assertEqual(
            REQUIRED_PHASE2_RUNTIME_KEYS,
            frozenset(
                {
                    "canonical_session",
                    "canonical_jobs",
                    "typed_tool_trace",
                    "permission_decisions",
                    "session_bundle",
                    "final_outcome",
                }
            ),
        )

    def test_allowed_path_returns_all_required_keys(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            r = run_phase2_runtime_wire_validation(
                allow_run_command=True, tmp_root=Path(td)
            )
        assert_phase2_runtime_keys_present(r)
        self.assertEqual(r["final_outcome"], "completed")

    def test_blocked_path_returns_all_required_keys(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            r = run_phase2_runtime_wire_validation(
                allow_run_command=False, tmp_root=Path(td)
            )
        assert_phase2_runtime_keys_present(r)
        self.assertIn(r["final_outcome"], {"failed", "escalated"})

    def test_assert_helper_raises_on_missing_keys(self) -> None:
        with self.assertRaises(AssertionError):
            assert_phase2_runtime_keys_present({"canonical_session": {}})


if __name__ == "__main__":
    unittest.main()
