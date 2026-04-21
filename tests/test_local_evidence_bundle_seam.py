import json
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict

from framework.local_evidence_bundle import LocalEvidenceBundleBuilder

def test_local_evidence_bundle_builder(tmp_path):
    baseline_data = {
        "package_id": "P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1",
        "executor": "aider_ollama",
        "route": "local_first",
        "validations_run": ["validation1", "validation2"],
        "validation_passed": True,
        "changed_files": ["file1.py", "file2.py"],
        "artifact_paths": ["artifact1.json", "artifact2.json"],
        "result": "success",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    summary_data = {
        "package_id": "P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1",
        "executor": "aider_ollama",
        "route": "local_first",
        "validation_count": 2,
        "artifact_count": 2,
        "result": "success",
        "summary_generated_at": datetime.now(timezone.utc).isoformat(),
    }

    index_data = {
        "package_id": "P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1",
        "executor": "aider_ollama",
        "route": "local_first",
        "baseline_receipt_path": "artifacts/local_runs/local_run_baseline_receipt.json",
        "summary_path": "artifacts/local_runs/local_run_receipt_summary.json",
        "validation_count": 2,
        "artifact_count": 2,
        "final_result": "success",
        "index_generated_at": datetime.now(timezone.utc).isoformat(),
    }

    baseline_path = tmp_path / 'local_run_baseline_receipt.json'
    with open(baseline_path, 'w') as f:
        json.dump(baseline_data, f)

    summary_path = tmp_path / 'local_run_receipt_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f)

    index_path = tmp_path / 'local_run_report_index.json'
    with open(index_path, 'w') as f:
        json.dump(index_data, f)

    bundle = LocalEvidenceBundleBuilder.from_files(str(baseline_path), str(summary_path), str(index_path))

    assert bundle.package_id == "P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1"
    assert bundle.executor == "aider_ollama"
    assert bundle.route == "local_first"
    assert bundle.baseline_receipt_path == str(baseline_path)
    assert bundle.summary_path == str(summary_path)
    assert bundle.report_index_path == str(index_path)
    assert bundle.validation_count == 2
    assert bundle.artifact_count == 2
    assert bundle.final_result == "success"

    bundle_path = tmp_path / 'local_evidence_bundle.json'
    with open(bundle_path, 'w') as f:
        json.dump(asdict(bundle), f)

    assert bundle_path.exists()
    with open(bundle_path, 'r') as f:
        data = json.load(f)
        assert data == {
            "package_id": "P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1",
            "executor": "aider_ollama",
            "route": "local_first",
            "baseline_receipt_path": str(baseline_path),
            "summary_path": str(summary_path),
            "report_index_path": str(index_path),
            "validation_count": 2,
            "artifact_count": 2,
            "final_result": "success",
            "bundle_generated_at": bundle.bundle_generated_at,
        }
