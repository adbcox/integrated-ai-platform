"""
Workspace controller: deterministic workspace initialization and cleanup.
"""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union


def _generate_workspace_path(session_id: str, job_id: str) -> str:
    """Generate deterministic workspace path from session and job IDs."""
    combined = f"{session_id}#{job_id}"
    digest = hashlib.sha256(combined.encode()).hexdigest()[:12]
    return f"ws_{session_id[:8]}_{job_id[:8]}_{digest}"


def initialize_workspace(
    session_id: str,
    job_id: str,
    artifact_root: Union[str, Path] = "artifacts/runtime_runs"
) -> Dict[str, Any]:
    """
    Initialize a new workspace with deterministic paths.

    Args:
        session_id: Session identifier
        job_id: Job identifier
        artifact_root: Root directory for runtime artifacts

    Returns:
        workspace_state dict with paths, timestamps, status
    """
    artifact_root = Path(artifact_root)
    artifact_root.mkdir(parents=True, exist_ok=True)

    workspace_name = _generate_workspace_path(session_id, job_id)
    workspace_root = artifact_root / workspace_name

    scratch_dir = workspace_root / "scratch"
    artifact_dir = workspace_root / "artifacts"
    lock_file = workspace_root / ".lock"

    workspace_root.mkdir(parents=True, exist_ok=True)
    scratch_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    lock_file.touch()

    now = datetime.utcnow().isoformat()

    workspace_state = {
        "session_id": session_id,
        "job_id": job_id,
        "workspace_root": str(workspace_root),
        "scratch_dir": str(scratch_dir),
        "artifact_dir": str(artifact_dir),
        "lock_file": str(lock_file),
        "status": "initialized",
        "created_at": now,
        "finalized_at": None
    }

    return workspace_state


def finalize_workspace(
    workspace_state: Dict[str, Any],
    preserve_artifacts: bool = True
) -> Dict[str, Any]:
    """
    Finalize workspace: clean scratch, preserve artifacts, remove lock.

    Args:
        workspace_state: Workspace state dict from initialize_workspace
        preserve_artifacts: If True, keep artifact_dir; if False, remove all

    Returns:
        Updated workspace_state with finalized status and timestamp
    """
    workspace_root = Path(workspace_state["workspace_root"])
    scratch_dir = Path(workspace_state["scratch_dir"])
    artifact_dir = Path(workspace_state["artifact_dir"])
    lock_file = Path(workspace_state["lock_file"])

    if scratch_dir.exists():
        shutil.rmtree(scratch_dir, ignore_errors=True)

    if not preserve_artifacts and artifact_dir.exists():
        shutil.rmtree(artifact_dir, ignore_errors=True)

    if lock_file.exists():
        try:
            lock_file.unlink()
        except Exception:
            pass

    now = datetime.utcnow().isoformat()

    updated_state = workspace_state.copy()
    updated_state["status"] = "finalized"
    updated_state["finalized_at"] = now

    return updated_state


def workspace_to_dict(workspace_state: Dict[str, Any]) -> Dict[str, Any]:
    """Convert workspace state to JSON-serializable dict."""
    return workspace_state.copy()


if __name__ == "__main__":
    session_id = "test_session_001"
    job_id = "test_job_001"

    ws = initialize_workspace(session_id, job_id)
    print(f"✓ Workspace initialized: {ws['workspace_root']}")

    final_ws = finalize_workspace(ws, preserve_artifacts=True)
    print(f"✓ Workspace finalized: status={final_ws['status']}")
