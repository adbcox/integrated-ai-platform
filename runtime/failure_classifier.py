"""
Failure classifier: classify execution failures and suggest recovery actions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union


def classify_failure(
    session_id: str,
    job_id: str,
    task_id: Optional[str],
    stage_failed: str,
    error_message: str,
    exit_code: Optional[int] = None,
    command_executed: Optional[List[str]] = None,
    retry_attempt: int = 0
) -> Dict[str, Any]:
    """
    Classify a failure and suggest recovery actions.

    Args:
        session_id: Session identifier
        job_id: Job identifier
        task_id: Optional task identifier
        stage_failed: Stage where failure occurred
        error_message: Error message
        exit_code: Optional exit code from command
        command_executed: Optional command that failed
        retry_attempt: Retry attempt number

    Returns:
        Normalized failure record
    """
    failure_type = "unknown_error"
    root_cause = "Unknown error"
    recovery_suggestions = []

    if "not allowed" in error_message.lower() or "whitelist" in error_message.lower():
        failure_type = "command_not_allowed"
        root_cause = "Command not in execution whitelist"
        recovery_suggestions = [
            {
                "action": "check_whitelist",
                "reason": "Command may need to be added to command whitelist"
            },
            {
                "action": "escalate_to_manual",
                "reason": "Command execution policy may need review"
            }
        ]
    elif stage_failed == "workspace_init" or "workspace" in error_message.lower():
        failure_type = "workspace_init_failed"
        root_cause = "Workspace initialization failed"
        recovery_suggestions = [
            {
                "action": "check_workspace_permissions",
                "reason": "Check workspace directory permissions and availability"
            },
            {
                "action": "retry_with_timeout_increase",
                "reason": "Workspace initialization may be timing-sensitive"
            }
        ]
    elif stage_failed == "profile_selection" or "profile" in error_message.lower():
        failure_type = "profile_selection_failed"
        root_cause = "Profile selection failed"
        recovery_suggestions = [
            {
                "action": "retry_with_profile_change",
                "reason": "Try different profile (fast/balanced/hard)"
            },
            {
                "action": "fallback_to_claude",
                "reason": "Escalate to Claude API if local models unavailable"
            }
        ]
    elif exit_code is not None and exit_code != 0:
        failure_type = "command_failed"
        root_cause = f"Command exited with code {exit_code}"
        recovery_suggestions = [
            {
                "action": "retry_with_timeout_increase",
                "reason": "Command may need more time to complete"
            },
            {
                "action": "check_whitelist",
                "reason": "Verify command is properly whitelisted"
            }
        ]
    elif "timed out" in error_message.lower() or "timeout" in error_message.lower():
        failure_type = "command_timeout"
        root_cause = "Command execution timed out"
        recovery_suggestions = [
            {
                "action": "retry_with_timeout_increase",
                "reason": "Command needs more time; increase timeout budget"
            },
            {
                "action": "retry_with_profile_change",
                "reason": "Try slower profile (balanced/hard) with higher timeout"
            }
        ]
    elif "artifact" in error_message.lower():
        failure_type = "artifact_emission_failed"
        root_cause = "Artifact emission failed"
        recovery_suggestions = [
            {
                "action": "check_workspace_permissions",
                "reason": "Verify artifact directory is writable"
            },
            {
                "action": "escalate_to_manual",
                "reason": "Manual investigation needed for artifact system"
            }
        ]
    elif stage_failed == "gateway" or "gateway" in error_message.lower():
        failure_type = "gateway_error"
        root_cause = "Inference gateway error"
        recovery_suggestions = [
            {
                "action": "fallback_to_claude",
                "reason": "Local model unavailable; fallback to Claude API"
            },
            {
                "action": "retry_with_profile_change",
                "reason": "Try different profile with different backend"
            }
        ]

    record = {
        "schema_version": "1.0",
        "record_kind": "failure_record",
        "session_id": session_id,
        "job_id": job_id,
        "task_id": task_id,
        "failure_type": failure_type,
        "root_cause": root_cause,
        "failure_description": error_message,
        "stage_failed": stage_failed,
        "command_executed": command_executed,
        "exit_code": exit_code,
        "error_message": error_message,
        "recovery_suggestions": recovery_suggestions,
        "retry_attempt": retry_attempt,
        "timestamp": datetime.utcnow().isoformat()
    }

    return record


def emit_failure_record(
    record: Dict[str, Any],
    output_path: Union[str, Path]
) -> Dict[str, Any]:
    """
    Write failure record to JSON file.

    Args:
        record: Failure record dict
        output_path: Path to write JSON failure record

    Returns:
        Result dict with path, size_bytes, timestamp, status
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(record, f, indent=2, default=str)

    file_size = output_path.stat().st_size
    now = datetime.utcnow().isoformat()

    result = {
        "output_path": str(output_path),
        "size_bytes": file_size,
        "emission_timestamp": now,
        "status": "success"
    }

    return result
