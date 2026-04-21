#!/usr/bin/env python3

import os
from datetime import datetime, timezone

from framework.local_run_baseline_receipt import LocalRunBaselineReceipt, LocalRunBaselineReceiptWriter

OUTPUT = "artifacts/local_runs/local_run_baseline_receipt.json"

def main():
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
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    writer.write(receipt, OUTPUT)

    print(f"Receipt written to {OUTPUT}")

if __name__ == "__main__":
    main()
