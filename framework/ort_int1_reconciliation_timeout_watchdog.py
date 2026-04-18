from typing import Any

def reconciliation_timeout_watchdog(input_dict):
    if not isinstance(input_dict, dict):
        return {"reconciliation_timeout_watchdog_status": "invalid_input"}
    return {"reconciliation_timeout_watchdog_status": "valid"}
