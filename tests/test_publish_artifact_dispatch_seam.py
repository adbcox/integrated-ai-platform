"""Conformance tests for framework/publish_artifact_dispatch.py (ADSC1-PUBLISH-ARTIFACT-DISPATCH-SEAM-1)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.publish_artifact_dispatch import dispatch_publish_artifact
from framework.tool_schema import PublishArtifactAction, PublishArtifactObservation
from framework.workspace_scope import ToolPathScope


def _scope(root, *writable):
    return ToolPathScope(source_root=root, writable_roots=tuple(writable))


# --- import and type ---

def test_import_dispatch_publish_artifact():
    assert callable(dispatch_publish_artifact)


def test_returns_observation_type(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst = tmp_path / "dst"
    dst.mkdir()
    (src / "artifact.json").write_text("{}")
    scope = _scope(src, dst)
    result = dispatch_publish_artifact(
        PublishArtifactAction(artifact_path=str(src / "artifact.json"), destination=str(dst / "out.json")),
        scope,
    )
    assert isinstance(result, PublishArtifactObservation)


# --- successful copy ---

def test_valid_copy_published_true(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    f = src / "file.txt"
    f.write_text("hello")
    scope = _scope(src, dst_dir)
    result = dispatch_publish_artifact(
        PublishArtifactAction(artifact_path=str(f), destination=str(dst_dir / "out.txt")),
        scope,
    )
    assert result.published is True
    assert result.error is None


def test_destination_file_exists_after_copy(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    f = src / "data.json"
    f.write_text('{"x":1}')
    scope = _scope(src, dst_dir)
    dest = dst_dir / "data_out.json"
    dispatch_publish_artifact(
        PublishArtifactAction(artifact_path=str(f), destination=str(dest)),
        scope,
    )
    assert dest.exists()
    assert dest.read_text() == '{"x":1}'


def test_destination_parent_auto_created(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst_base = tmp_path / "dst"
    dst_base.mkdir()
    f = src / "x.txt"
    f.write_text("x")
    scope = _scope(src, dst_base)
    nested_dest = dst_base / "sub" / "deep" / "out.txt"
    result = dispatch_publish_artifact(
        PublishArtifactAction(artifact_path=str(f), destination=str(nested_dest)),
        scope,
    )
    assert result.published is True
    assert nested_dest.exists()


# --- observation fields echo ---

def test_fields_echo_in_observation(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    f = src / "f.txt"
    f.write_text("y")
    scope = _scope(src, dst_dir)
    dest_path = str(dst_dir / "f_out.txt")
    result = dispatch_publish_artifact(
        PublishArtifactAction(artifact_path=str(f), destination=dest_path),
        scope,
    )
    assert result.artifact_path == str(f)
    assert result.destination == dest_path


# --- error cases ---

def test_source_missing_error_in_observation(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    scope = _scope(src, dst_dir)
    result = dispatch_publish_artifact(
        PublishArtifactAction(artifact_path=str(src / "missing.txt"), destination=str(dst_dir / "out.txt")),
        scope,
    )
    assert result.published is False
    assert result.error is not None


def test_destination_outside_writable_scope_error(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    f = src / "f.txt"
    f.write_text("z")
    # scope only marks src as source_root, no writable roots → dst outside writable
    scope = ToolPathScope(source_root=src)
    result = dispatch_publish_artifact(
        PublishArtifactAction(artifact_path=str(f), destination=str(dst_dir / "out.txt")),
        scope,
    )
    assert result.published is False
    assert result.error is not None


def test_error_not_raised(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    scope = _scope(src, dst_dir)
    # missing source — must not raise, just return published=False
    result = dispatch_publish_artifact(
        PublishArtifactAction(artifact_path=str(src / "gone.txt"), destination=str(dst_dir / "x.txt")),
        scope,
    )
    assert isinstance(result, PublishArtifactObservation)
    assert result.published is False


# --- package surface ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "dispatch_publish_artifact")
    assert callable(framework.dispatch_publish_artifact)
