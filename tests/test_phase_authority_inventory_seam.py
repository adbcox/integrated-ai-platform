"""Seam tests for P0-01-AUTHORITY-SURFACE-INVENTORY-1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

import run_phase_authority_inventory as inv


def test_import_module():
    assert callable(inv.build_inventory)


def test_build_inventory_returns_dict():
    result = inv.build_inventory()
    assert isinstance(result, dict)


def test_required_keys_present():
    result = inv.build_inventory()
    required = {
        "inventory_id",
        "generated_at",
        "canonical_phase_source",
        "authority_surfaces",
        "conflicts",
        "recommended_authority_order",
        "phase0_gate_status",
    }
    for key in required:
        assert key in result, f"missing key: {key}"


def test_at_least_three_authority_surfaces():
    result = inv.build_inventory()
    assert len(result["authority_surfaces"]) >= 3


def test_conflicts_is_list():
    result = inv.build_inventory()
    assert isinstance(result["conflicts"], list)


def test_recommended_authority_order_is_ranked():
    result = inv.build_inventory()
    order = result["recommended_authority_order"]
    assert len(order) >= 1
    ranks = [item["rank"] for item in order]
    assert ranks == sorted(ranks)


def test_phase0_gate_status_has_gate_classification():
    result = inv.build_inventory()
    status = result["phase0_gate_status"]
    assert "gate_classification" in status
    assert "assessment" in status


def test_emit_artifact(tmp_path):
    inventory = inv.build_inventory()
    inv.ARTIFACT_DIR  # read-only reference; emit to tmp_path instead
    out_path = tmp_path / "phase_authority_inventory.json"
    out_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    loaded = json.loads(out_path.read_text())
    assert loaded["inventory_id"] == "P0-01-AUTHORITY-SURFACE-INVENTORY-1"
    assert len(loaded["authority_surfaces"]) >= 3
    assert isinstance(loaded["conflicts"], list)
    assert "phase0_gate_status" in loaded


def test_runner_script_executes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_phase_authority_inventory.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    artifact = REPO_ROOT / "artifacts" / "governance" / "phase_authority_inventory.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text())
    assert data["inventory_id"] == "P0-01-AUTHORITY-SURFACE-INVENTORY-1"
