#!/usr/bin/env python3

import os
from datetime import datetime, timezone
from dataclasses import asdict
import json  # Added this import

from framework.local_run_receipt_summary import LocalRunReceiptSummaryBuilder

INPUT = "artifacts/local_runs/local_run_baseline_receipt.json"
OUTPUT = "artifacts/local_runs/local_run_receipt_summary.json"

def main():
    summary = LocalRunReceiptSummaryBuilder.from_file(INPUT)
    with open(OUTPUT, 'w') as f:
        json.dump(asdict(summary), f, indent=2)

    print(f"Summary written to {OUTPUT}")

if __name__ == "__main__":
    main()
