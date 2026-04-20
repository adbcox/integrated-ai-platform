"""Tests for qualify_v4_artifact_builder."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

from bin.qualify_v4_artifact_builder import (  # noqa: E402
    _classify_target,
    build_attribution_payload,
    build_benchmark_payload,
)


class ClassifyTargetTest(unittest.TestCase):
    def test_framework_file(self) -> None:
        self.assertEqual(_classify_target("framework/worker_runtime.py"), "framework_code")

    def test_bin_script(self) -> None:
        self.assertEqual(_classify_target("bin/stage3_manager.py"), "bin_scripts")

    def test_test_file(self) -> None:
        self.assertEqual(_classify_target("tests/test_foo.py"), "test_code")

    def test_config_file(self) -> None:
        self.assertEqual(_classify_target("config/promotion_manifest.json"), "config_data")

    def test_shell_file(self) -> None:
        self.assertEqual(_classify_target("shell/common.sh"), "shell_scripts")

    def test_promotion_file(self) -> None:
        self.assertEqual(_classify_target("promotion/manifest.py"), "promotion_engine")

    def test_governance_file(self) -> None:
        self.assertEqual(_classify_target("governance/current_phase.json"), "governance_artifacts")

    def test_unknown_path_returns_other(self) -> None:
        self.assertEqual(_classify_target("docs/something.md"), "other")

    def test_absolute_path_with_framework_prefix(self) -> None:
        self.assertEqual(
            _classify_target("/Users/admin/repo/framework/worker_runtime.py"),
            "framework_code",
        )


class BuildBenchmarkPayloadTest(unittest.TestCase):
    def test_empty_rows_returns_empty_classes(self) -> None:
        result = build_benchmark_payload([])
        self.assertEqual(result["classes"], {})
        self.assertEqual(result["run_count"], 0)

    def test_rows_without_target_skipped(self) -> None:
        result = build_benchmark_payload([{"accepted": True}, {"accepted": False}])
        self.assertEqual(result["classes"], {})

    def test_two_accepted_zero_rejected_in_framework_passes(self) -> None:
        rows = [
            {"target_file": "framework/worker_runtime.py", "accepted": True},
            {"target_file": "framework/scheduler.py", "accepted": True},
        ]
        result = build_benchmark_payload(rows)
        self.assertIn("framework_code", result["classes"])
        self.assertTrue(result["classes"]["framework_code"]["passed"])
        self.assertAlmostEqual(result["classes"]["framework_code"]["acceptance_rate"], 1.0)

    def test_one_accepted_two_rejected_fails(self) -> None:
        rows = [
            {"target_file": "bin/foo.py", "accepted": True},
            {"target_file": "bin/bar.py", "accepted": False},
            {"target_file": "bin/baz.py", "accepted": False},
        ]
        result = build_benchmark_payload(rows)
        self.assertIn("bin_scripts", result["classes"])
        entry = result["classes"]["bin_scripts"]
        self.assertFalse(entry["passed"])
        self.assertAlmostEqual(entry["acceptance_rate"], round(1 / 3, 3))

    def test_mixed_directories_produce_separate_classes(self) -> None:
        rows = [
            {"target_file": "framework/worker_runtime.py", "accepted": True},
            {"target_file": "bin/stage3_manager.py", "accepted": True},
        ]
        result = build_benchmark_payload(rows)
        self.assertIn("framework_code", result["classes"])
        self.assertIn("bin_scripts", result["classes"])
        self.assertEqual(len(result["classes"]), 2)

    def test_run_count_matches_target_bearing_rows(self) -> None:
        rows = [
            {"target_file": "framework/a.py", "accepted": True},
            {"target_file": "bin/b.py", "accepted": True},
            {"accepted": True},  # no target, skipped
        ]
        result = build_benchmark_payload(rows)
        self.assertEqual(result["run_count"], 2)

    def test_exact_threshold_passes(self) -> None:
        rows = [
            {"target_file": "tests/a.py", "accepted": True},
            {"target_file": "tests/b.py", "accepted": False},
        ]
        result = build_benchmark_payload(rows)
        entry = result["classes"]["test_code"]
        self.assertAlmostEqual(entry["acceptance_rate"], 0.5)
        self.assertTrue(entry["passed"])


class BuildAttributionPayloadTest(unittest.TestCase):
    def test_empty_rows_returns_zeros(self) -> None:
        result = build_attribution_payload([])
        self.assertEqual(result["orchestration_delta"], 0.0)
        self.assertEqual(result["model_delta"], 0.0)
        self.assertEqual(result["run_count"], 0)

    def test_no_has_attribution_field(self) -> None:
        result = build_attribution_payload([])
        self.assertNotIn("has_attribution", result)

    def test_all_accepted_no_fallback_delta_is_one(self) -> None:
        rows = [
            {"accepted": True, "fallback_used": False},
            {"accepted": True, "fallback_used": False},
        ]
        result = build_attribution_payload(rows)
        self.assertAlmostEqual(result["orchestration_delta"], 1.0)
        self.assertAlmostEqual(result["model_delta"], 1.0)

    def test_mixed_fallback_computes_expected_delta(self) -> None:
        rows = [
            {"accepted": True, "fallback_used": False},
            {"accepted": True, "fallback_used": True},
            {"accepted": False, "fallback_used": True},
            {"accepted": False, "fallback_used": False},
        ]
        result = build_attribution_payload(rows)
        # accepted_rate = 2/4 = 0.5, fallback_rate = 2/4 = 0.5
        # orchestration_delta = 0.5 - 0.5 = 0.0
        # model_delta = (1 - 0.5) - 0.5 = 0.0
        self.assertAlmostEqual(result["orchestration_delta"], 0.0)
        self.assertAlmostEqual(result["model_delta"], 0.0)
        self.assertAlmostEqual(result["accepted_rate"], 0.5)
        self.assertAlmostEqual(result["fallback_rate"], 0.5)

    def test_run_count_matches_total_rows(self) -> None:
        rows = [{"accepted": True, "fallback_used": False}] * 5
        result = build_attribution_payload(rows)
        self.assertEqual(result["run_count"], 5)

    def test_source_field_is_stage3_traces(self) -> None:
        result = build_attribution_payload([])
        self.assertEqual(result["source"], "stage3_traces")


class IntegrationTest(unittest.TestCase):
    """Run builder against real traces and verify gate activation."""

    def test_gates_ready_from_real_traces(self) -> None:
        import tempfile
        import os
        sys.path.insert(0, str(REPO_ROOT / "bin"))

        trace_path = REPO_ROOT / "artifacts" / "stage3_manager" / "traces.jsonl"
        if not trace_path.exists():
            self.skipTest("traces.jsonl not found")

        from bin.qualify_v4_artifact_builder import _load_jsonl
        rows = _load_jsonl(trace_path)
        if not rows:
            self.skipTest("traces.jsonl is empty")

        benchmark_payload = build_benchmark_payload(rows)
        attribution_payload = build_attribution_payload(rows)

        self.assertGreater(len(benchmark_payload["classes"]), 0, "Expected at least one benchmark class")

        with tempfile.TemporaryDirectory() as tmpdir:
            bench_out = Path(tmpdir) / "benchmark" / "latest.json"
            attr_out = Path(tmpdir) / "attribution" / "latest.json"
            bench_out.parent.mkdir(parents=True)
            attr_out.parent.mkdir(parents=True)
            bench_out.write_text(json.dumps(benchmark_payload) + "\n", encoding="utf-8")
            attr_out.write_text(json.dumps(attribution_payload) + "\n", encoding="utf-8")

            from bin.level10_qualify import (
                evaluate_v8_gates,
                summarize_attribution,
                summarize_benchmark,
            )

            bench_loaded = json.loads(bench_out.read_text())
            attr_loaded = json.loads(attr_out.read_text())

            bench_stats = summarize_benchmark(bench_loaded)
            attr_stats = summarize_attribution(attr_loaded)

            gates = evaluate_v8_gates(
                manifest_data={"promotion_policy": {"criteria": {"benchmark_min_class_count": 1}}},
                stage8_stats={},
                rag6_stats={},
                assessments={},
                gate_chain_stats={},
                benchmark_stats=bench_stats,
                attribution_stats=attr_stats,
            )

            self.assertTrue(
                gates["gates"]["benchmark8_ready"],
                f"benchmark8_ready must be True; bench_stats={bench_stats}",
            )
            self.assertTrue(
                gates["gates"]["attribution8_ready"],
                f"attribution8_ready must be True; attr_stats={attr_stats}",
            )

    def test_artifact_files_written_correctly(self) -> None:
        import tempfile

        trace_path = REPO_ROOT / "artifacts" / "stage3_manager" / "traces.jsonl"
        if not trace_path.exists():
            self.skipTest("traces.jsonl not found")

        from bin.qualify_v4_artifact_builder import _load_jsonl
        rows = _load_jsonl(trace_path)
        if not rows:
            self.skipTest("traces.jsonl is empty")

        with tempfile.TemporaryDirectory() as tmpdir:
            bench_out = Path(tmpdir) / "b" / "latest.json"
            attr_out = Path(tmpdir) / "a" / "latest.json"
            bench_out.parent.mkdir(parents=True)
            attr_out.parent.mkdir(parents=True)

            bench_payload = build_benchmark_payload(rows)
            attr_payload = build_attribution_payload(rows)
            bench_out.write_text(json.dumps(bench_payload) + "\n", encoding="utf-8")
            attr_out.write_text(json.dumps(attr_payload) + "\n", encoding="utf-8")

            self.assertTrue(bench_out.exists())
            self.assertTrue(attr_out.exists())

            bench_data = json.loads(bench_out.read_text())
            attr_data = json.loads(attr_out.read_text())

            self.assertIn("classes", bench_data)
            self.assertIn("orchestration_delta", attr_data)
            self.assertIn("model_delta", attr_data)


if __name__ == "__main__":
    unittest.main()
