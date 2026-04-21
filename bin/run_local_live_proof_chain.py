#!/usr/bin/env python3

import os
from datetime import datetime, timezone
from dataclasses import asdict
import json  # Added this import

from framework.local_live_proof_chain import LocalLiveProofChainBuilder

BASELINE_INPUT = "artifacts/local_runs/local_run_baseline_receipt.json"
SUMMARY_INPUT = "artifacts/local_runs/local_run_receipt_summary.json"
INDEX_INPUT = "artifacts/local_runs/local_run_report_index.json"
BUNDLE_INPUT = "artifacts/local_runs/local_evidence_bundle.json"
OUTPUT = "artifacts/local_runs/local_live_proof_chain.json"

def main():
    baseline_path = Path(BASELINE_INPUT)
    summary_path = Path(SUMMARY_INPUT)
    index_path = Path(INDEX_INPUT)
    bundle_path = Path(BUNDLE_INPUT)

    try:
        chain = LocalLiveProofChainBuilder.from_files(baseline_path, summary_path, index_path, bundle_path)
    except FileNotFoundError as e:
        print(e)
        return

    with open(OUTPUT, 'w') as f:
        json.dump(asdict(chain), f, indent=2)

    print(f"Local live proof chain written to {OUTPUT}")

if __name__ == "__main__":
    main()
