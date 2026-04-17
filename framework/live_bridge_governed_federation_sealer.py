from typing import Any

def seal_governed_federation(completion: dict, fed_gov_rollup: dict, sealer_config: dict) -> dict:
    if not isinstance(completion, dict) or not isinstance(fed_gov_rollup, dict) or not isinstance(sealer_config, dict):
        return {"governed_fed_seal_status": "invalid_input"}
    fc_ok = completion.get("governed_fed_completion_report_status") == "complete"
    fr_ok = fed_gov_rollup.get("fed_gov_rollup_status") == "rolled_up"
    if not fc_ok:
        return {"governed_fed_seal_status": "not_complete"}
    if not fr_ok:
        return {"governed_fed_seal_status": "no_rollup"}
    return {
        "governed_fed_seal_status": "sealed",
        "sealed_governed_fed_env_id": completion.get("report_phase"),
        "governed_fed_seal_id": sealer_config.get("seal_id", "gfseal-0001"),
    }
