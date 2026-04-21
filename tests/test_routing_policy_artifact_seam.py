"""Conformance tests for framework/routing_policy_artifact.py (LARAC2-ROUTING-POLICY-ARTIFACT-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.routing_policy_artifact import RoutingPolicyArtifact, build_routing_policy_artifact, emit_routing_policy
from framework.routing_config import DEFAULT_ROUTING_CONFIG
from framework.threshold_suggester import ThresholdSuggestions
from framework.task_class_readiness import TaskClassReadinessReport


def _suggestions(signal="hold"):
    return ThresholdSuggestions(suggestions=(), overall_signal=signal, computed_at="now")


def _readiness(verdict="ready"):
    return TaskClassReadinessReport(
        verdicts=(), overall_verdict=verdict, ready_count=1,
        marginal_count=0, not_ready_count=0, evaluated_at="now"
    )


# --- import and type ---

def test_import_build_routing_policy_artifact():
    assert callable(build_routing_policy_artifact)


def test_returns_routing_policy_artifact():
    r = build_routing_policy_artifact()
    assert isinstance(r, RoutingPolicyArtifact)


# --- fields ---

def test_artifact_fields_present():
    r = build_routing_policy_artifact()
    assert hasattr(r, "current_threshold")
    assert hasattr(r, "overall_signal")
    assert hasattr(r, "readiness_verdict")
    assert hasattr(r, "suggestions_count")
    assert hasattr(r, "policy_health")
    assert hasattr(r, "built_at")


# --- defaults ---

def test_all_none_works():
    r = build_routing_policy_artifact(routing_config=None, threshold_suggestions=None, readiness_report=None)
    assert isinstance(r, RoutingPolicyArtifact)


def test_unknown_when_no_inputs():
    r = build_routing_policy_artifact()
    assert r.overall_signal == "unknown"
    assert r.readiness_verdict == "unknown"
    assert r.policy_health == "unknown"


# --- populated inputs ---

def test_threshold_from_config():
    r = build_routing_policy_artifact(routing_config=DEFAULT_ROUTING_CONFIG)
    assert r.current_threshold == DEFAULT_ROUTING_CONFIG.global_threshold


def test_signal_from_suggestions():
    r = build_routing_policy_artifact(threshold_suggestions=_suggestions("increase_threshold"))
    assert r.overall_signal == "increase_threshold"


def test_readiness_from_report():
    r = build_routing_policy_artifact(readiness_report=_readiness("ready"))
    assert r.readiness_verdict == "ready"


# --- policy_health logic ---

def test_not_ready_is_degraded():
    r = build_routing_policy_artifact(
        threshold_suggestions=_suggestions("hold"),
        readiness_report=_readiness("not_ready")
    )
    assert r.policy_health == "degraded"


def test_healthy_when_ready_hold():
    r = build_routing_policy_artifact(
        threshold_suggestions=_suggestions("hold"),
        readiness_report=_readiness("ready")
    )
    assert r.policy_health == "healthy"


# --- emit artifact ---

def test_artifact_written(tmp_path):
    r = build_routing_policy_artifact()
    path = emit_routing_policy(r, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_parseable(tmp_path):
    r = build_routing_policy_artifact()
    path = emit_routing_policy(r, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "policy_health" in data
    assert "current_threshold" in data


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "RoutingPolicyArtifact")
    assert hasattr(framework, "build_routing_policy_artifact")
    assert hasattr(framework, "emit_routing_policy")
