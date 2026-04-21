import json
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict  # Added this import

from framework.local_run_report_index import LocalRunReportIndexBuilder

def test_local_run_report_index_builder(tmp_path):
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

    baseline_path = tmp_path / 'local_run_baseline_receipt.json'
    with open(baseline_path, 'w') as f:
        json.dump(baseline_data, f)

    summary_path = tmp_path / 'local_run_receipt_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f)

    index = LocalRunReportIndexBuilder.from_files(str(baseline_path), str(summary_path))

    assert index.package_id == "P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1"
    assert index.executor == "aider_ollama"
    assert index.route == "local_first"
    assert index.baseline_receipt_path == str(baseline_path)
    assert index.summary_path == str(summary_path)
    assert index.validation_count == 2
    assert index.artifact_count == 2
    assert index.final_result == "success"

    index_path = tmp_path / 'local_run_report_index.json'
    with open(index_path, 'w') as f:
        json.dump(asdict(index), f)

    assert index_path.exists()
    with open(index_path, 'r') as f:
        data = json.load(f)
        assert data == {
            "package_id": "P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1",
            "executor": "aider_ollama",
            "route": "local_first",
            "baseline_receipt_path": str(baseline_path),
            "summary_path": str(summary_path),
            "validation_count": 2,
            "artifact_count": 2,
            "final_result": "success",
            "index_generated_at": index.index_generated_at,
        }
