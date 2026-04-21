#!/usr/bin/env python3

import os
from datetime import datetime, timezone
from dataclasses import asdict
import json  # Added this import

from framework.local_evidence_bundle import LocalEvidenceBundleBuilder

BASELINE_INPUT = "artifacts/local_runs/local_run_baseline_receipt.json"
SUMMARY_INPUT = "artifacts/local_runs/local_run_receipt_summary.json"
INDEX_INPUT = "artifacts/local_runs/local_run_report_index.json"
OUTPUT = "artifacts/local_runs/local_evidence_bundle.json"

def main():
    bundle = LocalEvidenceBundleBuilder.from_files(BASELINE_INPUT, SUMMARY_INPUT, INDEX_INPUT)
    with open(OUTPUT, 'w') as f:
        json.dump(asdict(bundle), f, indent=2)

    print(f"Evidence bundle written to {OUTPUT}")

if __name__ == "__main__":
    main()
