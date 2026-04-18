"""Tests for artifacts.phase2_schema_entry_validation_report."""

from __future__ import annotations

import unittest

from artifacts.phase2_schema_entry_validation_report import (
    generate_phase2_schema_entry_validation_report,
)


class Phase2SchemaEntryValidationTest(unittest.TestCase):
    def test_all_checks_pass(self) -> None:
        report = generate_phase2_schema_entry_validation_report()
        self.assertTrue(
            report.get("all_checks_pass"),
            msg=f"report not passing: {report!r}",
        )
        self.assertEqual(report.get("status"), "pass")
        self.assertEqual(report.get("phase2_entry_check"), "phase2_schema_entry")
        self.assertTrue(report.get("contracts_present"))
        self.assertTrue(report.get("required_tools_present"))
        self.assertTrue(report.get("serialization_ok"))
        self.assertTrue(report.get("blocked_observation_ok"))
        self.assertTrue(report.get("bundle_shape_ok"))


if __name__ == "__main__":
    unittest.main()
