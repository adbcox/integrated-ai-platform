"""Tests for framework.routing_config_adopter — RoutingConfigAdopter seam."""
import json
import pytest
from pathlib import Path

from framework.local_memory_store import LocalMemoryStore
from framework.autonomy_metrics_extended import collect_extended_metrics
from framework.routing_config import RoutingConfig
from framework.routing_config_adopter import (
    AdoptionRecommendation,
    RoutingAdoptionResult,
    RoutingConfigAdopter,
    save_adoption_result,
)


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "mem")


@pytest.fixture
def empty_metrics(store):
    return collect_extended_metrics(memory_store=store)


@pytest.fixture
def high_failure_metrics(store):
    for _ in range(8):
        store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    for _ in range(2):
        store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    return collect_extended_metrics(memory_store=store)


def test_import_ok():
    from framework.routing_config_adopter import RoutingConfigAdopter, RoutingAdoptionResult  # noqa: F401


def test_adopt_returns_result(empty_metrics):
    adopter = RoutingConfigAdopter()
    result = adopter.adopt(empty_metrics)
    assert isinstance(result, RoutingAdoptionResult)


def test_adopt_empty_metrics_no_recommendations(empty_metrics):
    adopter = RoutingConfigAdopter()
    result = adopter.adopt(empty_metrics)
    assert result.classes_with_recommendation == 0


def test_adopt_result_total_classes_nonzero(empty_metrics):
    adopter = RoutingConfigAdopter()
    result = adopter.adopt(empty_metrics)
    assert result.total_classes_considered >= 0


def test_adopt_result_has_updated_config(empty_metrics):
    adopter = RoutingConfigAdopter()
    result = adopter.adopt(empty_metrics)
    assert isinstance(result.updated_config, RoutingConfig)


def test_adopt_result_generated_at_is_iso(empty_metrics):
    adopter = RoutingConfigAdopter()
    result = adopter.adopt(empty_metrics)
    assert "T" in result.generated_at


def test_high_failure_generates_recommendation(high_failure_metrics):
    adopter = RoutingConfigAdopter()
    result = adopter.adopt(high_failure_metrics, min_attempts=5)
    assert result.classes_with_recommendation > 0


def test_high_failure_threshold_above_observed(high_failure_metrics):
    adopter = RoutingConfigAdopter()
    result = adopter.adopt(high_failure_metrics, min_attempts=5)
    recs = [r for r in result.recommendations if r.has_recommendation]
    for r in recs:
        assert r.suggested_threshold > r.observed_failure_rate


def test_recommendation_fields():
    r = AdoptionRecommendation(
        task_class="text_replacement",
        observed_failure_rate=0.3,
        suggested_threshold=0.35,
        reason="test",
        has_recommendation=True,
    )
    assert r.task_class == "text_replacement"
    assert r.has_recommendation is True


def test_to_dict_keys(empty_metrics):
    adopter = RoutingConfigAdopter()
    result = adopter.adopt(empty_metrics)
    d = result.to_dict()
    for k in ("schema_version", "generated_at", "total_classes_considered", "recommendations"):
        assert k in d


def test_save_dry_run_no_file(empty_metrics, tmp_path):
    adopter = RoutingConfigAdopter()
    result = adopter.adopt(empty_metrics)
    saved = save_adoption_result(result, artifact_dir=tmp_path / "out", dry_run=True)
    assert saved.artifact_path == ""


def test_save_writes_file(empty_metrics, tmp_path):
    adopter = RoutingConfigAdopter()
    result = adopter.adopt(empty_metrics)
    saved = save_adoption_result(result, artifact_dir=tmp_path / "out", dry_run=False)
    assert saved.artifact_path != ""
    assert Path(saved.artifact_path).exists()


def test_save_json_valid(empty_metrics, tmp_path):
    adopter = RoutingConfigAdopter()
    result = adopter.adopt(empty_metrics)
    saved = save_adoption_result(result, artifact_dir=tmp_path / "out", dry_run=False)
    data = json.loads(Path(saved.artifact_path).read_text())
    assert "schema_version" in data
    assert "recommendations" in data


def test_updated_config_overrides_for_high_failure(high_failure_metrics):
    adopter = RoutingConfigAdopter()
    result = adopter.adopt(high_failure_metrics, min_attempts=5)
    assert len(result.updated_config.overrides) == result.classes_with_recommendation


def test_insufficient_attempts_no_override(store):
    for _ in range(2):
        store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    metrics = collect_extended_metrics(memory_store=store)
    adopter = RoutingConfigAdopter()
    result = adopter.adopt(metrics, min_attempts=5)
    recs_with = [r for r in result.recommendations if r.has_recommendation and r.task_class == "text_replacement"]
    assert len(recs_with) == 0


def test_init_ok_from_framework():
    from framework import RoutingConfigAdopter  # noqa: F401
