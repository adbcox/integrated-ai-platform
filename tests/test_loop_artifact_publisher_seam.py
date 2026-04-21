"""Tests for framework.loop_artifact_publisher — LoopArtifactPublisher seam."""
import json
import pytest
from pathlib import Path

from framework.mvp_coding_loop import MVPLoopResult
from framework.loop_artifact_publisher import LoopArtifactRecord, LoopArtifactPublisher


def _make_loop_result(success=True, task_kind="text_replacement", error=None):
    return MVPLoopResult(
        task_kind=task_kind,
        success=success,
        inspect_ok=True,
        patch_applied=success,
        test_passed=success,
        reverted=not success,
        artifact_path="",
        validation_artifact_path="",
        error=error,
    )


def test_import_ok():
    from framework.loop_artifact_publisher import LoopArtifactRecord, LoopArtifactPublisher  # noqa: F401


def test_record_fields():
    r = LoopArtifactRecord(
        artifact_id="abc", task_kind="text_replacement", target_path="",
        success=True, summary="ok", published_at="2026-01-01T00:00:00+00:00", artifact_path=""
    )
    assert r.artifact_id == "abc"
    assert r.task_kind == "text_replacement"
    assert r.success is True


def test_to_dict_keys():
    r = LoopArtifactRecord(
        artifact_id="abc", task_kind="tk", target_path="",
        success=True, summary="s", published_at="T", artifact_path=""
    )
    d = r.to_dict()
    for k in ("artifact_id", "task_kind", "target_path", "success", "summary", "published_at", "artifact_path"):
        assert k in d


def test_dry_run_returns_record():
    pub = LoopArtifactPublisher()
    result = _make_loop_result()
    record = pub.publish(result, dry_run=True)
    assert isinstance(record, LoopArtifactRecord)


def test_dry_run_empty_artifact_path():
    pub = LoopArtifactPublisher()
    result = _make_loop_result()
    record = pub.publish(result, dry_run=True)
    assert record.artifact_path == ""


def test_dry_run_no_dir_created(tmp_path):
    artifact_dir = tmp_path / "pub_out"
    pub = LoopArtifactPublisher()
    result = _make_loop_result()
    pub.publish(result, artifact_dir=artifact_dir, dry_run=True)
    assert not artifact_dir.exists()


def test_success_propagated():
    pub = LoopArtifactPublisher()
    result = _make_loop_result(success=False)
    record = pub.publish(result, dry_run=True)
    assert record.success is False


def test_task_kind_propagated():
    pub = LoopArtifactPublisher()
    result = _make_loop_result(task_kind="guard_clause")
    record = pub.publish(result, dry_run=True)
    assert record.task_kind == "guard_clause"


def test_artifact_id_is_string():
    pub = LoopArtifactPublisher()
    result = _make_loop_result()
    record = pub.publish(result, dry_run=True)
    assert isinstance(record.artifact_id, str)
    assert len(record.artifact_id) > 0


def test_artifact_id_unique():
    pub = LoopArtifactPublisher()
    result = _make_loop_result()
    r1 = pub.publish(result, dry_run=True)
    r2 = pub.publish(result, dry_run=True)
    assert r1.artifact_id != r2.artifact_id


def test_published_at_is_iso():
    pub = LoopArtifactPublisher()
    result = _make_loop_result()
    record = pub.publish(result, dry_run=True)
    assert "T" in record.published_at


def test_actual_publish_writes_file(tmp_path):
    artifact_dir = tmp_path / "pub_out"
    pub = LoopArtifactPublisher()
    result = _make_loop_result()
    record = pub.publish(result, artifact_dir=artifact_dir, dry_run=False)
    assert record.artifact_path != ""
    assert Path(record.artifact_path).exists()


def test_actual_publish_json_valid(tmp_path):
    artifact_dir = tmp_path / "pub_out"
    pub = LoopArtifactPublisher()
    result = _make_loop_result()
    record = pub.publish(result, artifact_dir=artifact_dir, dry_run=False)
    data = json.loads(Path(record.artifact_path).read_text())
    assert "schema_version" in data
    assert "artifact_id" in data


def test_init_ok_from_framework():
    from framework import LoopArtifactPublisher  # noqa: F401
