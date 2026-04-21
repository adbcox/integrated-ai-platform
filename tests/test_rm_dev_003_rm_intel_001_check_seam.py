"""Seam tests for RM-DEV-003 + RM-INTEL-001 integrated baseline validator."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "bin" / "run_rm_dev_003_rm_intel_001_check.py"
ARTIFACT = REPO_ROOT / "artifacts" / "governance" / "rm_dev_003_rm_intel_001_baseline_validation.json"


def test_script_is_importable():
    import importlib.util

    spec = importlib.util.spec_from_file_location("rm_dev003_intel001_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    assert hasattr(mod, "main")


def test_validator_runs_and_emits_artifact():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"validator failed: {result.stderr}\n{result.stdout}"
    assert ARTIFACT.exists()
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert payload["package_id"] == "RM-DEV-003-RM-INTEL-001-INTEGRATED-BASELINE"
    assert payload["overall_result"] == "pass"
    assert "rm_dev_003_run_artifact" in payload["checks"]
    assert payload["gate_results"]["rm_dev_003_gate"] is True
    assert payload["gate_results"]["rm_intel_001_gate"] is True
    assert payload["gate_results"]["integrated_linkage_gate"] is True
    assert payload["gate_results"]["validation_gate"] is True
