"""Tests for framework.readiness_evaluator — readiness evaluation seam."""
import json
import pytest
from pathlib import Path

from framework.local_memory_store import LocalMemoryStore
from framework.readiness_evaluator import (
    ReadinessCriterion,
    ReadinessEvaluation,
    evaluate_readiness,
)


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "memory")


@pytest.fixture
def artifact_dir(tmp_path):
    return tmp_path / "readiness"


def test_import_ok():
    from framework.readiness_evaluator import evaluate_readiness, ReadinessEvaluation  # noqa: F401


def test_evaluate_returns_readiness_evaluation(store, artifact_dir):
    result = evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert isinstance(result, ReadinessEvaluation)


def test_empty_store_deferred(store, artifact_dir):
    result = evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert result.readiness_verdict == "deferred_pending_evidence"


def test_empty_store_zero_attempts(store, artifact_dir):
    result = evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert result.total_attempts == 0


def test_criteria_count(store, artifact_dir):
    result = evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert len(result.criteria) == 3


def test_criteria_names(store, artifact_dir):
    result = evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    names = {c.name for c in result.criteria}
    assert "min_attempts" in names
    assert "max_failure_rate" in names
    assert "max_escalation_rate" in names


def test_empty_store_all_criteria_not_all_passed(store, artifact_dir):
    result = evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert not result.all_criteria_passed


def test_defer_reasons_non_empty_on_insufficient(store, artifact_dir):
    result = evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert len(result.defer_reasons) > 0


def test_all_criteria_passed_when_met(store, artifact_dir):
    for _ in range(13):
        store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    for _ in range(2):
        store.record_failure(task_kind="text_replacement", target_file="b.py", old_string="z", error="err")
    result = evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert result.all_criteria_passed
    assert result.readiness_verdict == "ready_for_controlled_adapter_campaign"


def test_high_failure_rate_deferred(store, artifact_dir):
    for _ in range(10):
        store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    result = evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert result.readiness_verdict == "deferred_pending_evidence"


def test_to_dict_keys(store, artifact_dir):
    result = evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    d = result.to_dict()
    for k in ("schema_version", "readiness_verdict", "total_attempts", "criteria", "all_criteria_passed"):
        assert k in d, f"Missing key: {k}"


def test_dry_run_no_artifact(store, artifact_dir):
    evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert not artifact_dir.exists()


def test_non_dry_run_writes_artifact(store, artifact_dir):
    result = evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=False)
    assert result.artifact_path != ""
    assert Path(result.artifact_path).exists()


def test_artifact_json_valid(store, artifact_dir):
    result = evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=False)
    data = json.loads(Path(result.artifact_path).read_text())
    assert "schema_version" in data
    assert "readiness_verdict" in data


def test_evaluated_at_is_iso(store, artifact_dir):
    result = evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert "T" in result.evaluated_at


def test_summary_lines_returns_list(store, artifact_dir):
    result = evaluate_readiness(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    lines = result.summary_lines()
    assert isinstance(lines, list)
    assert len(lines) >= 3
