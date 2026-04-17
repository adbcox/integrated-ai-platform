from typing import Any


def record_completion(
    existing_ledger: dict[str, Any], operation_id: str, completion_result: dict[str, Any]
) -> dict[str, Any]:
    if (
        not isinstance(existing_ledger, dict)
        or not isinstance(operation_id, str)
        or not operation_id
        or not isinstance(completion_result, dict)
    ):
        return {
            "ledger_valid": False,
            "operation_count": 0,
            "operations": {},
            "complete_count": 0,
            "ledger_status": "invalid_input",
        }

    prior_ops = existing_ledger.get("operations", {})
    if not isinstance(prior_ops, dict):
        prior_ops = {}

    terminal_values = {"complete", "signed_off", "closed", "archived", "intact", "approved"}
    status_value = "unknown"
    for key in completion_result.keys():
        if key.endswith("_status"):
            status_value = completion_result.get(key, "unknown")
            break

    complete = status_value in terminal_values
    operations = dict(prior_ops)
    ledger_status = "updated" if operation_id in operations else "recorded"
    operations[operation_id] = {"complete": complete, "status_value": status_value}
    complete_count = len(
        [name for name, entry in operations.items() if isinstance(entry, dict) and entry.get("complete") is True]
    )

    return {
        "ledger_valid": True,
        "operation_count": len(operations),
        "operations": operations,
        "complete_count": complete_count,
        "ledger_status": ledger_status,
    }


def summarize_completion_ledger(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("ledger_valid") is not True:
        return {
            "summary_valid": False,
            "ledger_status": "invalid_input",
            "operation_count": 0,
            "complete_count": 0,
        }

    return {
        "summary_valid": True,
        "ledger_status": result.get("ledger_status", "invalid_input"),
        "operation_count": int(result.get("operation_count", 0)),
        "complete_count": int(result.get("complete_count", 0)),
    }
