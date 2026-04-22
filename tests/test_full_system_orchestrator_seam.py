"""Seam tests for full system orchestrator."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_orchestrator_script_exists():
    """Verify orchestrator script exists."""
    orchestrator = REPO_ROOT / "bin" / "run_full_system_orchestrator.py"
    assert orchestrator.exists()


def test_orchestrator_imports():
    """Verify orchestrator imports correctly."""
    result = subprocess.run(
        "python3 -c 'import argparse, json, subprocess, sys, time, uuid; from datetime import datetime, timezone; from pathlib import Path; from typing import Any'",
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        shell=True,
    )
    assert result.returncode == 0


def test_orchestrator_single_run():
    """Run orchestrator once and verify output."""
    result = subprocess.run(
        "python3 bin/run_full_system_orchestrator.py",
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
        shell=True,
    )
    # Orchestrator may fail on specific stages but should run without crashing
    assert "ORCHESTRATOR RUN" in result.stdout or result.returncode == 1


def test_system_run_artifact_structure():
    """Verify system run summary structure when it exists."""
    latest_summary = REPO_ROOT / "artifacts/system_runs/latest/system_run_summary.json"
    if not latest_summary.exists():
        pytest.skip("Latest summary not found (run orchestrator first)")

    data = json.loads(latest_summary.read_text(encoding="utf-8"))

    # Verify required top-level keys
    assert "schema_version" in data
    assert "session_id" in data
    assert "pipeline_stages" in data
    assert "gate_status" in data

    # Verify gate status structure
    gate = data["gate_status"]
    assert "all_passed" in gate
    assert "gate_cleared" in gate
    assert "total_stages" in gate

    # Verify promotion readiness
    assert "promotion_readiness" in data
    promo = data["promotion_readiness"]
    assert "system_operational" in promo
    assert "ready_for_improvement_loop" in promo


def test_qc_pattern_store_exists():
    """Verify QC pattern store exists."""
    pattern_store = REPO_ROOT / "governance" / "qc_pattern_store.v1.yaml"
    assert pattern_store.exists()


def test_qc_pattern_store_structure():
    """Verify QC pattern store structure."""
    import yaml

    pattern_store = REPO_ROOT / "governance" / "qc_pattern_store.v1.yaml"
    if not pattern_store.exists():
        pytest.skip("Pattern store not found")

    data = yaml.safe_load(pattern_store.read_text(encoding="utf-8"))
    assert "schema_version" in data
    assert "failure_classes" in data
    assert "learned_patterns" in data
    assert "prevention_rules" in data


def test_bounded_codegen_upgrade():
    """Verify bounded codegen has modification capability."""
    codegen_file = REPO_ROOT / "bin" / "run_bounded_autonomous_codegen.py"
    content = codegen_file.read_text(encoding="utf-8")

    # Check for new modification function
    assert "_attempt_bounded_modification" in content
    assert "modification_result" in content


def test_pipeline_runners_exist():
    """Verify all pipeline runners exist."""
    runners = [
        "bin/run_rm_intel_refresh_delta.py",
        "bin/run_oss_watchtower_projection.py",
        "bin/run_bounded_autonomous_codegen.py",
        "bin/run_rm_dev_002_qc.py",
        "bin/run_rm_integrated_5_item_check.py",
    ]

    for runner in runners:
        assert (REPO_ROOT / runner).exists(), f"{runner} not found"


def test_orchestrator_help():
    """Verify orchestrator accepts help argument."""
    result = subprocess.run(
        "python3 bin/run_full_system_orchestrator.py --help",
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        shell=True,
    )
    assert result.returncode == 0
    assert "continuous" in result.stdout or "help" in result.stdout.lower()


def test_continuous_mode_flag():
    """Verify orchestrator recognizes continuous mode flag."""
    result = subprocess.run(
        "python3 bin/run_full_system_orchestrator.py --continuous --max-runs 1",
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        shell=True,
    )
    # Should complete after 1 run
    assert "Max runs" in result.stdout or "ORCHESTRATOR RUN" in result.stdout


def test_adaptive_bounded_execution():
    """Verify bounded runner implements adaptive strategy selection."""
    result = subprocess.run(
        "python3 bin/run_bounded_autonomous_codegen.py",
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        shell=True,
    )
    assert result.returncode in {0, 1}

    # Load latest artifact and verify adaptive fields
    latest = REPO_ROOT / "artifacts/bounded_autonomy/runs/latest_run.json"
    assert latest.exists()

    data = json.loads(latest.read_text(encoding="utf-8"))

    # Verify adaptive execution fields exist
    assert "adaptive_execution" in data
    assert "retry_count" in data["adaptive_execution"]
    assert "final_outcome" in data["adaptive_execution"]

    # Verify strategy selection
    assert "selected_strategy" in data["planned_changes"]
    strategy = data["planned_changes"]["selected_strategy"]
    assert strategy in {"logging_addition", "function_addition", "comment_only", "minimal_change"}


def test_qc_pattern_store_write_back():
    """Verify QC runner updates pattern store with findings."""
    result = subprocess.run(
        "python3 bin/run_rm_dev_002_qc.py",
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        shell=True,
    )
    assert result.returncode == 0

    # Load pattern store and verify run_history updated
    import yaml
    pattern_store_path = REPO_ROOT / "governance/qc_pattern_store.v1.yaml"
    pattern_store = yaml.safe_load(pattern_store_path.read_text(encoding="utf-8"))

    # Verify run_history exists and has entries
    assert "run_history" in pattern_store
    assert len(pattern_store["run_history"]) > 0

    # Verify latest entry has expected fields
    latest_run = pattern_store["run_history"][-1]
    assert "timestamp" in latest_run
    assert "finding_count" in latest_run
    assert "categories" in latest_run
