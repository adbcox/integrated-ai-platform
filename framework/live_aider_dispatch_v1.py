"""LiveAiderDispatchV1: structured live Aider dispatch surface (no broad orchestration)."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import yaml


DISPATCH_STATUS_DRY_RUN = "dry_run"
DISPATCH_STATUS_LIVE = "live"
DISPATCH_STATUS_BLOCKED = "blocked"
DISPATCH_STATUS_COMPLETED = "completed"
DISPATCH_STATUS_FAILED = "failed"

EXECUTION_MODE_LOCAL_FIRST = "local_first"
REPO_ROOT = Path(__file__).resolve().parents[1]


def _resolve_local_model() -> str:
    """Resolve a local Ollama model from runtime profile authority."""
    profiles_path = REPO_ROOT / "governance" / "runtime_profiles.v1.yaml"
    data = yaml.safe_load(profiles_path.read_text(encoding="utf-8")) or {}
    profiles = data.get("profiles") or {}
    hard = profiles.get("hard") or {}
    backend = str(hard.get("backend") or "").strip().lower()
    model = str(hard.get("model") or "").strip()
    if backend == "ollama" and model:
        return f"ollama/{model}"

    for profile_name in ("balanced", "fast"):
        profile = profiles.get(profile_name) or {}
        if str(profile.get("backend") or "").strip().lower() == "ollama" and str(profile.get("model") or "").strip():
            return f"ollama/{str(profile.get('model')).strip()}"
    return "ollama/qwen2.5-coder:14b"


@dataclass
class AiderDispatchRecordV1:
    package_id: str
    allowed_files: List[str]
    validation_sequence: List[str]
    execution_mode: str
    dispatch_command: str
    dispatch_status: str
    dispatched_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    exit_code: Optional[int] = None
    stdout_preview: str = ""
    stderr_preview: str = ""
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "allowed_files": self.allowed_files,
            "validation_sequence": self.validation_sequence,
            "execution_mode": self.execution_mode,
            "dispatch_command": self.dispatch_command,
            "dispatch_status": self.dispatch_status,
            "dispatched_at": self.dispatched_at,
            "exit_code": self.exit_code,
            "stdout_preview": self.stdout_preview,
            "stderr_preview": self.stderr_preview,
            "notes": self.notes,
        }


class LiveAiderDispatchV1:
    """Structured Aider dispatch surface; dry-run by default; live when explicitly enabled."""

    DEFAULT_VALIDATION_SEQUENCE = [
        "python3 -m pytest tests/ -x -q",
        "make check",
    ]

    def dispatch(
        self,
        package_id: str,
        allowed_files: List[str],
        message: str,
        validation_sequence: Optional[List[str]] = None,
        dry_run: bool = True,
        notes: Optional[List[str]] = None,
    ) -> AiderDispatchRecordV1:
        seq = validation_sequence if validation_sequence is not None else self.DEFAULT_VALIDATION_SEQUENCE

        if not allowed_files:
            return AiderDispatchRecordV1(
                package_id=package_id,
                allowed_files=allowed_files,
                validation_sequence=seq,
                execution_mode=EXECUTION_MODE_LOCAL_FIRST,
                dispatch_command="",
                dispatch_status=DISPATCH_STATUS_BLOCKED,
                notes=(notes or []) + ["no allowed_files specified"],
            )

        files_arg = " ".join(allowed_files)
        model_name = _resolve_local_model()
        cmd = (
            f"aider --model {model_name!r} --no-show-model-warnings --yes "
            f"--map-tokens 0 --message {message!r} {files_arg}"
        )

        if dry_run:
            return AiderDispatchRecordV1(
                package_id=package_id,
                allowed_files=allowed_files,
                validation_sequence=seq,
                execution_mode=EXECUTION_MODE_LOCAL_FIRST,
                dispatch_command=cmd,
                dispatch_status=DISPATCH_STATUS_DRY_RUN,
                exit_code=None,
                notes=(notes or []) + ["dry_run=True; no subprocess executed"],
            )

        # Live dispatch — bounded subprocess; aider may or may not be installed
        try:
            result = subprocess.run(
                [
                    "aider",
                    "--model",
                    model_name,
                    "--no-show-model-warnings",
                    "--yes",
                    "--map-tokens",
                    "0",
                    "--message",
                    message,
                ] + allowed_files,
                capture_output=True,
                text=True,
                timeout=300,
                env={
                    **os.environ,
                    "OLLAMA_API_BASE": os.environ.get("OLLAMA_API_BASE", "http://127.0.0.1:11434"),
                },
            )
            status = DISPATCH_STATUS_COMPLETED if result.returncode == 0 else DISPATCH_STATUS_FAILED
            return AiderDispatchRecordV1(
                package_id=package_id,
                allowed_files=allowed_files,
                validation_sequence=seq,
                execution_mode=EXECUTION_MODE_LOCAL_FIRST,
                dispatch_command=cmd,
                dispatch_status=status,
                exit_code=result.returncode,
                stdout_preview=result.stdout[:500],
                stderr_preview=result.stderr[:500],
                notes=notes or [],
            )
        except FileNotFoundError:
            return AiderDispatchRecordV1(
                package_id=package_id,
                allowed_files=allowed_files,
                validation_sequence=seq,
                execution_mode=EXECUTION_MODE_LOCAL_FIRST,
                dispatch_command=cmd,
                dispatch_status=DISPATCH_STATUS_BLOCKED,
                exit_code=None,
                notes=(notes or []) + ["aider not found on PATH; live dispatch unavailable"],
            )
        except subprocess.TimeoutExpired:
            return AiderDispatchRecordV1(
                package_id=package_id,
                allowed_files=allowed_files,
                validation_sequence=seq,
                execution_mode=EXECUTION_MODE_LOCAL_FIRST,
                dispatch_command=cmd,
                dispatch_status=DISPATCH_STATUS_FAILED,
                exit_code=None,
                notes=(notes or []) + ["dispatch timed out after 300s"],
            )
