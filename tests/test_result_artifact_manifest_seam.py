"""Conformance tests for framework/result_artifact_manifest.py (LARAC2-RESULT-MANIFEST-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.result_artifact_manifest import ResultArtifactManifest, build_manifest, emit_manifest


# --- import and type ---

def test_import_build_manifest():
    assert callable(build_manifest)


def test_returns_result_artifact_manifest():
    m = build_manifest("sess-1")
    assert isinstance(m, ResultArtifactManifest)


# --- fields ---

def test_manifest_fields_present():
    m = build_manifest("s")
    assert hasattr(m, "session_id")
    assert hasattr(m, "bundle_paths")
    assert hasattr(m, "bundle_count")
    assert hasattr(m, "existing_count")
    assert hasattr(m, "success_count")
    assert hasattr(m, "built_at")


# --- empty manifest ---

def test_empty_manifest():
    m = build_manifest("empty")
    assert m.bundle_count == 0
    assert m.existing_count == 0
    assert m.success_count == 0
    assert m.bundle_paths == []


# --- counts ---

def test_bundle_count_matches_paths():
    m = build_manifest("s", bundle_paths=["/a", "/b", "/c"])
    assert m.bundle_count == 3


def test_existing_count_nonexistent_paths():
    m = build_manifest("s", bundle_paths=["/nonexistent/a.json", "/nonexistent/b.json"])
    assert m.existing_count == 0


def test_existing_count_real_paths(tmp_path):
    f1 = tmp_path / "b1.json"
    f2 = tmp_path / "b2.json"
    f1.write_text("{}")
    f2.write_text("{}")
    m = build_manifest("s", bundle_paths=[str(f1), str(f2), "/nonexistent.json"])
    assert m.existing_count == 2


# --- session_id preserved ---

def test_session_id_preserved():
    m = build_manifest("my-session")
    assert m.session_id == "my-session"


# --- artifact emission ---

def test_artifact_written(tmp_path):
    m = build_manifest("test")
    path = emit_manifest(m, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_parseable(tmp_path):
    m = build_manifest("parse")
    path = emit_manifest(m, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "session_id" in data
    assert "bundle_count" in data


# --- built_at timestamp ---

def test_built_at_is_string():
    m = build_manifest("s")
    assert isinstance(m.built_at, str)
    assert len(m.built_at) > 0


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "ResultArtifactManifest")
    assert hasattr(framework, "build_manifest")
    assert hasattr(framework, "emit_manifest")
