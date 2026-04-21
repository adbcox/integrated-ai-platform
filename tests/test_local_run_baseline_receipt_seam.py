import json
from datetime import datetime, timezone
from pathlib import Path

from framework.local_run_baseline_receipt import LocalRunBaselineReceipt, LocalRunBaselineReceiptWriter

def test_local_run_baseline_receipt_writer(tmp_path):
    receipt = LocalRunBaselineReceipt(
        package_id="P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1",
        executor="aider_ollama",
        route="local_first",
        validations_run=["validation1", "validation2"],
        validation_passed=True,
        changed_files=["file1.py", "file2.py"],
        artifact_paths=["artifact1.json", "artifact2.json"],
        result="success",
        recorded_at=datetime.now(timezone.utc).isoformat(),
    )

    writer = LocalRunBaselineReceiptWriter()
    output_path = tmp_path / 'local_run_baseline_receipt.json'
    writer.write(receipt, str(output_path))

    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
        assert data == {
            "package_id": "P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1",
            "executor": "aider_ollama",
            "route": "local_first",
            "validations_run": ["validation1", "validation2"],
            "validation_passed": True,
            "changed_files": ["file1.py", "file2.py"],
            "artifact_paths": ["artifact1.json", "artifact2.json"],
            "result": "success",
            "recorded_at": receipt.recorded_at,
        }
