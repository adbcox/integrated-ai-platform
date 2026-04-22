#!/usr/bin/env python3
"""
Runtime entry point for bounded session execution.
Loads session definition, executes commands, records results, writes output.
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def load_session(path: str) -> Dict[str, Any]:
    """Load session definition from JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Session file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)


def execute_validation_step(step: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single validation step command.

    Returns result with command, stdout, stderr, return_code, duration.
    """
    command = step.get("command", "")
    if not command:
        return {
            "step_number": step.get("step_number"),
            "name": step.get("name"),
            "status": "skipped",
            "return_code": None,
            "stdout": "",
            "stderr": "No command specified"
        }

    # Execute command
    start_time = datetime.utcnow()
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        status = "pass" if result.returncode == 0 else "fail"

        return {
            "step_number": step.get("step_number"),
            "name": step.get("name"),
            "command": command,
            "status": status,
            "return_code": result.returncode,
            "stdout": result.stdout[:500],  # Truncate long output
            "stderr": result.stderr[:500],
            "duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
        }

    except subprocess.TimeoutExpired:
        return {
            "step_number": step.get("step_number"),
            "name": step.get("name"),
            "command": command,
            "status": "fail",
            "return_code": 124,
            "stderr": "Command timeout",
            "duration_ms": 30000
        }
    except Exception as e:
        return {
            "step_number": step.get("step_number"),
            "name": step.get("name"),
            "command": command,
            "status": "fail",
            "return_code": 1,
            "stderr": f"Execution error: {str(e)}",
            "duration_ms": 0
        }


def run_session(session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute session by running validation steps.
    Mutates session object with execution results.
    """
    # Initialize execution tracking if needed
    if "command_results" not in session:
        session["command_results"] = []
    if "test_results" not in session:
        session["test_results"] = []

    # Execute each validation step
    all_passed = True
    validation_steps = session.get("validation_steps", [])

    for step in validation_steps:
        step_result = execute_validation_step(step)
        session["command_results"].append(step_result)

        # Track as test result
        session["test_results"].append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "test_suite": "validation_steps",
            "test_name": step.get("name", f"step_{step.get('step_number')}"),
            "status": "pass" if step_result["status"] == "pass" else "fail",
            "duration_seconds": step_result.get("duration_ms", 0) / 1000
        })

        # Check hard stop
        if step.get("hard_stop", True) and step_result["status"] == "fail":
            all_passed = False
            break

    # Update session outcome
    session["final_outcome"] = "success" if all_passed else "failure"
    session["success_criteria_met"] = all_passed
    session["updated_at"] = datetime.utcnow().isoformat() + "Z"

    # Add execution summary to tool_trace
    if "tool_trace" not in session:
        session["tool_trace"] = []

    session["tool_trace"].append({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tool_name": "runtime_session_execution",
        "input": {"validation_steps": len(validation_steps)},
        "output": {
            "steps_executed": len(session["command_results"]),
            "final_outcome": session["final_outcome"]
        },
        "status": "success"
    })

    return session


def write_session_output(session: Dict[str, Any], output_path: str) -> None:
    """Write session output to artifacts/runs/."""
    Path("artifacts/runs").mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(session, f, indent=2)


def validate_schema(session: Dict[str, Any]) -> bool:
    """Quick validation that session has required fields."""
    required = ["session_id", "job_id", "task_id", "objective", "allowed_files",
                "forbidden_files", "validation_steps", "final_outcome"]
    for field in required:
        if field not in session:
            print(f"ERROR: Missing required field: {field}", file=sys.stderr)
            return False
    return True


def main():
    """Main entry point."""
    # Default to example if no argument
    session_path = sys.argv[1] if len(sys.argv) > 1 else "artifacts/examples/session_run_example.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "artifacts/runs/session_run_output.json"

    print(f"Loading session from: {session_path}")
    session = load_session(session_path)

    print(f"Executing {len(session.get('validation_steps', []))} validation steps...")
    session = run_session(session)

    print(f"Validating schema compliance...")
    if not validate_schema(session):
        sys.exit(1)

    print(f"Writing output to: {output_path}")
    write_session_output(session, output_path)

    print(f"\nFinal outcome: {session['final_outcome']}")
    print(f"Success criteria met: {session['success_criteria_met']}")

    return 0 if session["final_outcome"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
