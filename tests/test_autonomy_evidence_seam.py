"""Tests for framework.autonomy_evidence — local-autonomy evidence seam."""
import ast
import json
import pytest
from pathlib import Path

from framework.autonomy_evidence import (
    AutonomyEvidenceResult,
    TaskClassMetrics,
    collect_autonomy_evidence,
)
from framework.local_memory_store import LocalMemoryStore
from framework.task_prompt_pack import SUPPORTED_TASK_CLASSES


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "memory")


@pytest.fixture
def artifact_dir(tmp_path):
    return tmp_path / "evidence"


def test_import_ok():
    from framework.autonomy_evidence import collect_autonomy_evidence  # noqa: F401


def test_collect_returns_autonomy_evidence_result(store, artifact_dir):
    result = collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert isinstance(result, AutonomyEvidenceResult)


def test_collect_total_task_classes_matches_supported(store, artifact_dir):
    result = collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert result.total_task_classes == len(SUPPORTED_TASK_CLASSES)


def test_collect_task_class_metrics_count(store, artifact_dir):
    result = collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert len(result.task_class_metrics) == len(SUPPORTED_TASK_CLASSES)


def test_collect_with_empty_memory_has_zero_counts(store, artifact_dir):
    result = collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert result.overall_success_count == 0
    assert result.overall_failure_count == 0


def test_collect_counts_successes(store, artifact_dir):
    store.record_success(task_kind="text_replacement", target_file="f.py", old_string="x", new_string="y")
    store.record_success(task_kind="bug_fix", target_file="g.py", old_string="a", new_string="b")
    result = collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert result.overall_success_count == 2


def test_collect_counts_failures(store, artifact_dir):
    store.record_failure(task_kind="text_replacement", target_file="f.py", old_string="x", error="err")
    result = collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert result.overall_failure_count == 1


def test_collect_failure_rate_all_failures(store, artifact_dir):
    store.record_failure(task_kind="text_replacement", target_file="f.py", old_string="x", error="err")
    result = collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert result.overall_failure_rate == pytest.approx(1.0)


def test_collect_failure_rate_mixed(store, artifact_dir):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    store.record_failure(task_kind="text_replacement", target_file="b.py", old_string="z", error="err")
    result = collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert result.overall_failure_rate == pytest.approx(0.5)


def test_collect_aider_deferred_with_no_data(store, artifact_dir):
    result = collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert result.aider_readiness_decision == "deferred"


def test_collect_aider_deferred_high_failure_rate(store, artifact_dir):
    for _ in range(4):
        store.record_failure(task_kind="text_replacement", target_file="f.py", old_string="x", error="err")
    for _ in range(6):
        store.record_success(task_kind="text_replacement", target_file="g.py", old_string="y", new_string="z")
    # 40% failure rate but only 10 attempts, with failure_rate >= 30%
    result = collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert result.aider_readiness_decision == "deferred"


def test_collect_aider_ready_when_all_criteria_met(store, artifact_dir):
    # 15 attempts, 2 failures = 13.3% failure rate, 0 escalations
    for _ in range(13):
        store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    for _ in range(2):
        store.record_failure(task_kind="text_replacement", target_file="b.py", old_string="z", error="err")
    result = collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert result.aider_readiness_decision == "ready_for_controlled_adapter_campaign"


def test_collect_writes_artifact_when_not_dry_run(store, artifact_dir):
    collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=False)
    artifact = artifact_dir / "LAUC1_evidence.json"
    assert artifact.exists()


def test_collect_artifact_json_valid(store, artifact_dir):
    collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=False)
    data = json.loads((artifact_dir / "LAUC1_evidence.json").read_text())
    assert "schema_version" in data
    assert "aider_readiness_decision" in data
    assert "task_class_metrics" in data
    assert len(data["task_class_metrics"]) == len(SUPPORTED_TASK_CLASSES)


def test_collect_dry_run_does_not_write_artifact(store, artifact_dir):
    collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    assert not (artifact_dir / "LAUC1_evidence.json").exists()


def test_result_to_dict_contains_required_keys(store, artifact_dir):
    result = collect_autonomy_evidence(memory_store=store, artifact_dir=artifact_dir, dry_run=True)
    d = result.to_dict()
    for key in ("schema_version", "campaign_id", "overall_failure_rate", "aider_readiness_decision"):
        assert key in d, f"Missing key: {key}"


def test_bin_script_syntax_ok():
    src = Path("bin/lauc1_evidence_run.py").read_text(encoding="utf-8")
    ast.parse(src)


def test_campaign_id_in_result(store, artifact_dir):
    result = collect_autonomy_evidence(
        campaign_id="TEST-CAMPAIGN",
        memory_store=store,
        artifact_dir=artifact_dir,
        dry_run=True,
    )
    assert result.campaign_id == "TEST-CAMPAIGN"
