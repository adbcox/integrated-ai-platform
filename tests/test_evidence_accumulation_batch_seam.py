"""Tests for framework.evidence_accumulation_batch — EvidenceAccumulationBatch seam."""
import json
import pytest
from pathlib import Path

from framework.mvp_coding_loop import SAFE_TASK_KINDS
from framework.evidence_accumulation_batch import (
    BatchRunConfig,
    BatchKindResult,
    BatchRunResult,
    EvidenceAccumulationBatch,
)


def test_import_ok():
    from framework.evidence_accumulation_batch import EvidenceAccumulationBatch, BatchRunResult  # noqa: F401


def test_batch_run_config_fields():
    cfg = BatchRunConfig(runs_per_kind=2, dry_run=True)
    assert cfg.runs_per_kind == 2
    assert cfg.dry_run is True


def test_batch_kind_result_fields():
    kr = BatchKindResult(task_kind="text_replacement", total_runs=3, success_count=2, failure_count=1)
    assert kr.task_kind == "text_replacement"
    assert kr.total_runs == 3


def test_batch_run_returns_result():
    batch = EvidenceAccumulationBatch()
    config = BatchRunConfig(runs_per_kind=1, dry_run=True)
    result = batch.run(config)
    assert isinstance(result, BatchRunResult)


def test_batch_covers_all_safe_kinds():
    batch = EvidenceAccumulationBatch()
    config = BatchRunConfig(runs_per_kind=1, dry_run=True)
    result = batch.run(config)
    returned_kinds = {kr.task_kind for kr in result.kind_results}
    assert SAFE_TASK_KINDS.issubset(returned_kinds)


def test_batch_total_kinds_matches():
    batch = EvidenceAccumulationBatch()
    config = BatchRunConfig(runs_per_kind=1, dry_run=True)
    result = batch.run(config)
    assert result.total_kinds == len(result.kind_results)


def test_batch_total_runs_correct():
    batch = EvidenceAccumulationBatch()
    config = BatchRunConfig(runs_per_kind=2, dry_run=True)
    result = batch.run(config)
    assert result.total_runs == sum(kr.total_runs for kr in result.kind_results)


def test_batch_total_successes():
    batch = EvidenceAccumulationBatch()
    config = BatchRunConfig(runs_per_kind=1, dry_run=True)
    result = batch.run(config)
    assert result.total_successes + result.total_failures == result.total_runs


def test_batch_dry_run_no_file(tmp_path):
    batch = EvidenceAccumulationBatch()
    config = BatchRunConfig(runs_per_kind=1, dry_run=True, artifact_dir=tmp_path / "out")
    result = batch.run(config)
    assert result.artifact_path == ""


def test_batch_non_dry_run_writes_file(tmp_path):
    batch = EvidenceAccumulationBatch()
    config = BatchRunConfig(runs_per_kind=1, dry_run=False, artifact_dir=tmp_path / "out")
    result = batch.run(config)
    assert result.artifact_path != ""
    assert Path(result.artifact_path).exists()


def test_batch_json_valid(tmp_path):
    batch = EvidenceAccumulationBatch()
    config = BatchRunConfig(runs_per_kind=1, dry_run=False, artifact_dir=tmp_path / "out")
    result = batch.run(config)
    data = json.loads(Path(result.artifact_path).read_text())
    assert "schema_version" in data
    assert "kind_results" in data


def test_batch_generated_at_is_iso():
    batch = EvidenceAccumulationBatch()
    config = BatchRunConfig(runs_per_kind=1, dry_run=True)
    result = batch.run(config)
    assert "T" in result.generated_at


def test_summary_line_non_empty():
    batch = EvidenceAccumulationBatch()
    config = BatchRunConfig(runs_per_kind=1, dry_run=True)
    result = batch.run(config)
    assert isinstance(result.summary_line(), str)
    assert len(result.summary_line()) > 0


def test_to_dict_keys():
    batch = EvidenceAccumulationBatch()
    config = BatchRunConfig(runs_per_kind=1, dry_run=True)
    result = batch.run(config)
    d = result.to_dict()
    for k in ("schema_version", "generated_at", "total_kinds", "total_runs", "kind_results"):
        assert k in d


def test_kind_result_to_dict():
    kr = BatchKindResult(task_kind="text_replacement", total_runs=2, success_count=1, failure_count=1)
    d = kr.to_dict()
    assert d["task_kind"] == "text_replacement"
    assert d["total_runs"] == 2


def test_batch_runs_per_kind_respected():
    batch = EvidenceAccumulationBatch()
    config = BatchRunConfig(runs_per_kind=2, dry_run=True)
    result = batch.run(config)
    for kr in result.kind_results:
        if kr.error is None:
            assert kr.total_runs <= 2


def test_init_ok_from_framework():
    from framework import EvidenceAccumulationBatch  # noqa: F401
