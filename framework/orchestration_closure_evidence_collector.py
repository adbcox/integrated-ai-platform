from typing import Any


def collect_closure_evidence(
    packet_result: dict[str, Any],
    readiness_ledger: dict[str, Any],
    completion_ledger: dict[str, Any],
    audit_trail: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(packet_result, dict)
        or not isinstance(readiness_ledger, dict)
        or not isinstance(completion_ledger, dict)
        or not isinstance(audit_trail, dict)
    ):
        return {
            "collection_valid": False,
            "packet_complete": False,
            "readiness_entry_count": 0,
            "readiness_ready_count": 0,
            "operation_count": 0,
            "complete_op_count": 0,
            "trail_event_count": 0,
            "evidence_complete": False,
            "collection_status": "invalid_input",
        }

    packet_complete = packet_result.get("packet_complete", False) is True
    readiness_entry_count = int(readiness_ledger.get("entry_count", 0))
    readiness_ready_count = int(readiness_ledger.get("ready_count", 0))
    operation_count = int(completion_ledger.get("operation_count", 0))
    complete_op_count = int(completion_ledger.get("complete_count", 0))
    trail_event_count = int(audit_trail.get("event_count", 0))

    evidence_complete = (
        packet_complete and readiness_ready_count > 0 and complete_op_count > 0
    )

    return {
        "collection_valid": True,
        "packet_complete": packet_complete,
        "readiness_entry_count": readiness_entry_count,
        "readiness_ready_count": readiness_ready_count,
        "operation_count": operation_count,
        "complete_op_count": complete_op_count,
        "trail_event_count": trail_event_count,
        "evidence_complete": evidence_complete,
        "collection_status": "complete" if evidence_complete else "partial",
    }


def summarize_evidence_collection(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("collection_valid") is not True:
        return {
            "summary_valid": False,
            "collection_status": "invalid_input",
            "evidence_complete": False,
            "complete_op_count": 0,
        }

    return {
        "summary_valid": True,
        "collection_status": result.get("collection_status", "invalid_input"),
        "evidence_complete": bool(result.get("evidence_complete", False)),
        "complete_op_count": int(result.get("complete_op_count", 0)),
    }
