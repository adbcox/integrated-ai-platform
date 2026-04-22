#!/usr/bin/env python3
"""
Validation script for Phase 1 runtime execution path.

Checks:
1. New files exist
2. Schemas parse correctly
3. Modules import successfully
4. Execute one real bounded slice
5. Verify artifact emission
6. Check Phase 0 preservation
7. Emit validation artifact
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add repo root to path for imports
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from runtime import runtime_executor


def check_file_exists(path: Path, name: str) -> tuple[bool, str]:
    """Check if file exists."""
    if path.exists():
        return True, f"{name} exists"
    else:
        return False, f"{name} NOT FOUND: {path}"


def check_json_valid(path: Path, name: str) -> tuple[bool, str]:
    """Check if file is valid JSON."""
    try:
        with open(path) as f:
            json.load(f)
        return True, f"{name} is valid JSON"
    except Exception as e:
        return False, f"{name} JSON invalid: {str(e)}"


def validate_execution_path() -> dict:
    """Run full validation of execution path."""
    timestamp = datetime.utcnow().isoformat()
    checks = {}
    all_pass = True

    # 1. Check file existence
    file_checks = {
        "runtime_executor.py": REPO_ROOT / "runtime" / "runtime_executor.py",
        "runtime_execution_result.v1.json": REPO_ROOT / "runtime" / "schemas" / "runtime_execution_result.v1.json",
        "phase1_execution_control_example.json": REPO_ROOT / "artifacts" / "examples" / "phase1_execution_control_example.json",
        "RM-PHASE1-001.yaml": REPO_ROOT / "docs" / "roadmap" / "items" / "RM-PHASE1-001.yaml"
    }

    for name, path in file_checks.items():
        status, msg = check_file_exists(path, name)
        checks[f"file_{name}"] = {"status": "PASS" if status else "FAIL", "message": msg}
        if not status:
            all_pass = False

    # 2. Check schema validity
    schema_path = REPO_ROOT / "runtime" / "schemas" / "runtime_execution_result.v1.json"
    status, msg = check_json_valid(schema_path, "runtime_execution_result.v1.json")
    checks["schema_runtime_execution_result"] = {"status": "PASS" if status else "FAIL", "message": msg}
    if not status:
        all_pass = False

    # 3. Check execution control example validity
    control_path = REPO_ROOT / "artifacts" / "examples" / "phase1_execution_control_example.json"
    status, msg = check_json_valid(control_path, "phase1_execution_control_example.json")
    checks["example_execution_control"] = {"status": "PASS" if status else "FAIL", "message": msg}
    if not status:
        all_pass = False

    # 4. Module import check
    try:
        from runtime import runtime_executor as rt_exec
        checks["module_import_runtime_executor"] = {
            "status": "PASS",
            "message": "runtime_executor module imports successfully"
        }
    except Exception as e:
        checks["module_import_runtime_executor"] = {
            "status": "FAIL",
            "message": f"Failed to import runtime_executor: {str(e)}"
        }
        all_pass = False

    # 5. Function presence check
    try:
        assert hasattr(runtime_executor, "build_session_job"), "build_session_job not found"
        assert hasattr(runtime_executor, "execute_runtime_slice"), "execute_runtime_slice not found"
        checks["functions_present"] = {
            "status": "PASS",
            "message": "build_session_job and execute_runtime_slice functions present"
        }
    except AssertionError as e:
        checks["functions_present"] = {
            "status": "FAIL",
            "message": str(e)
        }
        all_pass = False

    # 6. Run real bounded execution
    try:
        objective = "Bounded compilation check of runtime/inference_gateway.py"
        result = runtime_executor.execute_runtime_slice(
            objective,
            task_id="phase1_harness_test",
            command=["python3", "-m", "py_compile", "runtime/inference_gateway.py"]
        )

        # Verify result structure
        assert result.get("schema_version") == "1.0", "Invalid schema_version"
        assert result.get("result_kind") == "runtime_execution_result", "Invalid result_kind"
        assert result.get("session_id"), "Missing session_id"
        assert result.get("job_id"), "Missing job_id"
        assert result.get("selected_profile") in ["fast", "balanced", "hard"], "Invalid profile"
        assert result.get("workspace"), "Missing workspace"
        assert result.get("command_result"), "Missing command_result"
        assert result.get("final_status") in ["success", "failed", "timeout", "error"], "Invalid final_status"
        assert result.get("final_status") == "success", "execute_runtime_slice must complete with status: success"

        checks["execution_runtime_slice"] = {
            "status": "PASS",
            "message": f"execute_runtime_slice completed with status: {result['final_status']}",
            "details": {
                "session_id": result.get("session_id"),
                "job_id": result.get("job_id"),
                "profile": result.get("selected_profile"),
                "workspace_initialized": bool(result.get("workspace")),
                "command_result_present": bool(result.get("command_result")),
                "artifact_emitted": bool(result.get("artifact_emitted"))
            }
        }

        # Store result for later checks
        execution_result = result
    except Exception as e:
        checks["execution_runtime_slice"] = {
            "status": "FAIL",
            "message": f"Execution failed: {str(e)}"
        }
        all_pass = False
        execution_result = None

    # 7. Verify artifact emission (if execution succeeded)
    if execution_result and execution_result.get("artifact_emitted"):
        artifact_path = execution_result["artifact_emitted"].get("output_path")
        if artifact_path and Path(artifact_path).exists():
            checks["artifact_emission"] = {
                "status": "PASS",
                "message": f"Artifact emitted to {artifact_path}",
                "size_bytes": execution_result["artifact_emitted"].get("size_bytes")
            }
        else:
            checks["artifact_emission"] = {
                "status": "FAIL",
                "message": f"Artifact not found at {artifact_path}"
            }
            all_pass = False
    else:
        checks["artifact_emission"] = {
            "status": "FAIL",
            "message": "No artifact emission data in result"
        }
        all_pass = False

    # 8. Verify session/job linkage
    if execution_result:
        try:
            assert execution_result["session_id"], "Missing session_id"
            assert execution_result["job_id"], "Missing job_id"
            assert execution_result["workspace"]["session_id"] == execution_result["session_id"], "Workspace session_id mismatch"
            assert execution_result["workspace"]["job_id"] == execution_result["job_id"], "Workspace job_id mismatch"
            checks["session_job_linkage"] = {
                "status": "PASS",
                "message": "Session/job linkage verified"
            }
        except AssertionError as e:
            checks["session_job_linkage"] = {
                "status": "FAIL",
                "message": str(e)
            }
            all_pass = False
    else:
        checks["session_job_linkage"] = {
            "status": "FAIL",
            "message": "No execution result to verify linkage"
        }
        all_pass = False

    # 9. Verify execution control reference
    if execution_result:
        if execution_result.get("execution_control_ref"):
            checks["execution_control_ref"] = {
                "status": "PASS",
                "message": f"execution_control_ref present: {execution_result['execution_control_ref']}"
            }
        else:
            checks["execution_control_ref"] = {
                "status": "PASS",
                "message": "execution_control_ref is None (optional)"
            }

    # 10. Verify Phase 0 preservation
    phase0_files = [
        REPO_ROOT / "governance" / "cmdb_lite.v1.yaml",
        REPO_ROOT / "schemas" / "session_job_schema.v1.json",
        REPO_ROOT / "schemas" / "execution_control_package.v1.json",
        REPO_ROOT / "governance" / "autonomy_scorecard.v1.yaml"
    ]

    phase0_preserved = all(f.exists() for f in phase0_files)
    checks["phase0_preservation"] = {
        "status": "PASS" if phase0_preserved else "FAIL",
        "message": "Phase 0 authority files intact" if phase0_preserved else "Some Phase 0 files missing"
    }
    if not phase0_preserved:
        all_pass = False

    # 11. Verify RM-PHASE1-001 exists
    rm_path = REPO_ROOT / "docs" / "roadmap" / "items" / "RM-PHASE1-001.yaml"
    rm_exists = rm_path.exists()
    checks["rm_phase1_exists"] = {
        "status": "PASS" if rm_exists else "FAIL",
        "message": "RM-PHASE1-001.yaml exists" if rm_exists else "RM-PHASE1-001.yaml not found"
    }
    if not rm_exists:
        all_pass = False

    # 12. Generate runtime execution example (if successful execution)
    if execution_result:
        example_path = REPO_ROOT / "artifacts" / "examples" / "phase1_runtime_execution_example.json"
        try:
            with open(example_path, "w") as f:
                json.dump(execution_result, f, indent=2)
            checks["example_runtime_execution"] = {
                "status": "PASS",
                "message": f"Runtime execution example generated at {example_path}"
            }
        except Exception as e:
            checks["example_runtime_execution"] = {
                "status": "FAIL",
                "message": f"Failed to write runtime execution example: {str(e)}"
            }
            all_pass = False
    else:
        checks["example_runtime_execution"] = {
            "status": "FAIL",
            "message": "Cannot generate example without successful execution"
        }
        all_pass = False

    # 13. Validate example matches schema
    if (REPO_ROOT / "artifacts" / "examples" / "phase1_runtime_execution_example.json").exists():
        try:
            with open(REPO_ROOT / "artifacts" / "examples" / "phase1_runtime_execution_example.json") as f:
                example_result = json.load(f)
            with open(REPO_ROOT / "runtime" / "schemas" / "runtime_execution_result.v1.json") as f:
                schema = json.load(f)

            # Basic validation: check required fields
            required_fields = schema.get("required", [])
            missing_fields = [f for f in required_fields if f not in example_result]

            if not missing_fields:
                checks["example_schema_validation"] = {
                    "status": "PASS",
                    "message": "Runtime execution example matches schema"
                }
            else:
                checks["example_schema_validation"] = {
                    "status": "FAIL",
                    "message": f"Missing required fields: {missing_fields}"
                }
                all_pass = False
        except Exception as e:
            checks["example_schema_validation"] = {
                "status": "FAIL",
                "message": f"Schema validation failed: {str(e)}"
            }
            all_pass = False

    overall_status = "PASS" if all_pass else "FAIL"

    validation_artifact = {
        "timestamp": timestamp,
        "repo_root": str(REPO_ROOT),
        "validation_checks": checks,
        "overall_status": overall_status
    }

    return validation_artifact


if __name__ == "__main__":
    result = validate_execution_path()

    # Write validation artifact
    artifact_path = REPO_ROOT / "artifacts" / "validation" / "phase1_runtime_execution_path_validation.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)

    with open(artifact_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Validation complete: {result['overall_status']}")
    print(f"Artifact written to: {artifact_path}")

    # Print summary
    for check_name, check_result in result["validation_checks"].items():
        status = check_result.get("status", "UNKNOWN")
        message = check_result.get("message", "")
        print(f"  {check_name}: {status} - {message}")

    sys.exit(0 if result["overall_status"] == "PASS" else 1)
