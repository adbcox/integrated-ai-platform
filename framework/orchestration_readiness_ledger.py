from typing import Any


def update_readiness_ledger(
    existing_ledger: dict[str, Any], layer_name: str, readiness_check: dict[str, Any]
) -> dict[str, Any]:
    if (
        not isinstance(existing_ledger, dict)
        or not isinstance(layer_name, str)
        or not layer_name
        or not isinstance(readiness_check, dict)
    ):
        return {
            "ledger_valid": False,
            "entry_count": 0,
            "entries": {},
            "ready_count": 0,
            "ledger_status": "invalid_input",
        }

    prior_entries = existing_ledger.get("entries", {})
    if not isinstance(prior_entries, dict):
        prior_entries = {}

    ready = False
    check_keys = []
    for key in readiness_check.keys():
        if key.endswith("_ready"):
            check_keys.append(key)

    if len(check_keys) == 0:
        for key in readiness_check.keys():
            if key.endswith("_valid"):
                check_keys.append(key)

    for key in check_keys:
        if readiness_check.get(key) is True:
            ready = True
            break

    entries = dict(prior_entries)
    status = "updated" if layer_name in entries else "added"
    entries[layer_name] = {"ready": ready, "check_keys": check_keys}
    ready_count = len(
        [name for name, entry in entries.items() if isinstance(entry, dict) and entry.get("ready") is True]
    )

    return {
        "ledger_valid": True,
        "entry_count": len(entries),
        "entries": entries,
        "ready_count": ready_count,
        "ledger_status": status,
    }


def summarize_readiness_ledger(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("ledger_valid") is not True:
        return {
            "summary_valid": False,
            "ledger_status": "invalid_input",
            "entry_count": 0,
            "ready_count": 0,
        }

    return {
        "summary_valid": True,
        "ledger_status": result.get("ledger_status", "invalid_input"),
        "entry_count": int(result.get("entry_count", 0)),
        "ready_count": int(result.get("ready_count", 0)),
    }
