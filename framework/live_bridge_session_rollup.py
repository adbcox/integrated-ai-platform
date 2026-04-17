from typing import Any
def rollup_sessions(session: dict[str, Any], session_validation: dict[str, Any], bridge_reporter: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(session, dict) or not isinstance(session_validation, dict) or not isinstance(bridge_reporter, dict):
        return {"session_rollup_status": "invalid_input", "rollup_session_id": None, "operations_complete": 0}
    all_complete = session.get("session_status") == "opened" and session_validation.get("session_validation_status") == "valid" and bridge_reporter.get("bridge_report_status") == "complete"
    if all_complete:
        return {"session_rollup_status": "rolled_up", "rollup_session_id": session.get("session_id"), "operations_complete": 3}
    return {"session_rollup_status": "incomplete_source", "rollup_session_id": None, "operations_complete": 0}
