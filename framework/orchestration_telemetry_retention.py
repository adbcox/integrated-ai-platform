from typing import Any


def manage_telemetry_retention(
    aggregation_result: dict[str, Any], retention_policy: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(aggregation_result, dict) or not isinstance(
        retention_policy, dict
    ):
        return {
            "retention_valid": False,
            "input_record_count": 0,
            "retained_record_count": 0,
            "dropped_record_count": 0,
            "retained_by_dimension": {},
            "retention_status": "invalid_input",
        }

    records_by_dimension = aggregation_result.get("records_by_dimension", {})
    if not isinstance(records_by_dimension, dict):
        records_by_dimension = {}

    limit = int(retention_policy.get("max_records_per_dimension", 0))
    input_record_count = int(aggregation_result.get("total_record_count", 0))
    retained_by_dimension = {}
    retained_record_count = 0

    for dimension, records in records_by_dimension.items():
        if not isinstance(records, list):
            records = []
        kept = records[: max(0, limit)] if limit > 0 else []
        retained_by_dimension[dimension] = len(kept)
        retained_record_count += len(kept)

    dropped_record_count = max(0, input_record_count - retained_record_count)

    if retained_record_count == 0:
        status = "empty"
    elif dropped_record_count > 0:
        status = "trimmed"
    else:
        status = "retained"

    return {
        "retention_valid": True,
        "input_record_count": input_record_count,
        "retained_record_count": retained_record_count,
        "dropped_record_count": dropped_record_count,
        "retained_by_dimension": retained_by_dimension,
        "retention_status": status,
    }


def summarize_retention(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("retention_valid") is not True:
        return {
            "summary_valid": False,
            "retention_status": "invalid_input",
            "retained_record_count": 0,
            "dropped_record_count": 0,
        }

    return {
        "summary_valid": True,
        "retention_status": result.get("retention_status", "invalid_input"),
        "retained_record_count": int(result.get("retained_record_count", 0)),
        "dropped_record_count": int(result.get("dropped_record_count", 0)),
    }
