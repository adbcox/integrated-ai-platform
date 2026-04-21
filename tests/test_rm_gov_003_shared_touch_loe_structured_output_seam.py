"""Seam tests for RM-GOV-003-SHARED-TOUCH-LOE-STRUCTURED-OUTPUT-SEAM-1."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def test_planner_service_has_shared_touch_keyword():
    planner = REPO_ROOT / "roadmap_governance" / "planner_service.py"
    text = planner.read_text(encoding="utf-8")
    assert "shared_touch" in text


def test_planner_service_has_shared_touch_surfaces_in_payload():
    planner = REPO_ROOT / "roadmap_governance" / "planner_service.py"
    text = planner.read_text(encoding="utf-8")
    assert '"shared_touch_surfaces"' in text


def test_planner_service_has_shared_touch_count_in_payload():
    planner = REPO_ROOT / "roadmap_governance" / "planner_service.py"
    text = planner.read_text(encoding="utf-8")
    assert '"shared_touch_count"' in text


def test_collect_shared_touch_surfaces_importable():
    from roadmap_governance.planner_service import _collect_shared_touch_surfaces
    assert callable(_collect_shared_touch_surfaces)


def test_collect_returns_surfaces_for_rm_gov_items():
    from roadmap_governance.planner_service import _collect_shared_touch_surfaces
    surfaces = _collect_shared_touch_surfaces(["RM-GOV-001", "RM-GOV-002", "RM-GOV-003"])
    assert len(surfaces) > 0, "Expected non-empty surfaces list from RM-GOV YAML items"
    assert isinstance(surfaces, list)
    assert all(isinstance(s, str) for s in surfaces)


def test_shared_touch_loe_subclaim_flipped():
    import importlib.util
    verifier_path = REPO_ROOT / "bin" / "run_rm_gov_003_verifier.py"
    spec = importlib.util.spec_from_file_location("run_rm_gov_003_verifier", verifier_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    result = mod.run()
    loe = result["subclaims"]["shared_touch_loe_optimization"]
    assert loe["evidenced"] is True, (
        f"shared_touch_loe_optimization still false: {loe.get('evidence_detail')}"
    )
