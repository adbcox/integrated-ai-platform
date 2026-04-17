from typing import Any


def write_closure_packet(
    final_report_result: dict[str, Any],
    handoff_result: dict[str, Any],
    sign_off_aggregation_result: dict[str, Any],
    boundary_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(final_report_result, dict)
        or not isinstance(handoff_result, dict)
        or not isinstance(sign_off_aggregation_result, dict)
        or not isinstance(boundary_result, dict)
    ):
        return {
            "packet_valid": False,
            "report_included": False,
            "handoff_included": False,
            "sign_off_included": False,
            "boundary_included": False,
            "packet_complete": False,
            "missing_components": [],
            "packet_status": "invalid_input",
        }

    report_included = final_report_result.get("report_valid") is True
    handoff_included = handoff_result.get("handoff_valid") is True
    sign_off_included = sign_off_aggregation_result.get("aggregation_valid") is True
    boundary_included = boundary_result.get("boundary_valid") is True

    missing = []
    if not report_included:
        missing.append("report")
    if not handoff_included:
        missing.append("handoff")
    if not sign_off_included:
        missing.append("sign_off")
    if not boundary_included:
        missing.append("boundary")

    packet_complete = len(missing) == 0

    if packet_complete:
        status = "complete"
    elif len(missing) <= 2:
        status = "partial"
    else:
        status = "incomplete"

    return {
        "packet_valid": True,
        "report_included": report_included,
        "handoff_included": handoff_included,
        "sign_off_included": sign_off_included,
        "boundary_included": boundary_included,
        "packet_complete": packet_complete,
        "missing_components": missing,
        "packet_status": status,
    }


def summarize_closure_packet(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("packet_valid") is not True:
        return {
            "summary_valid": False,
            "packet_status": "invalid_input",
            "packet_complete": False,
            "missing_count": 0,
        }

    return {
        "summary_valid": True,
        "packet_status": result.get("packet_status", "invalid_input"),
        "packet_complete": bool(result.get("packet_complete", False)),
        "missing_count": (
            len(result.get("missing_components", []))
            if isinstance(result.get("missing_components", []), list)
            else 0
        ),
    }
