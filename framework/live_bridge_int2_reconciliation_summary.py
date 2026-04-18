from typing import Any

def build_reconciliation_summary(contract, registry, purity, harness):
    if not isinstance(contract, dict) or not isinstance(registry, dict) or not isinstance(purity, dict) or not isinstance(harness, dict):
        return {"reconciliation_status": "invalid_input"}
    contract_ok = contract.get("shape_contract_manifest_status") == "published"
    registry_ok = registry.get("seal_token_registry_status") == "published"
    purity_ok = purity.get("family_purity_audit_status") == "clean"
    harness_ok = harness.get("harness_status") == "passed"
    if contract_ok and registry_ok and purity_ok and harness_ok:
        return {
            "reconciliation_status": "sealed",
            "contract_pair_count": contract.get("contract_pair_count", 0),
            "seal_token_count": registry.get("seal_count", 0),
            "harness_chain_length": harness.get("success_chain_length", 0),
        }
    return {
        "reconciliation_status": "incomplete",
        "contract_pair_count": contract.get("contract_pair_count", 0),
        "seal_token_count": registry.get("seal_count", 0),
        "harness_chain_length": harness.get("success_chain_length", 0),
    }
