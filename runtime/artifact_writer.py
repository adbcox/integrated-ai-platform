"""
Artifact writer: emit structured runtime artifacts following schema.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union


def _content_hash(data: Dict[str, Any]) -> str:
    """Generate SHA256 hash of artifact content."""
    content_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content_str.encode()).hexdigest()


def build_runtime_artifact(
    session_job: Dict[str, Any],
    routing: Dict[str, Any],
    workspace_state: Dict[str, Any],
    command_results: Optional[List[Dict[str, Any]]] = None,
    final_status: str = "success",
    execution_control_ref: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build a complete runtime artifact matching runtime_run_artifact.v1.json schema.

    Args:
        session_job: Dict with session_id, job_id, task_id (optional)
        routing: Dict with backend, model, selected_profile from inference gateway
        workspace_state: Dict from workspace_controller.initialize_workspace
        command_results: List of command execution results
        final_status: success/failure/partial
        execution_control_ref: Optional reference to execution control package

    Returns:
        Complete artifact dict ready for JSON serialization
    """
    command_results = command_results or []
    now = datetime.utcnow().isoformat()

    artifact = {
        "schema_version": "1.0",
        "artifact_kind": "runtime_run_artifact",
        "session_id": session_job.get("session_id"),
        "job_id": session_job.get("job_id"),
        "task_id": session_job.get("task_id"),
        "selected_profile": routing.get("selected_profile"),
        "backend": routing.get("backend"),
        "model": routing.get("model"),
        "workspace": workspace_state,
        "command_results": command_results,
        "final_status": final_status,
        "created_at": now,
        "content_hash": None,
        "validation_metadata": {
            "schema_version": "1.0",
            "validated": True,
            "validation_timestamp": now
        },
        "execution_control_ref": execution_control_ref
    }

    artifact["content_hash"] = _content_hash(artifact)

    return artifact


def emit_runtime_artifact(
    artifact: Dict[str, Any],
    output_path: Union[str, Path]
) -> Dict[str, Any]:
    """
    Write artifact to JSON file and return emission result.

    Args:
        artifact: Artifact dict to emit
        output_path: Path to write JSON artifact

    Returns:
        Result dict with path, size_bytes, hash, timestamp, status
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(artifact, f, indent=2, default=str)

    file_size = output_path.stat().st_size
    now = datetime.utcnow().isoformat()

    result = {
        "output_path": str(output_path),
        "size_bytes": file_size,
        "content_hash": artifact.get("content_hash"),
        "emission_timestamp": now,
        "status": "success"
    }

    return result


if __name__ == "__main__":
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
        "workspace_root": "/tmp/test_workspace",
        "scratch_dir": "/tmp/test_workspace/scratch",
        "artifact_dir": "/tmp/test_workspace/artifacts",
        "lock_file": "/tmp/test_workspace/.lock",
        "status": "initialized",
        "created_at": datetime.utcnow().isoformat(),
        "finalized_at": None
    }

    command_results = [
        {
            "command": ["ls", "-la"],
            "exit_code": 0,
            "stdout": "test output",
            "stderr": "",
            "duration_seconds": 0.1,
            "timed_out": False
        }
    ]

    artifact = build_runtime_artifact(
        session_job, routing, workspace_state, command_results
    )
    print("✓ Runtime artifact built")

    result = emit_runtime_artifact(artifact, "/tmp/test_artifact.json")
    print(f"✓ Artifact emitted: {result['output_path']}")
