#!/usr/bin/env python3

import os
from datetime import datetime, timezone
from dataclasses import asdict
import json  # Added this import

from framework.local_run_report_index import LocalRunReportIndexBuilder

BASELINE_INPUT = "artifacts/local_runs/local_run_baseline_receipt.json"
SUMMARY_INPUT = "artifacts/local_runs/local_run_receipt_summary.json"
OUTPUT = "artifacts/local_runs/local_run_report_index.json"

def main():
    index = LocalRunReportIndexBuilder.from_files(BASELINE_INPUT, SUMMARY_INPUT)
    with open(OUTPUT, 'w') as f:
        json.dump(asdict(index), f, indent=2)

    print(f"Report index written to {OUTPUT}")

if __name__ == "__main__":
    main()
