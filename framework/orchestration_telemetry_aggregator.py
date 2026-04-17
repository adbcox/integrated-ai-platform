from typing import Any


def aggregate_telemetry(emit_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(emit_results, list):
        return {
            "aggregation_valid": False,
            "total_emit_count": 0,
            "valid_emit_count": 0,
            "total_record_count": 0,
            "records_by_dimension": {},
            "failed_emit_count": 0,
            "aggregation_status": "invalid_input",
        }

    if len(emit_results) == 0:
        return {
            "aggregation_valid": True,
            "total_emit_count": 0,
            "valid_emit_count": 0,
            "total_record_count": 0,
            "records_by_dimension": {},
            "failed_emit_count": 0,
            "aggregation_status": "empty",
        }

    records_by_dimension = {}
    valid_emit_count = 0
    failed_emit_count = 0
    total_record_count = 0

    for emit_result in emit_results:
        if isinstance(emit_result, dict) and emit_result.get("emit_valid") is True:
            valid_emit_count += 1
            records = emit_result.get("records", [])
            if not isinstance(records, list):
                records = []
            total_record_count += int(emit_result.get("record_count", 0))

            for record in records:
                if not isinstance(record, dict):
                    continue
                dimension = record.get("dimension", "unknown")
                if dimension not in records_by_dimension:
                    records_by_dimension[dimension] = []
                records_by_dimension[dimension].append(record)
        else:
            failed_emit_count += 1

    total_emit_count = len(emit_results)

    if valid_emit_count == 0:
        status = "empty"
    elif valid_emit_count == total_emit_count:
        status = "aggregated"
    else:
        status = "partial"

    return {
        "aggregation_valid": True,
        "total_emit_count": total_emit_count,
        "valid_emit_count": valid_emit_count,
        "total_record_count": total_record_count,
        "records_by_dimension": records_by_dimension,
        "failed_emit_count": failed_emit_count,
        "aggregation_status": status,
    }


def summarize_telemetry_aggregation(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("aggregation_valid") is not True:
        return {
            "summary_valid": False,
            "aggregation_status": "invalid_input",
            "total_record_count": 0,
            "failed_emit_count": 0,
        }

    return {
        "summary_valid": True,
        "aggregation_status": result.get("aggregation_status", "invalid_input"),
        "total_record_count": int(result.get("total_record_count", 0)),
        "failed_emit_count": int(result.get("failed_emit_count", 0)),
    }
