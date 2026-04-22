"""Seam tests for integrated 5-item roadmap validator."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "bin" / "run_rm_integrated_5_item_check.py"
ARTIFACT = REPO_ROOT / "artifacts" / "governance" / "rm_integrated_5_item_validation.json"


def test_script_importable():
    import importlib.util

    spec = importlib.util.spec_from_file_location("rm_integrated_5_item_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert hasattr(module, "main")


def test_validator_runs_and_emits_artifact():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"validator failed: {result.stderr}\n{result.stdout}"
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert payload["package_id"] == "RM-INTEGRATED-5-ITEM-ADVANCEMENT"
    assert payload["overall_result"] == "pass"
    assert payload["gate_results"]["rm_intel_002_gate"] is True
    assert payload["gate_results"]["rm_intel_001_gate"] is True
    assert payload["gate_results"]["rm_dev_005_gate"] is True
    assert payload["gate_results"]["rm_dev_003_gate"] is True
    assert payload["gate_results"]["rm_dev_002_gate"] is True
    assert payload["gate_results"]["operational_flow_gate"] is True
    assert payload["gate_results"]["integration_gate"] is True
