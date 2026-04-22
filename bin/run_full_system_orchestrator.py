#!/usr/bin/env python3
"""Execute full pipeline orchestration: refresh → projection → bounded run → QC → validation."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _run_stage(stage_name: str, cmd: str, session_id: str) -> dict[str, Any]:
    """Run a pipeline stage and return result."""
    print(f"\n[{stage_name}] Starting...")
    start = time.time()

    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
        elapsed = time.time() - start

        result = {
            "stage": stage_name,
            "session_id": session_id,
            "status": "pass" if proc.returncode == 0 else "fail",
            "exit_code": proc.returncode,
            "elapsed_seconds": elapsed,
            "timestamp": _iso_now(),
        }

        if proc.returncode == 0:
            print(f"[{stage_name}] PASS ({elapsed:.1f}s)")
        else:
            print(f"[{stage_name}] FAIL ({elapsed:.1f}s)")
            print(f"  stdout: {proc.stdout[:200]}")
            print(f"  stderr: {proc.stderr[:200]}")

        return result
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"[{stage_name}] TIMEOUT ({elapsed:.1f}s)")
        return {
            "stage": stage_name,
            "session_id": session_id,
            "status": "timeout",
            "exit_code": -1,
            "elapsed_seconds": elapsed,
            "timestamp": _iso_now(),
        }
    except Exception as e:
        elapsed = time.time() - start
        print(f"[{stage_name}] ERROR: {e}")
        return {
            "stage": stage_name,
            "session_id": session_id,
            "status": "error",
            "exit_code": -1,
            "error": str(e),
            "elapsed_seconds": elapsed,
            "timestamp": _iso_now(),
        }


def _build_pipeline(session_id: str) -> list[tuple[str, str]]:
    """Build the pipeline stages."""
    return [
        ("oss_refresh", "python3 bin/run_rm_intel_refresh_delta.py"),
        ("watchtower_projection", "python3 bin/run_oss_watchtower_projection.py"),
        ("bounded_codegen", "python3 bin/run_bounded_autonomous_codegen.py"),
        ("qc_analysis", "python3 bin/run_rm_dev_002_qc.py"),
        ("integrated_validation", "python3 bin/run_rm_integrated_5_item_check.py"),
    ]


def _load_json(path: Path) -> dict[str, Any] | None:
    """Safely load JSON file."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _collect_artifacts(session_id: str) -> dict[str, Any]:
    """Collect output artifacts from each stage."""
    artifacts = {
        "refresh_delta": _load_json(REPO_ROOT / "artifacts/governance/oss_refresh_delta.json"),
        "watchtower_projection": _load_json(REPO_ROOT / "artifacts/governance/oss_watchtower_projection.json"),
        "bounded_run": _load_json(REPO_ROOT / "artifacts/bounded_autonomy/runs/latest_run.json"),
        "qc_result": _load_json(REPO_ROOT / "artifacts/qc/latest_qc_result.json"),
        "integrated_check": _load_json(REPO_ROOT / "artifacts/governance/integrated_5_item_check.json"),
    }
    return {k: v for k, v in artifacts.items() if v is not None}


def main() -> int:
    parser = argparse.ArgumentParser(description="Full system orchestrator")
    parser.add_argument("--continuous", action="store_true", help="Run in continuous loop")
    parser.add_argument("--interval-seconds", type=int, default=300, help="Interval between runs in continuous mode")
    parser.add_argument("--max-runs", type=int, default=None, help="Max runs in continuous mode")
    parser.add_argument("--session-id", default=None, help="Override session ID")
    args = parser.parse_args()

    run_count = 0

    while True:
        run_count += 1
        session_id = args.session_id or str(uuid.uuid4())[:8]

        print(f"\n{'='*60}")
        print(f"ORCHESTRATOR RUN #{run_count} | session_id={session_id}")
        print(f"{'='*60}")

        start_time = datetime.now(timezone.utc)
        pipeline = _build_pipeline(session_id)
        stage_results = []

        # Run each stage in sequence
        for stage_name, cmd in pipeline:
            result = _run_stage(stage_name, cmd, session_id)
            stage_results.append(result)

            # Stop on first failure (non-continuous mode)
            if result["status"] != "pass" and not args.continuous:
                break

        # Collect artifacts
        artifacts = _collect_artifacts(session_id)

        # Determine gate status
        all_passed = all(r["status"] == "pass" for r in stage_results)
        gate_cleared = all_passed

        # Build summary
        summary = {
            "schema_version": 1,
            "package_id": "FULL-SYSTEM-ORCHESTRATOR",
            "session_id": session_id,
            "run_number": run_count,
            "started_at": start_time.isoformat(),
            "completed_at": _iso_now(),
            "pipeline_stages": stage_results,
            "gate_status": {
                "all_passed": all_passed,
                "gate_cleared": gate_cleared,
                "total_stages": len(stage_results),
                "passed_stages": sum(1 for r in stage_results if r["status"] == "pass"),
            },
            "collected_artifacts": list(artifacts.keys()),
            "promotion_readiness": {
                "system_operational": gate_cleared,
                "ready_for_improvement_loop": gate_cleared,
                "recommend_continuous_mode": gate_cleared,
            },
        }

        # Write summary
        out_dir = REPO_ROOT / "artifacts/system_runs" / session_id
        out_dir.mkdir(parents=True, exist_ok=True)
        summary_path = out_dir / "system_run_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        # Write latest pointer
        latest_dir = REPO_ROOT / "artifacts/system_runs" / "latest"
        latest_dir.mkdir(parents=True, exist_ok=True)
        (latest_dir / "system_run_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )

        print(f"\nSummary: {summary_path}")
        print(f"Gate cleared: {gate_cleared}")

        if not args.continuous:
            return 0 if gate_cleared else 1

        # Continuous mode: check max runs
        if args.max_runs and run_count >= args.max_runs:
            print(f"\nMax runs ({args.max_runs}) reached. Stopping.")
            return 0

        # Sleep before next run
        print(f"\nWaiting {args.interval_seconds}s before next run...")
        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
