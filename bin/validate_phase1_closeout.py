#!/usr/bin/env python3
"""
Phase 1 Closeout Validator

Comprehensive validation of Phase 1 runtime foundation for closure readiness.
Checks: schema compliance, module functionality, session/job alignment,
execution control integration, artifact completeness, and roadmap evidence.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from runtime import runtime_executor, inference_gateway, workspace_controller, command_runner, artifact_writer


def validate_schema_file(path: Path, name: str) -> tuple[bool, str]:
    """Validate a JSON schema file."""
    try:
        with open(path) as f:
            schema = json.load(f)
        if "$schema" not in schema:
            return False, f"{name} missing $schema"
        if "type" not in schema:
            return False, f"{name} missing type"
        if "required" not in schema:
            return False, f"{name} missing required fields"
        return True, f"{name} is valid schema"
    except Exception as e:
        return False, f"{name} invalid: {str(e)}"


def validate_session_job_schema_compliance() -> tuple[bool, str]:
    """Validate that build_session_job produces objects compliant with session_job_schema."""
    try:
        with open(REPO_ROOT / "schemas" / "session_job_schema.v1.json") as f:
            schema = json.load(f)
        required_fields = set(schema.get("required", []))

        session_job = runtime_executor.build_session_job(
            "test objective",
            task_id="test_task",
            allowed_files=["f1"],
            forbidden_files=["f2"]
        )

        session_job_fields = set(session_job.keys())
        missing = required_fields - session_job_fields

        if missing:
            return False, f"Session/job missing required fields: {missing}"

        if session_job["session_id"] is None:
            return False, "session_id is None"
        if session_job["job_id"] is None:
            return False, "job_id is None"
        if session_job["allowed_files"] != ["f1"]:
            return False, "allowed_files not preserved"
        if session_job["forbidden_files"] != ["f2"]:
            return False, "forbidden_files not preserved"

        return True, "Session/job compliant with schema"
    except Exception as e:
        return False, f"Session/job compliance check failed: {str(e)}"


def validate_execution_control_package_example() -> tuple[bool, str]:
    """Validate execution control package example against schema."""
    try:
        with open(REPO_ROOT / "schemas" / "execution_control_package.v1.json") as f:
            schema = json.load(f)
        required_fields = set(schema.get("required", []))

        with open(REPO_ROOT / "artifacts" / "examples" / "phase1_execution_control_example.json") as f:
            example = json.load(f)

        example_fields = set(example.keys())
        missing = required_fields - example_fields

        if missing:
            return False, f"Execution control example missing required fields: {missing}"

        return True, "Execution control package example valid"
    except Exception as e:
        return False, f"Execution control package check failed: {str(e)}"


def validate_runtime_execution_result_example() -> tuple[bool, str]:
    """Validate runtime execution result example against schema."""
    try:
        with open(REPO_ROOT / "runtime" / "schemas" / "runtime_execution_result.v1.json") as f:
            schema = json.load(f)
        required_fields = set(schema.get("required", []))

        with open(REPO_ROOT / "artifacts" / "examples" / "phase1_runtime_execution_example.json") as f:
            example = json.load(f)

        example_fields = set(example.keys())
        missing = required_fields - example_fields

        if missing:
            return False, f"Runtime execution example missing required fields: {missing}"

        if example["session_id"] != example["workspace"]["session_id"]:
            return False, "Session ID mismatch between result and workspace"

        if example["job_id"] != example["workspace"]["job_id"]:
            return False, "Job ID mismatch between result and workspace"

        return True, "Runtime execution result example valid"
    except Exception as e:
        return False, f"Runtime execution result check failed: {str(e)}"


def validate_module_imports() -> tuple[bool, str]:
    """Validate that all runtime modules import correctly."""
    try:
        from runtime import (
            inference_gateway, workspace_controller, artifact_writer,
            command_runner, runtime_executor
        )
        return True, "All runtime modules import successfully"
    except Exception as e:
        return False, f"Module import failed: {str(e)}"


def validate_profile_selection() -> tuple[bool, str]:
    """Validate profile selection heuristics."""
    try:
        test_cases = [
            ("simple read/report task", "fast"),
            ("normal coding or multi-step repo task", "balanced"),
            ("explicit escalation / high-complexity / fallback request", "hard"),
        ]

        for objective, expected_profile in test_cases:
            selection = inference_gateway.select_profile(objective)
            selected = selection.get("selected_profile")
            if selected != expected_profile:
                return False, f"Profile selection failed: {objective} -> {selected}, expected {expected_profile}"

        return True, "Profile selection heuristics working correctly"
    except Exception as e:
        return False, f"Profile selection check failed: {str(e)}"


def validate_workspace_lifecycle() -> tuple[bool, str]:
    """Validate workspace initialization and finalization."""
    try:
        session_id = "test_session_001"
        job_id = "test_job_001"

        ws = workspace_controller.initialize_workspace(session_id, job_id)

        if ws["session_id"] != session_id:
            return False, "Workspace session_id mismatch"
        if ws["job_id"] != job_id:
            return False, "Workspace job_id mismatch"
        if ws["status"] != "initialized":
            return False, "Workspace status not initialized"
        if not Path(ws["workspace_root"]).exists():
            return False, "Workspace root not created"

        final_ws = workspace_controller.finalize_workspace(ws, preserve_artifacts=True)

        if final_ws["status"] != "finalized":
            return False, "Workspace status not finalized"
        if final_ws["finalized_at"] is None:
            return False, "Finalized_at is None"

        return True, "Workspace lifecycle correct"
    except Exception as e:
        return False, f"Workspace lifecycle check failed: {str(e)}"


def validate_command_whitelist() -> tuple[bool, str]:
    """Validate command whitelisting enforcement."""
    try:
        # Allowed command
        result = command_runner.execute_command(["python3", "-c", "print('ok')"])
        if not result["allowed"]:
            return False, "Allowed command was rejected"

        # Forbidden command
        result = command_runner.execute_command(["rm", "-rf", "/"])
        if result["allowed"]:
            return False, "Forbidden command was allowed"

        return True, "Command whitelist enforcement working"
    except Exception as e:
        return False, f"Command whitelist check failed: {str(e)}"


def validate_artifact_emission() -> tuple[bool, str]:
    """Validate artifact building and emission."""
    try:
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
            "workspace_root": "/tmp/test_ws",
            "scratch_dir": "/tmp/test_ws/scratch",
            "artifact_dir": "/tmp/test_ws/artifacts",
            "lock_file": "/tmp/test_ws/.lock",
            "status": "initialized",
            "created_at": datetime.utcnow().isoformat(),
            "finalized_at": None
        }

        command_result = {
            "command": ["ls"],
            "allowed": True,
            "exit_code": 0,
            "stdout": "test",
            "stderr": "",
            "duration_seconds": 0.1,
            "cwd": None,
            "timed_out": False
        }

        artifact = artifact_writer.build_runtime_artifact(
            session_job, routing, workspace_state, [command_result]
        )

        if artifact["session_id"] != session_job["session_id"]:
            return False, "Artifact session_id mismatch"
        if artifact["job_id"] != session_job["job_id"]:
            return False, "Artifact job_id mismatch"
        if artifact["content_hash"] is None:
            return False, "Artifact content_hash is None"

        return True, "Artifact emission working correctly"
    except Exception as e:
        return False, f"Artifact emission check failed: {str(e)}"


def validate_execution_control_linkage() -> tuple[bool, str]:
    """Validate that execution control reference survives through execution."""
    try:
        with open(REPO_ROOT / "artifacts" / "examples" / "phase1_runtime_execution_example.json") as f:
            result = json.load(f)

        if "execution_control_ref" not in result:
            return False, "execution_control_ref field missing from result"

        return True, "Execution control linkage present in result"
    except Exception as e:
        return False, f"Execution control linkage check failed: {str(e)}"


def validate_roadmap_consistency() -> tuple[bool, str]:
    """Validate roadmap files are consistent with repo state."""
    try:
        import yaml

        with open(REPO_ROOT / "docs" / "roadmap" / "items" / "RM-PHASE1-001.yaml") as f:
            rm_item = yaml.safe_load(f)

        if rm_item.get("status") != "completed":
            return False, "RM-PHASE1-001 status is not completed"

        expected_outputs = [
            "governance/runtime_profiles.v1.yaml",
            "runtime/inference_gateway.py",
            "runtime/workspace_controller.py",
            "runtime/artifact_writer.py",
            "runtime/command_runner.py",
            "runtime/runtime_executor.py",
            "runtime/schemas/",
            "artifacts/validation/phase1_runtime_foundation_validation.json",
            "artifacts/validation/phase1_runtime_execution_path_validation.json",
            "artifacts/validation/phase1_closeout_validation.json",
            "artifacts/validation/phase1_integration_tests.json",
            "artifacts/examples/phase1_runtime_run_example.json",
            "artifacts/examples/phase1_execution_control_example.json",
            "artifacts/examples/phase1_runtime_execution_example.json",
            "bin/validate_phase1_runtime_foundation.py",
            "bin/validate_phase1_runtime_execution_path.py",
            "bin/validate_phase1_closeout.py",
            "bin/test_phase1_runtime_integration.py"
        ]

        artifact_outputs = rm_item.get("ai_operability", {}).get("artifact_outputs", [])
        for expected in expected_outputs:
            if expected not in artifact_outputs:
                return False, f"Expected artifact {expected} not in roadmap output list"

        return True, "Roadmap consistency verified"
    except Exception as e:
        return False, f"Roadmap consistency check failed: {str(e)}"


def validate_phase0_preservation() -> tuple[bool, str]:
    """Validate that Phase 0 authority files are intact."""
    try:
        phase0_files = [
            REPO_ROOT / "governance" / "cmdb_lite.v1.yaml",
            REPO_ROOT / "schemas" / "session_job_schema.v1.json",
            REPO_ROOT / "schemas" / "execution_control_package.v1.json",
            REPO_ROOT / "governance" / "autonomy_scorecard.v1.yaml",
            REPO_ROOT / "docs" / "standards" / "DEFINITION_OF_DONE.md"
        ]

        for f in phase0_files:
            if not f.exists():
                return False, f"Phase 0 file missing: {f}"

        return True, "Phase 0 authority files intact"
    except Exception as e:
        return False, f"Phase 0 preservation check failed: {str(e)}"


def validate_all_schema_files() -> tuple[bool, str]:
    """Validate all JSON schema files are well-formed."""
    try:
        schema_files = [
            REPO_ROOT / "runtime" / "schemas" / "inference_request.v1.json",
            REPO_ROOT / "runtime" / "schemas" / "inference_response.v1.json",
            REPO_ROOT / "runtime" / "schemas" / "profile_selection.v1.json",
            REPO_ROOT / "runtime" / "schemas" / "workspace_state.v1.json",
            REPO_ROOT / "runtime" / "schemas" / "runtime_run_artifact.v1.json",
            REPO_ROOT / "runtime" / "schemas" / "runtime_execution_result.v1.json",
        ]

        for schema_file in schema_files:
            if not schema_file.exists():
                return False, f"Schema file missing: {schema_file}"

            with open(schema_file) as f:
                json.load(f)

        return True, "All runtime schemas valid"
    except Exception as e:
        return False, f"Schema validation failed: {str(e)}"


def run_closeout_validation() -> dict:
    """Run all Phase 1 closeout validation checks."""
    timestamp = datetime.utcnow().isoformat()
    checks = {}
    all_pass = True

    validators = [
        ("module_imports", validate_module_imports),
        ("schema_files", validate_all_schema_files),
        ("session_job_schema_compliance", validate_session_job_schema_compliance),
        ("execution_control_package_example", validate_execution_control_package_example),
        ("runtime_execution_result_example", validate_runtime_execution_result_example),
        ("profile_selection", validate_profile_selection),
        ("workspace_lifecycle", validate_workspace_lifecycle),
        ("command_whitelist", validate_command_whitelist),
        ("artifact_emission", validate_artifact_emission),
        ("execution_control_linkage", validate_execution_control_linkage),
        ("roadmap_consistency", validate_roadmap_consistency),
        ("phase0_preservation", validate_phase0_preservation),
    ]

    for check_name, validator_func in validators:
        try:
            status, message = validator_func()
            checks[check_name] = {
                "status": "PASS" if status else "FAIL",
                "message": message
            }
            if not status:
                all_pass = False
        except Exception as e:
            checks[check_name] = {
                "status": "FAIL",
                "message": f"Validator exception: {str(e)}"
            }
            all_pass = False

    overall_status = "PASS" if all_pass else "FAIL"

    validation_artifact = {
        "timestamp": timestamp,
        "repo_root": str(REPO_ROOT),
        "validation_checks": checks,
        "overall_status": overall_status,
        "validator_version": "1.0"
    }

    return validation_artifact


if __name__ == "__main__":
    result = run_closeout_validation()

    artifact_path = REPO_ROOT / "artifacts" / "validation" / "phase1_closeout_validation.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)

    with open(artifact_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Phase 1 Closeout Validation: {result['overall_status']}")
    print(f"Artifact: {artifact_path}")
    print()

    for check_name, check_result in result["validation_checks"].items():
        status = check_result.get("status", "UNKNOWN")
        message = check_result.get("message", "")
        symbol = "✓" if status == "PASS" else "✗"
        print(f"{symbol} {check_name}: {message}")

    sys.exit(0 if result["overall_status"] == "PASS" else 1)
