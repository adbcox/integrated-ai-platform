"""Seam tests for operational runners in integrated 5-item roadmap flow."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
REFRESH = REPO_ROOT / "bin" / "run_rm_intel_refresh_delta.py"
PROJECTION = REPO_ROOT / "bin" / "run_oss_watchtower_projection.py"
BOUNDED = REPO_ROOT / "bin" / "run_bounded_autonomous_codegen.py"
QC = REPO_ROOT / "bin" / "run_rm_dev_002_qc.py"

REFRESH_ART = REPO_ROOT / "artifacts" / "governance" / "oss_refresh_delta.json"
PROJ_ART = REPO_ROOT / "artifacts" / "governance" / "oss_watchtower_projection.json"
RUN_ART = REPO_ROOT / "artifacts" / "bounded_autonomy" / "runs" / "latest_run.json"
QC_ART = REPO_ROOT / "artifacts" / "qc" / "latest_qc_result.json"


def _run(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(path)], cwd=REPO_ROOT, capture_output=True, text=True)


def test_refresh_and_projection_emit_artifacts():
    result_refresh = _run(REFRESH)
    assert result_refresh.returncode == 0, result_refresh.stderr + result_refresh.stdout
    result_projection = _run(PROJECTION)
    assert result_projection.returncode == 0, result_projection.stderr + result_projection.stdout

    refresh_payload = json.loads(REFRESH_ART.read_text(encoding="utf-8"))
    projection_payload = json.loads(PROJ_ART.read_text(encoding="utf-8"))
    assert refresh_payload["artifact_type"] == "oss_refresh_delta"
    assert projection_payload["artifact_type"] == "oss_watchtower_projection"
    assert projection_payload["integrated_chain"]["rm_intel_002_to_rm_intel_001"] is True


def test_bounded_and_qc_emit_artifacts():
    bounded_result = _run(BOUNDED)
    assert bounded_result.returncode == 0, bounded_result.stderr + bounded_result.stdout
    qc_result = _run(QC)
    assert qc_result.returncode == 0, qc_result.stderr + qc_result.stdout

    run_payload = json.loads(RUN_ART.read_text(encoding="utf-8"))
    qc_payload = json.loads(QC_ART.read_text(encoding="utf-8"))
    assert (run_payload.get("decision") or {}).get("disposition") == "success"
    assert "findings" in qc_payload and isinstance(qc_payload["findings"], list)
    assert qc_payload["integration_refs"]["bounded_run_artifact"]
