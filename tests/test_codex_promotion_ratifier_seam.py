"""Tests for framework.codex_promotion_ratifier — LAPC1 P6."""
import json
import pytest
from pathlib import Path

from framework.codex_availability_gate import evaluate_codex_availability
from framework.codex_promotion_ratifier import (
    CODEX_PROMOTION_DONE,
    CODEX_LONG_TERM_DEFERRED,
    CodexPromotionArtifact,
    ratify_codex_promotion,
)


def _avail():
    return evaluate_codex_availability(dry_run=True)


def test_import_ok():
    from framework.codex_promotion_ratifier import ratify_codex_promotion, CodexPromotionArtifact  # noqa: F401


def test_constants():
    assert CODEX_PROMOTION_DONE == "codex_done"
    assert CODEX_LONG_TERM_DEFERRED == "codex_long_term_deferred"


def test_returns_artifact():
    a = ratify_codex_promotion(dry_run=True)
    assert isinstance(a, CodexPromotionArtifact)


def test_no_inputs_is_deferred():
    a = ratify_codex_promotion(dry_run=True)
    assert a.decision == CODEX_LONG_TERM_DEFERRED


def test_blocked_availability_is_deferred():
    avail = _avail()
    a = ratify_codex_promotion(avail, dry_run=True)
    assert a.decision == CODEX_LONG_TERM_DEFERRED


def test_availability_result_propagated():
    avail = _avail()
    a = ratify_codex_promotion(avail, dry_run=True)
    assert a.availability_result == avail.overall_result


def test_codex_available_propagated():
    avail = _avail()
    a = ratify_codex_promotion(avail, dry_run=True)
    assert a.codex_available == avail.codex_available


def test_defer_reason_non_empty_when_deferred():
    a = ratify_codex_promotion(dry_run=True)
    if a.decision == CODEX_LONG_TERM_DEFERRED:
        assert len(a.defer_reason) > 0


def test_next_review_trigger_non_empty():
    a = ratify_codex_promotion(dry_run=True)
    assert len(a.next_review_trigger) > 0


def test_rationale_non_empty():
    a = ratify_codex_promotion(dry_run=True)
    assert len(a.rationale) > 0


def test_to_dict_schema_version():
    a = ratify_codex_promotion(dry_run=True)
    d = a.to_dict()
    assert d["schema_version"] == 1


def test_to_dict_keys():
    a = ratify_codex_promotion(dry_run=True)
    d = a.to_dict()
    for k in ("schema_version", "decision", "rationale", "availability_result",
              "codex_available", "defer_reason", "next_review_trigger", "ratified_at"):
        assert k in d


def test_json_round_trip():
    a = ratify_codex_promotion(dry_run=True)
    text = json.dumps(a.to_dict())
    back = json.loads(text)
    assert back["schema_version"] == 1
    assert back["decision"] in (CODEX_PROMOTION_DONE, CODEX_LONG_TERM_DEFERRED)


def test_dry_run_no_file(tmp_path):
    a = ratify_codex_promotion(artifact_dir=tmp_path / "out", dry_run=True)
    assert a.artifact_path == ""


def test_non_dry_run_writes_file(tmp_path):
    a = ratify_codex_promotion(artifact_dir=tmp_path / "out", dry_run=False)
    assert a.artifact_path != ""
    assert Path(a.artifact_path).exists()


def test_init_ok_from_framework():
    from framework import ratify_codex_promotion  # noqa: F401
