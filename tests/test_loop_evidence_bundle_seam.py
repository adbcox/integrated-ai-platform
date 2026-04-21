"""Conformance tests for framework/loop_evidence_bundle.py (LARAC2-EVIDENCE-BUNDLE-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.loop_evidence_bundle import LoopEvidenceBundle, build_evidence_bundle, emit_evidence_bundle


# --- import and type ---

def test_import_build_evidence_bundle():
    assert callable(build_evidence_bundle)


def test_returns_loop_evidence_bundle():
    b = build_evidence_bundle("s")
    assert isinstance(b, LoopEvidenceBundle)


# --- fields ---

def test_bundle_fields_present():
    b = build_evidence_bundle("s")
    assert hasattr(b, "session_id")
    assert hasattr(b, "built_at")
    assert hasattr(b, "search_result")
    assert hasattr(b, "discovery_result")
    assert hasattr(b, "diff_package")
    assert hasattr(b, "validation_record")
    assert hasattr(b, "retry_telemetry")
    assert hasattr(b, "publication_record")


# --- empty bundle ---

def test_empty_bundle_all_none():
    b = build_evidence_bundle("s")
    assert b.search_result is None
    assert b.discovery_result is None
    assert b.diff_package is None
    assert b.validation_record is None
    assert b.retry_telemetry is None
    assert b.publication_record is None


def test_empty_bundle_serializes(tmp_path):
    b = build_evidence_bundle("sess-empty")
    path = emit_evidence_bundle(b, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert data["session_id"] == "sess-empty"


# --- populated bundle ---

def test_search_result_populated():
    from framework.search_aware_inspect import SearchAwareInspectResult
    sr = SearchAwareInspectResult(
        path="x.py", content="", inspect_error=None,
        search_query="q", context_snippet="ctx", search_error=None, search_match_count=1
    )
    b = build_evidence_bundle("s", search_result=sr)
    assert b.search_result is not None
    assert b.search_result["context_snippet"] == "ctx"


def test_diff_package_populated():
    from framework.diff_result_packager import DiffResultPackage
    dp = DiffResultPackage(session_id="s", diff="diff text", diff_error=None, ref=None, packaged_at="now")
    b = build_evidence_bundle("s", diff_package=dp)
    assert b.diff_package is not None
    assert b.diff_package["diff"] == "diff text"


def test_retry_telemetry_populated():
    from framework.retry_telemetry import RetryTelemetryRecord
    rt = RetryTelemetryRecord(
        session_id="s", job_id="j", total_steps=3, failed_steps=1,
        retry_eligible_failures=0, outcome="partial", recorded_at="now"
    )
    b = build_evidence_bundle("s", retry_telemetry=rt)
    assert b.retry_telemetry is not None
    assert b.retry_telemetry["total_steps"] == 3


# --- emit artifact ---

def test_artifact_written(tmp_path):
    b = build_evidence_bundle("test-sess")
    path = emit_evidence_bundle(b, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_named_with_session_id(tmp_path):
    b = build_evidence_bundle("my-session")
    path = emit_evidence_bundle(b, artifact_dir=tmp_path)
    assert "my-session" in path


def test_artifact_parseable(tmp_path):
    b = build_evidence_bundle("parse-test")
    path = emit_evidence_bundle(b, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "session_id" in data
    assert "built_at" in data


# --- session_id preserved ---

def test_session_id_preserved():
    b = build_evidence_bundle("xyz-123")
    assert b.session_id == "xyz-123"


# --- built_at timestamp ---

def test_built_at_is_string():
    b = build_evidence_bundle("s")
    assert isinstance(b.built_at, str)
    assert len(b.built_at) > 0


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "LoopEvidenceBundle")
    assert hasattr(framework, "build_evidence_bundle")
    assert hasattr(framework, "emit_evidence_bundle")
