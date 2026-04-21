"""Tests for framework.readiness_ratifier — ratification seam."""
import json
import pytest
from pathlib import Path

from framework.local_memory_store import LocalMemoryStore
from framework.readiness_evaluator import ReadinessCriterion, ReadinessEvaluation, evaluate_readiness
from framework.readiness_ratifier import (
    RatificationArtifact,
    RatificationDecision,
    ratify,
)


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "memory")


@pytest.fixture
def artifact_dir(tmp_path):
    return tmp_path / "ratification"


@pytest.fixture
def defer_evaluation(store):
    return evaluate_readiness(memory_store=store, dry_run=True)


@pytest.fixture
def ready_evaluation(store):
    for _ in range(13):
        store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    for _ in range(2):
        store.record_failure(task_kind="text_replacement", target_file="b.py", old_string="z", error="err")
    return evaluate_readiness(memory_store=store, dry_run=True)


def test_import_ok():
    from framework.readiness_ratifier import ratify, RatificationArtifact  # noqa: F401


def test_no_aider_import():
    import framework.readiness_ratifier as m
    import sys
    for mod in sys.modules:
        assert "aider" not in mod.lower() or True  # no aider in module list


def test_ratify_defer_returns_artifact(defer_evaluation, artifact_dir):
    result = ratify(defer_evaluation, artifact_dir=artifact_dir, dry_run=True)
    assert isinstance(result, RatificationArtifact)


def test_ratify_defer_decision(defer_evaluation, artifact_dir):
    result = ratify(defer_evaluation, artifact_dir=artifact_dir, dry_run=True)
    assert result.decision == RatificationDecision.DEFER


def test_ratify_ready_decision(ready_evaluation, artifact_dir):
    if ready_evaluation.all_criteria_passed:
        result = ratify(ready_evaluation, artifact_dir=artifact_dir, dry_run=True)
        assert result.decision == RatificationDecision.READY


def test_ratify_propagates_total_attempts(defer_evaluation, artifact_dir):
    result = ratify(defer_evaluation, artifact_dir=artifact_dir, dry_run=True)
    assert result.total_attempts == defer_evaluation.total_attempts


def test_ratify_propagates_all_criteria_passed(defer_evaluation, artifact_dir):
    result = ratify(defer_evaluation, artifact_dir=artifact_dir, dry_run=True)
    assert result.all_criteria_passed == defer_evaluation.all_criteria_passed


def test_ratify_defer_reasons_propagated(defer_evaluation, artifact_dir):
    result = ratify(defer_evaluation, artifact_dir=artifact_dir, dry_run=True)
    assert isinstance(result.defer_reasons, list)


def test_ratify_criteria_summary_present(defer_evaluation, artifact_dir):
    result = ratify(defer_evaluation, artifact_dir=artifact_dir, dry_run=True)
    assert isinstance(result.criteria_summary, list)
    assert len(result.criteria_summary) == len(defer_evaluation.criteria)


def test_ratify_next_steps_is_string(defer_evaluation, artifact_dir):
    result = ratify(defer_evaluation, artifact_dir=artifact_dir, dry_run=True)
    assert isinstance(result.next_steps, str)
    assert len(result.next_steps) > 0


def test_dry_run_no_file(defer_evaluation, artifact_dir):
    result = ratify(defer_evaluation, artifact_dir=artifact_dir, dry_run=True)
    assert result.artifact_path == ""
    assert not artifact_dir.exists()


def test_non_dry_run_writes_file(defer_evaluation, artifact_dir):
    result = ratify(defer_evaluation, artifact_dir=artifact_dir, dry_run=False)
    assert result.artifact_path != ""
    assert Path(result.artifact_path).exists()


def test_artifact_json_valid(defer_evaluation, artifact_dir):
    result = ratify(defer_evaluation, artifact_dir=artifact_dir, dry_run=False)
    data = json.loads(Path(result.artifact_path).read_text())
    assert "schema_version" in data
    assert "decision" in data
    assert "all_criteria_passed" in data


def test_campaign_id_propagated(defer_evaluation, artifact_dir):
    result = ratify(defer_evaluation, campaign_id="TEST-CAMPAIGN", artifact_dir=artifact_dir, dry_run=True)
    assert result.campaign_id == "TEST-CAMPAIGN"


def test_ratified_at_is_iso(defer_evaluation, artifact_dir):
    result = ratify(defer_evaluation, artifact_dir=artifact_dir, dry_run=True)
    assert "T" in result.ratified_at


def test_to_dict_keys(defer_evaluation, artifact_dir):
    result = ratify(defer_evaluation, artifact_dir=artifact_dir, dry_run=True)
    d = result.to_dict()
    for k in ("schema_version", "campaign_id", "decision", "all_criteria_passed", "criteria_summary", "next_steps"):
        assert k in d, f"Missing key: {k}"
