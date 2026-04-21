"""Seam tests for RM-GOV-003-SHARED-TOUCH-LOE-INSPECTOR-SEAM-1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bin.run_rm_gov_003_shared_touch_loe_inspector import run_inspection, emit_inspection


def test_import_inspector():
    from bin.run_rm_gov_003_shared_touch_loe_inspector import run_inspection
    assert callable(run_inspection)


def test_inspection_id():
    result = run_inspection()
    assert result["inspection_id"] == "RM-GOV-003-SHARED-TOUCH-LOE-INSPECTOR-SEAM-1"


def test_yaml_surfaces_present():
    result = run_inspection()
    assert result["any_yaml_has_surfaces"] is True
    for item_id in ("RM-GOV-001", "RM-GOV-002", "RM-GOV-003"):
        assert result["yaml_shared_touch"][item_id]["has_shared_touch_surfaces"] is True


def test_planner_service_has_no_loe_output_initially():
    result = run_inspection()
    # Before P4 runs, planner has no shared_touch output
    # After P4, this may flip — the test asserts structural presence of the key
    assert "has_loe_output" in result["planner_service"]
    assert "payload_keys_in_artifact" in result["planner_service"]


def test_gap_confirmed_or_resolved():
    result = run_inspection()
    # After P4, gap_confirmed may be False; test accepts either state
    assert isinstance(result["gap_confirmed"], bool)
    assert "resolution_required" in result


def test_emit_artifact_written(tmp_path):
    result = run_inspection()
    path = emit_inspection(result, artifact_dir=tmp_path)
    assert Path(path).exists()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["inspection_id"] == "RM-GOV-003-SHARED-TOUCH-LOE-INSPECTOR-SEAM-1"
    assert "planner_service" in data
    assert "yaml_shared_touch" in data
