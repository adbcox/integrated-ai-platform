import json
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict

from framework.local_live_proof_chain import LocalLiveProofChainBuilder

def test_local_live_proof_chain_builder_complete(tmp_path):
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
        "live_execution_signal": True
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

    bundle_data = {
        "package_id": "P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1",
        "executor": "aider_ollama",
        "route": "local_first",
        "baseline_receipt_path": "artifacts/local_runs/local_run_baseline_receipt.json",
        "summary_path": "artifacts/local_runs/local_run_receipt_summary.json",
        "report_index_path": "artifacts/local_runs/local_run_report_index.json",
        "validation_count": 2,
        "artifact_count": 2,
        "final_result": "success",
        "bundle_generated_at": datetime.now(timezone.utc).isoformat(),
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

    bundle_path = tmp_path / 'local_evidence_bundle.json'
    with open(bundle_path, 'w') as f:
        json.dump(bundle_data, f)

    chain = LocalLiveProofChainBuilder.from_files(baseline_path, summary_path, index_path, bundle_path)

    assert chain.package_id == "P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1"
    assert chain.executor == "aider_ollama"
    assert chain.route == "local_first"
    assert chain.evidence_inputs_seen == ["baseline_receipt", "summary", "index", "bundle"]
    assert chain.validation_count == 4
    assert chain.artifact_count == 4
    assert chain.final_result == "success"
    assert chain.live_execution_signal == True
    assert chain.live_dispatch_succeeded == True
    assert chain.dispatch_mode == "local_live"

    chain_path = tmp_path / 'local_live_proof_chain.json'
    with open(chain_path, 'w') as f:
        json.dump(asdict(chain), f)

    assert chain_path.exists()
    with open(chain_path, 'r') as f:
        data = json.load(f)
        assert data == {
            "package_id": "P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1",
            "executor": "aider_ollama",
            "route": "local_first",
            "evidence_inputs_seen": ["baseline_receipt", "summary", "index", "bundle"],
            "validation_count": 4,
            "artifact_count": 4,
            "final_result": "success",
            "live_execution_signal": True,
            "proof_generated_at": chain.proof_generated_at,
            "live_dispatch_succeeded": True,
            "dispatch_mode": "local_live"
        }

def test_local_live_proof_chain_builder_partial(tmp_path):
    # Only baseline present — summary, index, bundle absent.
    # Builder returns a partial chain (no FileNotFoundError for optional inputs).
    # live_dispatch_succeeded must be False; dispatch_mode must be "unknown".
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

    baseline_path = tmp_path / 'local_run_baseline_receipt.json'
    with open(baseline_path, 'w') as f:
        json.dump(baseline_data, f)

    summary_path = tmp_path / 'local_run_receipt_summary.json'
    index_path = tmp_path / 'local_run_report_index.json'
    bundle_path = tmp_path / 'local_evidence_bundle.json'

    chain = LocalLiveProofChainBuilder.from_files(baseline_path, summary_path, index_path, bundle_path)

    assert chain.package_id == "P1-LF-01-LOCAL-RUN-BASELINE-RECEIPT-1"
    assert chain.executor == "aider_ollama"
    assert chain.route == "local_first"
    assert chain.evidence_inputs_seen == ["baseline_receipt"]
    assert chain.live_execution_signal is True
    assert chain.live_dispatch_succeeded is False
    assert chain.dispatch_mode == "unknown"


def test_local_live_proof_chain_builder_missing_baseline_raises(tmp_path):
    # Builder raises FileNotFoundError only when the baseline itself is absent.
    baseline_path = tmp_path / 'local_run_baseline_receipt.json'
    summary_path = tmp_path / 'local_run_receipt_summary.json'
    index_path = tmp_path / 'local_run_report_index.json'
    bundle_path = tmp_path / 'local_evidence_bundle.json'

    try:
        LocalLiveProofChainBuilder.from_files(baseline_path, summary_path, index_path, bundle_path)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError as e:
        assert str(baseline_path) in str(e)
