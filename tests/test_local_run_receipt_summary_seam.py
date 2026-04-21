import json
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict

from framework.local_run_receipt_summary import LocalRunReceiptSummaryBuilder

def test_local_run_receipt_summary_builder(tmp_path):
    receipt_data = {
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

    receipt_path = tmp_path / 'local_run_baseline_receipt.json'
    with open(receipt_path, 'w') as f:
        json.dump(receipt_data, f)

    summary = LocalRunReceiptSummaryBuilder.from_file(str(receipt_path))

    assert summary.package_id == "P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1"
    assert summary.executor == "aider_ollama"
    assert summary.route == "local_first"
    assert summary.validation_count == 2
    assert summary.artifact_count == 2
    assert summary.result == "success"

    summary_path = tmp_path / 'local_run_receipt_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(asdict(summary), f)

    assert summary_path.exists()
    with open(summary_path, 'r') as f:
        data = json.load(f)
        assert data == {
            "package_id": "P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1",
            "executor": "aider_ollama",
            "route": "local_first",
            "validation_count": 2,
            "artifact_count": 2,
            "result": "success",
            "summary_generated_at": summary.summary_generated_at,
        }
