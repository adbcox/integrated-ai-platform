"""Tests for artifacts.phase2_runtime_wire_validation_report."""

from __future__ import annotations

import unittest

from artifacts.phase2_runtime_wire_validation_report import (
    generate_phase2_runtime_wire_validation_report,
)


class Phase2RuntimeWireValidationTest(unittest.TestCase):
    def test_all_checks_pass(self) -> None:
        report = generate_phase2_runtime_wire_validation_report()
        self.assertTrue(
            report.get("all_checks_pass"),
            msg=f"report not passing: {report!r}",
        )
        self.assertEqual(report.get("status"), "pass")
        self.assertEqual(
            report.get("phase2_runtime_wire_check"), "phase2_runtime_wire"
        )
        self.assertTrue(report.get("allow_shape_ok"))
        self.assertTrue(report.get("block_shape_ok"))
        self.assertTrue(report.get("allow_final_outcome_completed"))
        self.assertTrue(report.get("block_has_blocked_run_command"))
        self.assertTrue(report.get("allow_persisted_phase2_flag"))
        self.assertTrue(report.get("block_persisted_phase2_flag"))


if __name__ == "__main__":
    unittest.main()
