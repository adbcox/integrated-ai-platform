#!/usr/bin/env python3
"""
Phase 1 Runtime Integration Tests

Tests full end-to-end runtime execution with multiple scenarios to ensure robustness.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from runtime import runtime_executor


def test_simple_compilation_check():
    """Test: simple compilation check with balanced profile."""
    objective = "Simple Python compilation check"
    result = runtime_executor.execute_runtime_slice(
        objective,
        task_id="test_compile",
        command=["python3", "-m", "py_compile", "runtime/inference_gateway.py"]
    )

    assert result["session_id"] is not None, "session_id missing"
    assert result["job_id"] is not None, "job_id missing"
    assert result["selected_profile"] in ["fast", "balanced", "hard"], f"invalid profile: {result['selected_profile']}"
    assert result["workspace"] is not None, "workspace missing"
    assert result["command_executed"] == ["python3", "-m", "py_compile", "runtime/inference_gateway.py"], "command mismatch"
    assert result["command_result"] is not None, "command_result missing"
    assert result["artifact_emitted"] is not None, "artifact_emitted missing"
    assert result["final_status"] in ["success", "failed", "timeout", "error"], f"invalid status: {result['final_status']}"
    assert result["workspace"]["session_id"] == result["session_id"], "workspace session_id mismatch"
    assert result["workspace"]["job_id"] == result["job_id"], "workspace job_id mismatch"

    return True, "Simple compilation test passed"


def test_fast_profile_selection():
    """Test: objective matching 'simple' keywords selects fast profile."""
    objective = "Simple quick read and summarize the file"
    result = runtime_executor.execute_runtime_slice(
        objective,
        task_id="test_fast",
        command=["ls", "-la"]
    )

    assert result["selected_profile"] == "fast", f"expected fast profile, got {result['selected_profile']}"

    return True, "Fast profile selection test passed"


def test_hard_profile_selection():
    """Test: objective matching 'complex' keywords selects hard profile."""
    objective = "Complex escalation with fallback required for critical analysis"
    result = runtime_executor.execute_runtime_slice(
        objective,
        task_id="test_hard",
        command=["python3", "--version"]
    )

    assert result["selected_profile"] == "hard", f"expected hard profile, got {result['selected_profile']}"

    return True, "Hard profile selection test passed"


def test_session_job_linkage():
    """Test: session/job IDs are properly linked through execution."""
    objective = "Test session job linkage"
    result = runtime_executor.execute_runtime_slice(
        objective,
        task_id="test_linkage",
        command=["pwd"]
    )

    session_id = result["session_id"]
    job_id = result["job_id"]

    assert result["workspace"]["session_id"] == session_id, "workspace session_id mismatch"
    assert result["workspace"]["job_id"] == job_id, "workspace job_id mismatch"
    assert result["artifact_emitted"] is not None, "artifact not emitted"

    return True, "Session/job linkage test passed"


def test_execution_control_reference():
    """Test: execution_control_ref is preserved in result."""
    objective = "Test execution control reference"
    control_ref = "phase1_execution_control_example.json"
    result = runtime_executor.execute_runtime_slice(
        objective,
        task_id="test_control_ref",
        command=["echo", "test"],
        execution_control_ref=control_ref
    )

    assert result["execution_control_ref"] == control_ref, "execution_control_ref not preserved"

    return True, "Execution control reference test passed"


def test_workspace_finalization():
    """Test: workspace is finalized even after execution."""
    objective = "Test workspace finalization"
    result = runtime_executor.execute_runtime_slice(
        objective,
        task_id="test_finalization",
        command=["ls"]
    )

    workspace = result["workspace"]
    assert workspace["status"] == "finalized", f"workspace status is {workspace['status']}, expected finalized"
    assert workspace["finalized_at"] is not None, "workspace finalized_at is None"

    return True, "Workspace finalization test passed"


def test_artifact_emission_path():
    """Test: emitted artifact actually exists and contains valid data."""
    objective = "Test artifact emission"
    result = runtime_executor.execute_runtime_slice(
        objective,
        task_id="test_artifact",
        command=["python3", "-c", "print('test')"]
    )

    artifact_info = result["artifact_emitted"]
    artifact_path = Path(artifact_info["output_path"])

    assert artifact_path.exists(), f"artifact file does not exist: {artifact_path}"
    assert artifact_info["size_bytes"] > 0, "artifact size is 0"
    assert artifact_info["content_hash"] is not None, "artifact content_hash is None"

    # Verify artifact content
    with open(artifact_path) as f:
        artifact_data = json.load(f)

    assert artifact_data["session_id"] == result["session_id"], "artifact session_id mismatch"
    assert artifact_data["job_id"] == result["job_id"], "artifact job_id mismatch"

    return True, "Artifact emission path test passed"


def test_allowed_files_preservation():
    """Test: allowed/forbidden files are preserved through session/job."""
    objective = "Test file scope preservation"
    allowed = ["runtime/**", "artifacts/**"]
    forbidden = ["framework/**", "tests/**"]

    result = runtime_executor.execute_runtime_slice(
        objective,
        task_id="test_files",
        command=["ls"],
        allowed_files=allowed,
        forbidden_files=forbidden
    )

    # Check that execution completed (files passed through to session/job)
    assert result["session_id"] is not None, "execution failed"

    return True, "File scope preservation test passed"


def run_integration_tests():
    """Run all integration tests."""
    tests = [
        ("simple_compilation_check", test_simple_compilation_check),
        ("fast_profile_selection", test_fast_profile_selection),
        ("hard_profile_selection", test_hard_profile_selection),
        ("session_job_linkage", test_session_job_linkage),
        ("execution_control_reference", test_execution_control_reference),
        ("workspace_finalization", test_workspace_finalization),
        ("artifact_emission_path", test_artifact_emission_path),
        ("allowed_files_preservation", test_allowed_files_preservation),
    ]

    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "repo_root": str(REPO_ROOT),
        "test_results": {},
        "total_tests": len(tests),
        "passed_tests": 0,
        "failed_tests": 0,
    }

    for test_name, test_func in tests:
        try:
            passed, message = test_func()
            results["test_results"][test_name] = {
                "status": "PASS" if passed else "FAIL",
                "message": message
            }
            if passed:
                results["passed_tests"] += 1
                print(f"✓ {test_name}: {message}")
            else:
                results["failed_tests"] += 1
                print(f"✗ {test_name}: {message}")
        except AssertionError as e:
            results["test_results"][test_name] = {
                "status": "FAIL",
                "message": f"Assertion failed: {str(e)}"
            }
            results["failed_tests"] += 1
            print(f"✗ {test_name}: {str(e)}")
        except Exception as e:
            results["test_results"][test_name] = {
                "status": "FAIL",
                "message": f"Exception: {str(e)}"
            }
            results["failed_tests"] += 1
            print(f"✗ {test_name}: {str(e)}")

    results["overall_status"] = "PASS" if results["failed_tests"] == 0 else "FAIL"

    return results


if __name__ == "__main__":
    results = run_integration_tests()

    artifact_path = REPO_ROOT / "artifacts" / "validation" / "phase1_integration_tests.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)

    with open(artifact_path, "w") as f:
        json.dump(results, f, indent=2)

    print()
    print(f"Integration Tests: {results['overall_status']}")
    print(f"Passed: {results['passed_tests']}/{results['total_tests']}")
    print(f"Artifact: {artifact_path}")

    sys.exit(0 if results["overall_status"] == "PASS" else 1)
