"""
Runtime executor: orchestrate bounded execution slices with session/job linkage and artifact emission.
Instrumented with execution tracing (OPS-001), failure classification (OPS-002), and performance profiling (OPS-003).
"""

import json
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from runtime import (
    inference_gateway,
    workspace_controller,
    artifact_writer,
    command_runner,
    execution_tracer,
    failure_classifier,
    performance_profiler
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def build_session_job(
    objective: str,
    task_id: Optional[str] = None,
    allowed_files: Optional[List[str]] = None,
    forbidden_files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Build a session/job pair for execution matching session_job_schema.v1.json.

    Args:
        objective: High-level execution objective
        task_id: Optional task identifier
        allowed_files: Optional list of allowed file patterns
        forbidden_files: Optional list of forbidden file patterns

    Returns:
        session_job dict with session_id, job_id, objective, and execution context
    """
    session_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    session_job = {
        "schema_version": "1.0",
        "session_id": session_id,
        "job_id": job_id,
        "task_id": task_id,
        "objective": objective,
        "status": "initialized",
        "created_at": now,
        "allowed_files": allowed_files or [],
        "forbidden_files": forbidden_files or [],
        "validation_steps": [
            "initialize_workspace",
            "select_profile",
            "execute_command",
            "build_artifact",
            "emit_artifact",
            "finalize_workspace"
        ],
        "final_outcome": None
    }

    return session_job


def execute_runtime_slice(
    objective: str,
    task_id: Optional[str] = None,
    command: Optional[List[str]] = None,
    execution_control_ref: Optional[str] = None,
    allowed_files: Optional[List[str]] = None,
    forbidden_files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Execute a bounded runtime slice end-to-end with tracing, failure classification, and performance profiling.

    Orchestrates: session/job → profile selection → workspace → command execution → artifact emission

    Args:
        objective: Execution objective
        task_id: Optional task identifier
        command: Command to execute (list of strings)
        execution_control_ref: Optional reference to execution control package
        allowed_files: Optional allowed file patterns
        forbidden_files: Optional forbidden file patterns

    Returns:
        Result dict matching runtime_execution_result.v1.json schema
    """
    if command is None:
        command = ["python3", "-m", "py_compile", "runtime/inference_gateway.py"]

    start_time = time.time()
    final_status = "success"
    execution_error = None
    ops_artifacts = {}

    # Step 1: Build session/job
    try:
        session_job = build_session_job(objective, task_id, allowed_files, forbidden_files)
        session_id = session_job["session_id"]
        job_id = session_job["job_id"]

        tracer = execution_tracer.ExecutionTracer(session_id, job_id, objective)
        profiler = performance_profiler.PerformanceProfiler(session_id, job_id, task_id)
        tracer.record_stage_start("session_job")
    except Exception as e:
        return {
            "schema_version": "1.0",
            "result_kind": "runtime_execution_result",
            "session_id": None,
            "job_id": None,
            "task_id": task_id,
            "objective": objective,
            "selected_profile": None,
            "backend": None,
            "model": None,
            "workspace": None,
            "command_executed": command,
            "command_result": None,
            "artifact_emitted": None,
            "final_status": "error",
            "execution_duration_seconds": time.time() - start_time,
            "execution_control_ref": execution_control_ref,
            "created_at": datetime.utcnow().isoformat(),
            "validation_metadata": {
                "schema_version": "1.0",
                "validated": False,
                "validation_timestamp": datetime.utcnow().isoformat()
            }
        }

    session_job_duration = time.time() - start_time
    tracer.record_stage_complete("session_job", session_job_duration)
    profiler.record_stage_timing("session_job_creation", session_job_duration)

    # Step 2: Select profile
    profile_start = time.time()
    tracer.record_stage_start("profile_selection")
    routing = None
    try:
        profile_selection = inference_gateway.select_profile(objective)
        selected_profile = profile_selection["selected_profile"]
        profiles = inference_gateway.load_runtime_profiles()
        profile_config = profiles["profiles"][selected_profile]
        routing = {
            "selected_profile": selected_profile,
            "backend": profile_config["backend"],
            "model": profile_config["model"]
        }
        profile_duration = time.time() - profile_start
        tracer.record_stage_complete("profile_selection", profile_duration, {
            "selected_profile": selected_profile,
            "backend": profile_config["backend"],
            "model": profile_config["model"]
        })
        tracer.record_profile_selected(selected_profile, profile_config["backend"], profile_config["model"])
        profiler.selected_profile = selected_profile
        profiler.record_stage_timing("profile_selection", profile_duration)
    except Exception as e:
        profile_duration = time.time() - profile_start
        execution_error = f"Profile selection failed: {str(e)}"
        final_status = "error"
        tracer.record_stage_error("profile_selection", execution_error, profile_duration)
        routing = None

    # Step 3: Initialize workspace
    workspace_state = None
    if final_status == "success":
        workspace_start = time.time()
        tracer.record_stage_start("workspace_init")
        try:
            workspace_state = workspace_controller.initialize_workspace(session_id, job_id)
            workspace_duration = time.time() - workspace_start
            tracer.record_stage_complete("workspace_init", workspace_duration)
            profiler.record_stage_timing("workspace_initialization", workspace_duration)
        except Exception as e:
            workspace_duration = time.time() - workspace_start
            execution_error = f"Workspace initialization failed: {str(e)}"
            final_status = "error"
            tracer.record_stage_error("workspace_init", execution_error, workspace_duration)

    # Step 4: Execute command
    command_result = None
    if final_status == "success" and workspace_state:
        command_start = time.time()
        tracer.record_command_started(command)
        try:
            workspace_root = workspace_state["workspace_root"]
            command_result = command_runner.execute_command(
                command,
                cwd=REPO_ROOT,
                timeout_seconds=30
            )
            command_duration = time.time() - command_start
            tracer.record_command_completed(command, command_duration, command_result.get("exit_code", -1))
            profiler.record_stage_timing("command_execution", command_duration)
            profiler.record_command_metrics(
                command,
                command_duration,
                command_result.get("exit_code"),
                len(command_result.get("stdout", "")),
                len(command_result.get("stderr", ""))
            )

            if command_result.get("timed_out"):
                final_status = "timeout"
            elif not command_result.get("allowed"):
                final_status = "failed"
            elif command_result.get("exit_code") != 0:
                final_status = "failed"
        except Exception as e:
            command_duration = time.time() - command_start
            execution_error = f"Command execution failed: {str(e)}"
            final_status = "error"
            command_result = None
            profiler.record_stage_timing("command_execution", command_duration)

    # Step 5: Build artifact
    artifact = None
    if final_status != "error" and routing and workspace_state:
        try:
            artifact = artifact_writer.build_runtime_artifact(
                session_job=session_job,
                routing=routing,
                workspace_state=workspace_state,
                command_results=[command_result] if command_result else [],
                final_status=final_status,
                execution_control_ref=execution_control_ref
            )
        except Exception as e:
            execution_error = f"Artifact build failed: {str(e)}"
            final_status = "error"
            artifact = None

    # Step 6: Emit artifact
    artifact_emitted = None
    artifact_start = time.time()
    tracer.record_stage_start("artifact_emission")
    if artifact and workspace_state:
        try:
            artifact_dir = Path(workspace_state["artifact_dir"])
            artifact_path = artifact_dir / f"runtime_execution_{session_id[:8]}.json"
            emission_result = artifact_writer.emit_runtime_artifact(artifact, artifact_path)
            artifact_emitted = {
                "output_path": emission_result["output_path"],
                "size_bytes": emission_result["size_bytes"],
                "content_hash": emission_result["content_hash"],
                "emission_timestamp": emission_result["emission_timestamp"],
                "status": emission_result["status"]
            }
            tracer.record_artifact_emitted(str(artifact_path), emission_result["size_bytes"])
            artifact_duration = time.time() - artifact_start
            tracer.record_stage_complete("artifact_emission", artifact_duration)
            profiler.record_stage_timing("artifact_emission", artifact_duration)
        except Exception as e:
            artifact_duration = time.time() - artifact_start
            execution_error = f"Artifact emission failed: {str(e)}"
            if final_status == "success":
                final_status = "failed"
            tracer.record_stage_error("artifact_emission", execution_error, artifact_duration)

    # Step 7: Finalize workspace
    finalize_start = time.time()
    tracer.record_stage_start("workspace_finalize")
    if workspace_state:
        try:
            workspace_state = workspace_controller.finalize_workspace(workspace_state, preserve_artifacts=True)
            finalize_duration = time.time() - finalize_start
            tracer.record_stage_complete("workspace_finalize", finalize_duration)
            profiler.record_stage_timing("workspace_finalization", finalize_duration)
        except Exception as e:
            finalize_duration = time.time() - finalize_start
            tracer.record_stage_error("workspace_finalize", str(e), finalize_duration)
            if final_status == "success":
                final_status = "failed"

    # Step 8: Emit OPS artifacts (trace, failure record, performance profile)
    if workspace_state:
        artifact_dir = Path(workspace_state["artifact_dir"])

        try:
            trace_path = artifact_dir / f"execution_trace_{session_id[:8]}.json"
            trace_result = tracer.emit_trace(trace_path)
            ops_artifacts["execution_trace"] = trace_result
        except Exception as e:
            pass

        if final_status != "success":
            try:
                failure_record = failure_classifier.classify_failure(
                    session_id=session_id,
                    job_id=job_id,
                    task_id=task_id,
                    stage_failed="execution",
                    error_message=execution_error or "Execution failed",
                    exit_code=command_result.get("exit_code") if command_result else None,
                    command_executed=command,
                    retry_attempt=0
                )
                failure_path = artifact_dir / f"failure_record_{session_id[:8]}.json"
                failure_result = failure_classifier.emit_failure_record(failure_record, failure_path)
                ops_artifacts["failure_record"] = failure_result
            except Exception as e:
                pass

        try:
            perf_profile = profiler.build_profile()
            perf_path = artifact_dir / f"performance_profile_{session_id[:8]}.json"
            perf_result = profiler.emit_profile(perf_path)
            ops_artifacts["performance_profile"] = perf_result
        except Exception as e:
            pass

    # Build result
    duration = time.time() - start_time

    result = {
        "schema_version": "1.0",
        "result_kind": "runtime_execution_result",
        "session_id": session_id,
        "job_id": job_id,
        "task_id": task_id,
        "objective": objective,
        "selected_profile": routing.get("selected_profile") if routing else None,
        "backend": routing.get("backend") if routing else None,
        "model": routing.get("model") if routing else None,
        "workspace": workspace_state,
        "command_executed": command,
        "command_result": command_result,
        "artifact_emitted": artifact_emitted,
        "ops_artifacts": ops_artifacts,
        "final_status": final_status,
        "execution_duration_seconds": round(duration, 3),
        "execution_control_ref": execution_control_ref,
        "created_at": datetime.utcnow().isoformat(),
        "validation_metadata": {
            "schema_version": "1.0",
            "validated": True,
            "validation_timestamp": datetime.utcnow().isoformat()
        }
    }

    return result


if __name__ == "__main__":
    objective = "Bounded compilation check of runtime/inference_gateway.py"
    result = execute_runtime_slice(objective, task_id="phase1_harness_test")
    print(f"✓ Runtime execution completed: {result['final_status']}")
    print(f"  Session: {result['session_id']}")
    print(f"  Job: {result['job_id']}")
    print(f"  Profile: {result['selected_profile']}")
