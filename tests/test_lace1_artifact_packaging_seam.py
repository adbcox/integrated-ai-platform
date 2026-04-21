"""Seam tests for LACE1-P5-ARTIFACT-PACKAGING-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.artifact_packaging_gate import ArtifactPackagingGate, BundledArtifact


def test_import_gate():
    from framework.artifact_packaging_gate import ArtifactPackagingGate
    assert callable(ArtifactPackagingGate)


def test_pack_returns_bundled_artifact():
    gate = ArtifactPackagingGate()
    b = gate.pack(task_id="t1", prose_summary="test", source_paths=["a.py"])
    assert isinstance(b, BundledArtifact)


def test_bundle_id_prefix():
    b = ArtifactPackagingGate().pack(task_id="mytask", prose_summary="x", source_paths=[])
    assert b.bundle_id.startswith("BUNDLE-mytask-")


def test_diff_summary_default():
    b = ArtifactPackagingGate().pack(task_id="t1", prose_summary="x", source_paths=[])
    assert b.diff_summary == "(no diff)"


def test_source_paths_preserved():
    paths = ["framework/a.py", "tests/b.py"]
    b = ArtifactPackagingGate().pack(task_id="t1", prose_summary="x", source_paths=paths)
    assert b.source_paths == paths


def test_emit_writes_json(tmp_path):
    gate = ArtifactPackagingGate()
    b = gate.pack(task_id="t1", prose_summary="summary text", source_paths=["f.py"])
    path = gate.emit(b, artifact_dir=tmp_path)
    assert Path(path).exists()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["bundle_id"].startswith("BUNDLE-")
    assert data["source_paths"] == ["f.py"]
