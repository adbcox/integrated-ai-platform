from typing import Any


def detect_telemetry_gaps(
    aggregation_result: dict[str, Any], required_dimensions: list[str]
) -> dict[str, Any]:
    if not isinstance(aggregation_result, dict) or not isinstance(
        required_dimensions, list
    ):
        return {
            "detection_valid": False,
            "required_count": 0,
            "present_count": 0,
            "missing_dimensions": [],
            "empty_dimensions": [],
            "gap_count": 0,
            "gap_status": "invalid_input",
        }

    if len(required_dimensions) == 0:
        return {
            "detection_valid": True,
            "required_count": 0,
            "present_count": 0,
            "missing_dimensions": [],
            "empty_dimensions": [],
            "gap_count": 0,
            "gap_status": "complete",
        }

    records_by_dim = aggregation_result.get("records_by_dimension", {})
    if not isinstance(records_by_dim, dict):
        records_by_dim = {}

    missing_dimensions = [d for d in required_dimensions if d not in records_by_dim]
    empty_dimensions = [
        d
        for d in required_dimensions
        if d in records_by_dim
        and isinstance(records_by_dim.get(d), list)
        and len(records_by_dim.get(d)) == 0
    ]

    gap_count = len(missing_dimensions) + len(empty_dimensions)

    if gap_count == 0:
        status = "complete"
    elif missing_dimensions == required_dimensions:
        status = "all_missing"
    else:
        status = "gaps_detected"

    return {
        "detection_valid": True,
        "required_count": len(required_dimensions),
        "present_count": len(required_dimensions) - len(missing_dimensions),
        "missing_dimensions": missing_dimensions,
        "empty_dimensions": empty_dimensions,
        "gap_count": gap_count,
        "gap_status": status,
    }


def summarize_gap_detection(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("detection_valid") is not True:
        return {
            "summary_valid": False,
            "gap_status": "invalid_input",
            "gap_count": 0,
            "missing_dimensions": [],
        }

    return {
        "summary_valid": True,
        "gap_status": result.get("gap_status", "invalid_input"),
        "gap_count": int(result.get("gap_count", 0)),
        "missing_dimensions": (
            result.get("missing_dimensions", [])
            if isinstance(result.get("missing_dimensions", []), list)
            else []
        ),
    }
