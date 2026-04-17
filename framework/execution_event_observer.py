from typing import Any

def record_job_accepted_event(job_id: str, task_class: str, created_at: str) -> dict[str, Any]:
    try:
        from datetime import datetime as dt
        now = dt.utcnow().isoformat(timespec="seconds")
    except Exception:
        now = ""
    return {
        "event_id": "evt-{}-0".format(job_id),
        "job_id": job_id,
        "event_type": "accepted",
        "timestamp_utc": now,
        "lifecycle_state": "accepted",
        "task_class": task_class,
        "created_at_utc": created_at
    }

def record_job_lifecycle_transition(job_id: str, old_state: str, new_state: str, context_id: str = "") -> dict[str, Any]:
    try:
        from datetime import datetime as dt
        now = dt.utcnow().isoformat(timespec="seconds")
    except Exception:
        now = ""
    transition_map = {
        "queued": "queued",
        "dispatched": "dispatched",
        "running": "running",
        "completed": "completed",
        "failed": "failed",
        "retry_waiting": "retry_waiting"
    }
    event_type = transition_map.get(new_state, new_state)
    return {
        "event_id": "evt-{}-{}".format(job_id, new_state),
        "job_id": job_id,
        "event_type": event_type,
        "timestamp_utc": now,
        "old_state": old_state,
        "new_state": new_state,
        "lifecycle_state": new_state,
        "context_id": context_id
    }

def record_execution_attempt(job_id: str, attempt_number: int, executor_name: str, context_id: str = "") -> dict[str, Any]:
    try:
        from datetime import datetime as dt
        now = dt.utcnow().isoformat(timespec="seconds")
    except Exception:
        now = ""
    return {
        "event_id": "evt-{}-attempt-{}".format(job_id, attempt_number),
        "job_id": job_id,
        "event_type": "running",
        "timestamp_utc": now,
        "attempt_number": attempt_number,
        "executor_name": executor_name,
        "context_id": context_id
    }

def record_execution_completion(job_id: str, success: bool, exit_code: int, duration_sec: float) -> dict[str, Any]:
    try:
        from datetime import datetime as dt
        now = dt.utcnow().isoformat(timespec="seconds")
    except Exception:
        now = ""
    event_type = "completed" if success else "failed"
    return {
        "event_id": "evt-{}-{}".format(job_id, event_type),
        "job_id": job_id,
        "event_type": event_type,
        "timestamp_utc": now,
        "success": success,
        "exit_code": exit_code,
        "duration_sec": duration_sec
    }
