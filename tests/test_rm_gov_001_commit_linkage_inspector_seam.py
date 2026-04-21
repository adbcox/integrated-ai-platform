"""Seam tests for RM-GOV-001-COMMIT-LINKAGE-INSPECTOR-SEAM-1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bin.run_rm_gov_001_commit_linkage_inspector import run_inspection, emit_inspection


def test_import_inspector():
    from bin.run_rm_gov_001_commit_linkage_inspector import run_inspection
    assert callable(run_inspection)


def test_inspection_covers_three_items():
    result = run_inspection()
    assert len(result["items"]) == 3
    assert "RM-GOV-001" in result["items"]
    assert "RM-GOV-002" in result["items"]
    assert "RM-GOV-003" in result["items"]


def test_all_items_need_population():
    result = run_inspection()
    for item_id, item in result["items"].items():
        assert item["needs_population"] is True, f"{item_id} already has last_execution_commit set"


def test_all_have_recommendations():
    result = run_inspection()
    assert result["all_have_recommendations"] is True
    for item_id, item in result["items"].items():
        assert item["recommended_sha"] is not None, f"{item_id} has no recommended_sha"
        assert len(item["recommended_sha"]) >= 7, f"{item_id} sha too short"


def test_file_history_probes_non_empty():
    result = run_inspection()
    for item_id, item in result["items"].items():
        probes = item["file_history_probes"]
        has_any = any(len(v) > 0 for v in probes.values())
        assert has_any, f"{item_id} has no file history in any probe"


def test_emit_artifact_written(tmp_path):
    result = run_inspection()
    path = emit_inspection(result, artifact_dir=tmp_path)
    assert Path(path).exists()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["inspection_id"] == "RM-GOV-001-COMMIT-LINKAGE-INSPECTOR-SEAM-1"
    assert len(data["items"]) == 3
    assert "items_needing_population" in data
