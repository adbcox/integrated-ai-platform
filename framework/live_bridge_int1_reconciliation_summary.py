from typing import Any

def build_reconciliation_summary(contract: Any, registry: Any, purity: Any, harness: Any) -> dict[str, Any]:
    if not isinstance(contract, dict) or not isinstance(registry, dict) or not isinstance(purity, dict) or not isinstance(harness, dict):
        return {"reconciliation_status": "invalid_input"}
    c_ok = contract.get("contract_status") == "built"
    r_ok = registry.get("registry_status") == "built"
    p_ok = purity.get("purity_status") == "passed"
    h_ok = harness.get("harness_status") == "passed"
    if c_ok and r_ok and p_ok and h_ok:
        return {
            "reconciliation_status": "reconciled",
            "contract_pair_count": contract.get("contract_pair_count", 0),
            "seal_token_count": registry.get("seal_token_count", 0),
            "harness_chain_length": harness.get("success_chain_length", 0),
        }
    return {
        "reconciliation_status": "incomplete_source",
        "contract_pair_count": contract.get("contract_pair_count", 0),
        "seal_token_count": registry.get("seal_token_count", 0),
        "harness_chain_length": harness.get("success_chain_length", 0),
    }

