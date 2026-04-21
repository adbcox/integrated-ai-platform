"""Conformance tests for framework/bounded_result_publisher.py (LARAC2-PUBLISH-RESULT-SEAM-1)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.bounded_result_publisher import BoundedResultPublisher, PublicationRecord


# --- import and type ---

def test_import_bounded_result_publisher():
    assert callable(BoundedResultPublisher)


def test_returns_publication_record(tmp_path):
    src = tmp_path / "result.json"
    src.write_text('{"ok": true}')
    pub = BoundedResultPublisher(artifact_dir=tmp_path / "pub")
    r = pub.publish("sess-1", str(src))
    assert isinstance(r, PublicationRecord)


# --- fields ---

def test_result_fields_present(tmp_path):
    src = tmp_path / "a.json"
    src.write_text("{}")
    r = BoundedResultPublisher(artifact_dir=tmp_path / "out").publish("s", str(src))
    assert hasattr(r, "session_id")
    assert hasattr(r, "artifact_path")
    assert hasattr(r, "destination")
    assert hasattr(r, "published")
    assert hasattr(r, "publication_error")
    assert hasattr(r, "published_at")


# --- session_id preserved ---

def test_session_id_preserved(tmp_path):
    src = tmp_path / "f.txt"
    src.write_text("x")
    r = BoundedResultPublisher(artifact_dir=tmp_path / "out").publish("my-session", str(src))
    assert r.session_id == "my-session"


# --- successful publish ---

def test_published_true_on_success(tmp_path):
    src = tmp_path / "result.json"
    src.write_text("{}")
    r = BoundedResultPublisher(artifact_dir=tmp_path / "out").publish("s", str(src))
    assert r.published is True
    assert r.publication_error is None


def test_destination_under_artifact_dir(tmp_path):
    src = tmp_path / "result.json"
    src.write_text("{}")
    pub = BoundedResultPublisher(artifact_dir=tmp_path / "out")
    r = pub.publish("my-session", str(src))
    assert "my-session" in r.destination
    assert "result.json" in r.destination


# --- failure non-raising ---

def test_failure_non_raising_missing_source(tmp_path):
    r = BoundedResultPublisher(artifact_dir=tmp_path / "out").publish("s", "/nonexistent/file.txt")
    assert isinstance(r, PublicationRecord)
    assert r.published is False


def test_error_captured_on_failure(tmp_path):
    r = BoundedResultPublisher(artifact_dir=tmp_path / "out").publish("s", "/nonexistent/x.json")
    assert r.publication_error is not None


# --- published_at timestamp ---

def test_published_at_is_string(tmp_path):
    src = tmp_path / "f.json"
    src.write_text("{}")
    r = BoundedResultPublisher(artifact_dir=tmp_path / "out").publish("s", str(src))
    assert isinstance(r.published_at, str)
    assert len(r.published_at) > 0


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "BoundedResultPublisher")
    assert hasattr(framework, "PublicationRecord")
