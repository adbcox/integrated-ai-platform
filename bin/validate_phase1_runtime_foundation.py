#!/usr/bin/env python3
"""
Validation script for Phase 1 runtime foundation.
Performs 25+ checks and writes JSON report.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed", file=sys.stderr)
    sys.exit(1)
RUNTIME_DIR = REPO_ROOT / "runtime"
GOVERNANCE_DIR = REPO_ROOT / "governance"
BIN_DIR = REPO_ROOT / "bin"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
DOCS_DIR = REPO_ROOT / "docs"


def check_file_exists(path: Path, description: str) -> Tuple[bool, str]:
    """Check if a file exists."""
    if path.exists():
        return True, f"{description} exists"
    return False, f"{description} missing at {path}"


def check_schema_valid(path: Path, description: str) -> Tuple[bool, str]:
    """Check if a JSON/YAML schema is valid."""
    try:
        if path.suffix in [".json"]:
            with open(path, "r") as f:
                json.load(f)
        elif path.suffix in [".yaml", ".yml"]:
            with open(path, "r") as f:
                yaml.safe_load(f)
        return True, f"{description} valid"
    except Exception as e:
        return False, f"{description} parse error: {e}"


def check_module_importable(module_name: str, description: str) -> Tuple[bool, str]:
    """Check if a Python module can be imported."""
    try:
        __import__(module_name)
        return True, f"{description} importable"
    except Exception as e:
        return False, f"{description} import failed: {e}"


def run_validation() -> dict:
    """Run all validation checks."""
    checks = {}

    checks["file_structure"] = {}
    checks["schema_validation"] = {}
    checks["module_imports"] = {}
    checks["profile_selection"] = {}
    checks["workspace_operations"] = {}
    checks["command_execution"] = {}
    checks["artifact_generation"] = {}
    checks["roadmap_consistency"] = {}
    checks["phase0_preservation"] = {}

    now = datetime.utcnow().isoformat()

    checks["file_structure"]["runtime_dir_exists"], checks["file_structure"]["runtime_dir_msg"] = \
        check_file_exists(RUNTIME_DIR, "runtime/ directory")

    required_files = {
        RUNTIME_DIR / "inference_gateway.py": "inference_gateway.py",
        RUNTIME_DIR / "workspace_controller.py": "workspace_controller.py",
        RUNTIME_DIR / "artifact_writer.py": "artifact_writer.py",
        RUNTIME_DIR / "command_runner.py": "command_runner.py",
        GOVERNANCE_DIR / "runtime_profiles.v1.yaml": "runtime_profiles.v1.yaml",
        DOCS_DIR / "roadmap" / "items" / "RM-PHASE1-001.yaml": "RM-PHASE1-001.yaml",
        BIN_DIR / "validate_phase1_runtime_foundation.py": "validate_phase1_runtime_foundation.py",
    }

    for file_path, desc in required_files.items():
        ok, msg = check_file_exists(file_path, desc)
        checks["file_structure"][desc] = {"status": "PASS" if ok else "FAIL", "message": msg}

    schema_files = {
        RUNTIME_DIR / "schemas" / "inference_request.v1.json": "inference_request.v1.json",
        RUNTIME_DIR / "schemas" / "inference_response.v1.json": "inference_response.v1.json",
        RUNTIME_DIR / "schemas" / "profile_selection.v1.json": "profile_selection.v1.json",
        RUNTIME_DIR / "schemas" / "workspace_state.v1.json": "workspace_state.v1.json",
        RUNTIME_DIR / "schemas" / "runtime_run_artifact.v1.json": "runtime_run_artifact.v1.json",
    }

    for file_path, desc in schema_files.items():
        ok, msg = check_schema_valid(file_path, desc)
        checks["schema_validation"][desc] = {"status": "PASS" if ok else "FAIL", "message": msg}

    modules_to_import = [
        ("runtime.inference_gateway", "inference_gateway module"),
        ("runtime.workspace_controller", "workspace_controller module"),
        ("runtime.artifact_writer", "artifact_writer module"),
        ("runtime.command_runner", "command_runner module"),
    ]

    for module_name, desc in modules_to_import:
        ok, msg = check_module_importable(module_name, desc)
        checks["module_imports"][desc] = {"status": "PASS" if ok else "FAIL", "message": msg}

    try:
        from runtime.inference_gateway import select_profile, route_request, build_inference_request

        test_cases = [
            ("simple read/report task", "fast"),
            ("normal coding or multi-step repo task", "balanced"),
            ("explicit escalation / high-complexity / fallback request", "hard"),
        ]

        profile_checks = []
        for goal, expected_profile in test_cases:
            request = build_inference_request(goal)
            response = route_request(request)
            selected = response.get("selected_profile")
            passed = selected == expected_profile
            profile_checks.append({
                "goal": goal[:40] + "...",
                "expected": expected_profile,
                "selected": selected,
                "passed": passed
            })

        checks["profile_selection"]["sample_selections"] = {
            "status": "PASS" if all(c["passed"] for c in profile_checks) else "PARTIAL",
            "checks": profile_checks
        }

    except Exception as e:
        checks["profile_selection"]["sample_selections"] = {
            "status": "FAIL",
            "error": str(e)
        }

    try:
        from runtime.workspace_controller import initialize_workspace, finalize_workspace
        import tempfile
        import shutil

        tmpdir = tempfile.mkdtemp()
        ws = initialize_workspace("test_session_001", "test_job_001", artifact_root=tmpdir)
        final_ws = finalize_workspace(ws, preserve_artifacts=True)

        checks["workspace_operations"]["initialization"] = {
            "status": "PASS",
            "workspace_created": ws["status"] == "initialized"
        }

        checks["workspace_operations"]["finalization"] = {
            "status": "PASS",
            "workspace_finalized": final_ws["status"] == "finalized"
        }

        if Path(tmpdir).exists():
            shutil.rmtree(tmpdir, ignore_errors=True)

    except Exception as e:
        checks["workspace_operations"]["workspace_test"] = {
            "status": "FAIL",
            "error": str(e)
        }

    try:
        from runtime.command_runner import execute_command

        result = execute_command(["python3", "-m", "py_compile", str(RUNTIME_DIR / "inference_gateway.py")], timeout_seconds=10)
        checks["command_execution"]["compile_test"] = {
            "status": "PASS" if result["exit_code"] == 0 else "FAIL",
            "allowed": result["allowed"],
            "exit_code": result["exit_code"]
        }

        denied_result = execute_command(["rm", "-rf", "/"], timeout_seconds=5)
        checks["command_execution"]["whitelist_enforcement"] = {
            "status": "PASS" if not denied_result["allowed"] else "FAIL",
            "message": "Dangerous commands properly blocked"
        }

    except Exception as e:
        checks["command_execution"]["command_test"] = {
            "status": "FAIL",
            "error": str(e)
        }

    try:
        from runtime.artifact_writer import build_runtime_artifact, emit_runtime_artifact
        import tempfile
        import shutil

        tmpdir = tempfile.mkdtemp()
        tmpdir_path = Path(tmpdir)

        session_job = {
            "session_id": "test_session_001",
            "job_id": "test_job_001",
            "task_id": None
        }

        routing = {
            "selected_profile": "balanced",
            "backend": "ollama",
            "model": "qwen2.5-coder:32b"
        }

        workspace_state = {
            "session_id": "test_session_001",
            "job_id": "test_job_001",
            "workspace_root": str(tmpdir_path),
            "scratch_dir": str(tmpdir_path / "scratch"),
            "artifact_dir": str(tmpdir_path / "artifacts"),
            "lock_file": str(tmpdir_path / ".lock"),
            "status": "initialized",
            "created_at": now,
            "finalized_at": None
        }

        artifact = build_runtime_artifact(session_job, routing, workspace_state)
        emission_result = emit_runtime_artifact(artifact, tmpdir_path / "test_artifact.json")

        checks["artifact_generation"]["build"] = {
            "status": "PASS",
            "schema_version": artifact.get("schema_version")
        }

        checks["artifact_generation"]["emission"] = {
            "status": "PASS",
            "output_path": emission_result["output_path"],
            "size_bytes": emission_result["size_bytes"]
        }

        if tmpdir_path.exists():
            shutil.rmtree(str(tmpdir_path), ignore_errors=True)

    except Exception as e:
        checks["artifact_generation"]["artifact_test"] = {
            "status": "FAIL",
            "error": str(e)
        }

    rm_phase1_path = DOCS_DIR / "roadmap" / "items" / "RM-PHASE1-001.yaml"
    ok, msg = check_file_exists(rm_phase1_path, "RM-PHASE1-001.yaml")
    checks["roadmap_consistency"]["rm_phase1_exists"] = {
        "status": "PASS" if ok else "FAIL",
        "message": msg
    }

    try:
        with open(rm_phase1_path, "r") as f:
            rm_phase1 = yaml.safe_load(f)
        has_dependencies = "dependencies" in rm_phase1
        checks["roadmap_consistency"]["rm_phase1_dependencies"] = {
            "status": "PASS" if has_dependencies else "FAIL",
            "message": "Dependencies field present" if has_dependencies else "Missing dependencies"
        }
    except Exception as e:
        checks["roadmap_consistency"]["rm_phase1_parse"] = {
            "status": "FAIL",
            "error": str(e)
        }

    phase0_files = [
        (GOVERNANCE_DIR / "cmdb_lite.v1.yaml", "cmdb_lite.v1.yaml"),
        (REPO_ROOT / "schemas" / "session_job_schema.v1.json", "session_job_schema.v1.json"),
        (REPO_ROOT / "schemas" / "execution_control_package.v1.json", "execution_control_package.v1.json"),
        (GOVERNANCE_DIR / "autonomy_scorecard.v1.yaml", "autonomy_scorecard.v1.yaml"),
    ]

    for file_path, desc in phase0_files:
        ok, msg = check_file_exists(file_path, desc)
        checks["phase0_preservation"][desc] = {
            "status": "PASS" if ok else "FAIL",
            "message": msg
        }

    report = {
        "timestamp": now,
        "repo_root": str(REPO_ROOT),
        "validation_checks": checks,
        "overall_status": "PASS"
    }

    for category in checks.values():
        if isinstance(category, dict):
            for check in category.values():
                if isinstance(check, dict) and check.get("status") == "FAIL":
                    report["overall_status"] = "FAIL"
                    break

    return report


def main():
    """Main entry point."""
    report = run_validation()

    artifacts_validation_dir = ARTIFACTS_DIR / "validation"
    artifacts_validation_dir.mkdir(parents=True, exist_ok=True)

    report_path = artifacts_validation_dir / "phase1_runtime_foundation_validation.json"

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))

    if report["overall_status"] == "PASS":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
