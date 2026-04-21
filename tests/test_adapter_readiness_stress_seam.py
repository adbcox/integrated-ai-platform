"""Conformance tests for framework/adapter_readiness_stress.py (LARAC2-ADAPTER-READINESS-STRESS-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.adapter_readiness_stress import (
    StressCheck, StressHarnessResult, AdapterReadinessStressHarness, emit_stress_result
)
from framework.local_quality_score import LocalQualityScore
from framework.unified_local_metrics import UnifiedLocalMetrics
from framework.routing_policy_artifact import RoutingPolicyArtifact
from framework.failure_cluster_analysis import FailureClusterReport, FailureCluster


def _quality_score(raw_score=0.75, grade="B"):
    return LocalQualityScore(
        raw_score=raw_score, grade=grade,
        evidence_weight=0.85,
        first_pass_contribution=0.30,
        benchmark_contribution=0.25,
        reliability_contribution=0.20,
        computed_at="2026-01-01T00:00:00+00:00",
    )


def _unified_metrics(failure_rate=0.10, first_pass_rate=0.80):
    return UnifiedLocalMetrics(
        first_pass_rate=first_pass_rate, failure_rate=failure_rate,
        total_retry_burden=0.05, readiness_verdict="ready",
        task_classes_total=3,
        computed_at="2026-01-01T00:00:00+00:00",
    )


def _policy_artifact(policy_health="healthy"):
    return RoutingPolicyArtifact(
        policy_health=policy_health,
        current_threshold=0.6,
        overall_signal="hold",
        readiness_verdict="ready",
        suggestions_count=0,
        built_at="2026-01-01T00:00:00+00:00",
    )


def _cluster_report(n_clusters=2):
    clusters = [
        FailureCluster(
            cluster_key=f"text_replacement|SyntaxError|prefix{i}",
            task_kind="text_replacement",
            error_type="SyntaxError",
            error_prefix="prefix",
            occurrence_count=i + 1,
            example_summary="unexpected indent",
        )
        for i in range(n_clusters)
    ]
    return FailureClusterReport(
        clusters=clusters,
        total_failures_analyzed=n_clusters * 2,
        top_cluster_key=clusters[0].cluster_key if clusters else None,
        analyzed_at="2026-01-01T00:00:00+00:00",
    )


# --- import and type ---

def test_import_stress_harness():
    assert callable(AdapterReadinessStressHarness)


def test_returns_stress_harness_result():
    r = AdapterReadinessStressHarness().run()
    assert isinstance(r, StressHarnessResult)


# --- all-none returns unknown ---

def test_all_none_verdict_unknown():
    r = AdapterReadinessStressHarness().run()
    assert r.verdict == "unknown"


def test_all_none_quality_score_zero():
    r = AdapterReadinessStressHarness().run()
    assert r.quality_score == 0.0


# --- quality score check ---

def test_quality_score_passing():
    r = AdapterReadinessStressHarness().run(quality_score=_quality_score(0.75))
    qs_check = next(c for c in r.checks if c.check_name == "quality_score_sufficient")
    assert qs_check.passed is True


def test_quality_score_failing():
    r = AdapterReadinessStressHarness().run(quality_score=_quality_score(0.50))
    qs_check = next(c for c in r.checks if c.check_name == "quality_score_sufficient")
    assert qs_check.passed is False


def test_quality_score_none_fails_check():
    r = AdapterReadinessStressHarness().run(unified_metrics=_unified_metrics())
    qs_check = next(c for c in r.checks if c.check_name == "quality_score_sufficient")
    assert qs_check.passed is False


# --- failure rate check ---

def test_failure_rate_acceptable():
    r = AdapterReadinessStressHarness().run(unified_metrics=_unified_metrics(failure_rate=0.20))
    fr_check = next(c for c in r.checks if c.check_name == "failure_rate_acceptable")
    assert fr_check.passed is True


def test_failure_rate_too_high():
    r = AdapterReadinessStressHarness().run(unified_metrics=_unified_metrics(failure_rate=0.50))
    fr_check = next(c for c in r.checks if c.check_name == "failure_rate_acceptable")
    assert fr_check.passed is False


# --- routing policy check ---

def test_routing_policy_healthy():
    r = AdapterReadinessStressHarness().run(policy_artifact=_policy_artifact("healthy"))
    pol_check = next(c for c in r.checks if c.check_name == "routing_policy_not_degraded")
    assert pol_check.passed is True


def test_routing_policy_degraded():
    r = AdapterReadinessStressHarness().run(policy_artifact=_policy_artifact("degraded"))
    pol_check = next(c for c in r.checks if c.check_name == "routing_policy_not_degraded")
    assert pol_check.passed is False


# --- cluster check ---

def test_cluster_count_bounded():
    r = AdapterReadinessStressHarness().run(failure_clusters=_cluster_report(5))
    cl_check = next(c for c in r.checks if c.check_name == "failure_clusters_bounded")
    assert cl_check.passed is True


def test_cluster_count_exceeded():
    r = AdapterReadinessStressHarness().run(failure_clusters=_cluster_report(15))
    cl_check = next(c for c in r.checks if c.check_name == "failure_clusters_bounded")
    assert cl_check.passed is False


def test_cluster_none_passes():
    r = AdapterReadinessStressHarness().run(
        quality_score=_quality_score(), unified_metrics=_unified_metrics()
    )
    cl_check = next(c for c in r.checks if c.check_name == "failure_clusters_bounded")
    assert cl_check.passed is True


# --- stable / unstable verdicts ---

def test_stable_when_all_pass():
    r = AdapterReadinessStressHarness().run(
        quality_score=_quality_score(0.75),
        unified_metrics=_unified_metrics(failure_rate=0.10),
        policy_artifact=_policy_artifact("healthy"),
        failure_clusters=_cluster_report(2),
    )
    assert r.verdict == "stable"
    assert r.blocking_failures == 0


def test_unstable_when_quality_fails():
    r = AdapterReadinessStressHarness().run(
        quality_score=_quality_score(0.50),
        unified_metrics=_unified_metrics(failure_rate=0.10),
        policy_artifact=_policy_artifact("healthy"),
    )
    assert r.verdict == "unstable"
    assert r.blocking_failures >= 1


def test_unknown_when_metrics_missing():
    r = AdapterReadinessStressHarness().run(quality_score=_quality_score(0.75))
    assert r.verdict == "unknown"


# --- checks list ---

def test_checks_list_length():
    r = AdapterReadinessStressHarness().run()
    assert len(r.checks) == 4


def test_all_checks_are_stress_check():
    r = AdapterReadinessStressHarness().run()
    for c in r.checks:
        assert isinstance(c, StressCheck)


# --- artifact ---

def test_artifact_written(tmp_path):
    r = AdapterReadinessStressHarness().run()
    path = emit_stress_result(r, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_parseable(tmp_path):
    r = AdapterReadinessStressHarness().run()
    path = emit_stress_result(r, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "verdict" in data
    assert "checks" in data
    assert "blocking_failures" in data


def test_artifact_path_set(tmp_path):
    r = AdapterReadinessStressHarness().run()
    path = emit_stress_result(r, artifact_dir=tmp_path)
    assert r.artifact_path == path


# --- no adapter code ---

def test_no_adapter_code_imported():
    import framework.adapter_readiness_stress as m
    src = Path(m.__file__).read_text()
    assert "adapter_campaign" not in src
    assert "ControlledAdapter" not in src


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "AdapterReadinessStressHarness")
    assert hasattr(framework, "StressHarnessResult")
    assert hasattr(framework, "StressCheck")
    assert hasattr(framework, "emit_stress_result")
