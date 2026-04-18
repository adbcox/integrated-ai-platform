"""Tests for Phase 2 typed tool implementation validation."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


class TestPhase2ToolImplValidation(unittest.TestCase):
    def test_validation_report_all_checks_pass(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        report = None
        try:
            from artifacts.phase2_tool_impl_validation_report import (
                generate_phase2_tool_impl_validation_report,
            )
            report = generate_phase2_tool_impl_validation_report()
        except Exception as exc:
            self.fail(f"generate_phase2_tool_impl_validation_report raised: {exc}")

        self.assertIsInstance(report, dict)
        checks = report.get("checks", [])
        failed = [c for c in checks if not c.get("passed")]
        self.assertTrue(
            report.get("all_checks_pass"),
            msg=f"all_checks_pass is False; failed checks: {failed}",
        )

    def test_required_typed_tools_constant(self):
        from framework.runtime_validation_pack import REQUIRED_PHASE2_TYPED_TOOLS
        self.assertIn("read_file", REQUIRED_PHASE2_TYPED_TOOLS)
        self.assertIn("list_dir", REQUIRED_PHASE2_TYPED_TOOLS)
        self.assertIn("git_diff", REQUIRED_PHASE2_TYPED_TOOLS)
        self.assertIn("run_tests", REQUIRED_PHASE2_TYPED_TOOLS)

    def test_allow_run_produces_four_tool_names(self):
        from framework.runtime_validation_pack import (
            REQUIRED_PHASE2_TYPED_TOOLS,
            run_phase2_typed_tool_validation,
        )
        with tempfile.TemporaryDirectory(prefix="p2_impl_allow_") as d:
            result = run_phase2_typed_tool_validation(
                allow_all_tools=True,
                tmp_root=Path(d),
            )
        typed_trace = result.get("typed_tool_trace", [])
        observed = {
            e.get("tool_name")
            for e in typed_trace
            if e.get("kind") == "tool_observation"
        }
        for tool in REQUIRED_PHASE2_TYPED_TOOLS:
            self.assertIn(tool, observed, msg=f"{tool} not in typed_tool_trace: {observed}")

    def test_block_run_produces_blocked_observations(self):
        from framework.runtime_validation_pack import run_phase2_typed_tool_validation
        with tempfile.TemporaryDirectory(prefix="p2_impl_block_") as d:
            result = run_phase2_typed_tool_validation(
                allow_all_tools=False,
                tmp_root=Path(d),
            )
        typed_trace = result.get("typed_tool_trace", [])
        blocked = [
            e for e in typed_trace
            if e.get("kind") == "tool_observation"
            and e.get("status") == "blocked"
            and e.get("allowed") is False
        ]
        self.assertGreaterEqual(len(blocked), 1, msg="No blocked observations found")


if __name__ == "__main__":
    unittest.main()
