"""Conformance tests for framework/threshold_suggester.py (LARAC2-THRESHOLD-SUGGESTION-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.threshold_suggester import (
    ThresholdSuggestion, ThresholdSuggestions, derive_threshold_suggestions, emit_threshold_suggestions
)
from framework.local_quality_score import LocalQualityScore
from framework.task_class_readiness import TaskClassReadinessReport
from framework.routing_config import RoutingConfig, DEFAULT_ROUTING_CONFIG


def _score(raw=0.75, grade="B"):
    return LocalQualityScore(
        raw_score=raw, grade=grade, evidence_weight=0.85,
        first_pass_contribution=0.3, benchmark_contribution=0.3,
        reliability_contribution=0.15, computed_at="now",
    )


def _readiness(verdict="ready"):
    return TaskClassReadinessReport(
        verdicts=(), overall_verdict=verdict, ready_count=1,
        marginal_count=0, not_ready_count=0, evaluated_at="now"
    )


# --- import and type ---

def test_import_derive_threshold_suggestions():
    assert callable(derive_threshold_suggestions)


def test_returns_threshold_suggestions():
    s = derive_threshold_suggestions(_score())
    assert isinstance(s, ThresholdSuggestions)


# --- fields ---

def test_suggestions_fields_present():
    s = derive_threshold_suggestions(_score())
    assert hasattr(s, "suggestions")
    assert hasattr(s, "overall_signal")
    assert hasattr(s, "computed_at")


# --- no config works ---

def test_no_config_works():
    s = derive_threshold_suggestions(_score(), current_config=None)
    assert isinstance(s, ThresholdSuggestions)


# --- readiness None works ---

def test_no_readiness_works():
    s = derive_threshold_suggestions(_score(), readiness_report=None)
    assert isinstance(s, ThresholdSuggestions)


# --- signal values ---

def test_overall_signal_valid():
    s = derive_threshold_suggestions(_score())
    assert s.overall_signal in {"increase_threshold", "hold", "reduce_threshold"}


def test_not_ready_produces_reduce():
    s = derive_threshold_suggestions(_score(raw=0.4, grade="D"), readiness_report=_readiness("not_ready"))
    assert s.overall_signal == "reduce_threshold"


def test_high_score_ready_produces_increase_or_hold():
    s = derive_threshold_suggestions(_score(raw=0.90, grade="A"), readiness_report=_readiness("ready"))
    assert s.overall_signal in {"increase_threshold", "hold"}


# --- suggestions are advisory only (no config mutation) ---

def test_no_config_mutation():
    config = DEFAULT_ROUTING_CONFIG
    original_threshold = config.global_threshold
    derive_threshold_suggestions(_score(), current_config=config)
    assert config.global_threshold == original_threshold


# --- emit artifact ---

def test_artifact_written(tmp_path):
    s = derive_threshold_suggestions(_score())
    path = emit_threshold_suggestions(s, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_parseable(tmp_path):
    s = derive_threshold_suggestions(_score())
    path = emit_threshold_suggestions(s, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "overall_signal" in data
    assert "suggestions" in data


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "derive_threshold_suggestions")
    assert hasattr(framework, "ThresholdSuggestions")
    assert hasattr(framework, "ThresholdSuggestion")
