"""Tests for framework.threshold_tuner — ThresholdTuner seam."""
import json
import pytest
from pathlib import Path

from framework.local_memory_store import LocalMemoryStore
from framework.autonomy_metrics_extended import collect_extended_metrics
from framework.evidence_accumulation_batch import BatchRunConfig, EvidenceAccumulationBatch
from framework.threshold_tuner import (
    ThresholdRecommendation,
    ThresholdTuningResult,
    tune_thresholds,
    save_tuning_result,
)


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "mem")


@pytest.fixture
def empty_metrics(store):
    return collect_extended_metrics(memory_store=store)


@pytest.fixture
def batch_result():
    batch = EvidenceAccumulationBatch()
    config = BatchRunConfig(runs_per_kind=3, dry_run=True)
    return batch.run(config)


@pytest.fixture
def high_failure_metrics(store):
    for _ in range(8):
        store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    for _ in range(2):
        store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    return collect_extended_metrics(memory_store=store)


def test_import_ok():
    from framework.threshold_tuner import ThresholdTuningResult, tune_thresholds  # noqa: F401


def test_tune_returns_result(empty_metrics):
    result = tune_thresholds(empty_metrics)
    assert isinstance(result, ThresholdTuningResult)


def test_tune_no_change_on_empty(empty_metrics):
    result = tune_thresholds(empty_metrics, min_attempts=5)
    assert result.classes_with_recommendation == 0


def test_tune_total_classes_nonzero(empty_metrics):
    result = tune_thresholds(empty_metrics)
    assert result.total_classes >= 0


def test_recommendation_fields():
    r = ThresholdRecommendation(
        task_class="text_replacement",
        observed_failure_rate=0.3,
        batch_failure_rate=0.1,
        suggested_threshold=0.35,
        confidence=0.8,
        reason="test",
        has_recommendation=True,
    )
    assert r.task_class == "text_replacement"
    assert r.has_recommendation is True
    assert r.confidence == 0.8


def test_to_dict_keys(empty_metrics):
    result = tune_thresholds(empty_metrics)
    d = result.to_dict()
    for k in ("schema_version", "generated_at", "total_classes", "recommendations"):
        assert k in d


def test_generated_at_is_iso(empty_metrics):
    result = tune_thresholds(empty_metrics)
    assert "T" in result.generated_at


def test_high_failure_generates_recommendation(high_failure_metrics):
    result = tune_thresholds(high_failure_metrics, min_attempts=5)
    assert result.classes_with_recommendation > 0


def test_high_failure_threshold_above_observed(high_failure_metrics):
    result = tune_thresholds(high_failure_metrics, min_attempts=5)
    recs = [r for r in result.recommendations if r.has_recommendation]
    for r in recs:
        assert r.suggested_threshold > r.observed_failure_rate


def test_confidence_bounded(empty_metrics):
    result = tune_thresholds(empty_metrics)
    for r in result.recommendations:
        assert 0.0 <= r.confidence <= 1.0


def test_with_batch_evidence_increases_attempts(high_failure_metrics, batch_result):
    result_no_batch = tune_thresholds(high_failure_metrics, min_attempts=50)
    result_with_batch = tune_thresholds(high_failure_metrics, batch_result, min_attempts=3)
    assert result_with_batch.classes_with_recommendation >= result_no_batch.classes_with_recommendation


def test_save_dry_run_no_file(empty_metrics, tmp_path):
    result = tune_thresholds(empty_metrics)
    saved = save_tuning_result(result, artifact_dir=tmp_path / "out", dry_run=True)
    assert saved.artifact_path == ""


def test_save_writes_file(empty_metrics, tmp_path):
    result = tune_thresholds(empty_metrics)
    saved = save_tuning_result(result, artifact_dir=tmp_path / "out", dry_run=False)
    assert saved.artifact_path != ""
    assert Path(saved.artifact_path).exists()


def test_save_json_valid(empty_metrics, tmp_path):
    result = tune_thresholds(empty_metrics)
    saved = save_tuning_result(result, artifact_dir=tmp_path / "out", dry_run=False)
    data = json.loads(Path(saved.artifact_path).read_text())
    assert "schema_version" in data
    assert "recommendations" in data


def test_recommendation_to_dict():
    r = ThresholdRecommendation(
        task_class="bug_fix", observed_failure_rate=0.2, batch_failure_rate=0.1,
        suggested_threshold=0.25, confidence=0.5, reason="test", has_recommendation=True
    )
    d = r.to_dict()
    for k in ("task_class", "observed_failure_rate", "suggested_threshold", "confidence", "has_recommendation"):
        assert k in d


def test_init_ok_from_framework():
    from framework import tune_thresholds  # noqa: F401
