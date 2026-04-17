from typing import Any

def audit_layer_presence() -> dict[str, bool]:
    layers_to_check = [
        ("schema_registry", "framework.schema_registry", "SCHEMA_REGISTRY"),
        ("runtime_catalog", "framework.runtime_contract_catalog", "RuntimeContractCatalog"),
        ("contract_loader", "framework.contract_loader", "ContractLoader"),
        ("retrieval_helpers", "framework.contract_retrieval_helpers", "get_all_contracts_with_metadata"),
        ("navigation", "framework.contract_navigation", "find_related_contracts_by_pattern"),
        ("aggregation", "framework.metadata_aggregation", "aggregate_metadata_by_field"),
    ]
    results = {}
    for layer_name, module_path, symbol in layers_to_check:
        try:
            mod = __import__(module_path, fromlist=[symbol])
            getattr(mod, symbol)
            results[layer_name] = True
        except Exception:
            results[layer_name] = False
    return results

def compute_foundation_completeness() -> dict[str, Any]:
    layers = audit_layer_presence()
    present = sum(1 for v in layers.values() if v)
    total = len(layers)
    completeness = round(present / float(total) * 100, 1) if total > 0 else 0
    return {
        "total_layers_required": total,
        "layers_present": present,
        "completeness_percent": completeness,
        "all_layers_present": present == total
    }

def validate_runtime_foundation() -> dict[str, Any]:
    try:
        completeness = compute_foundation_completeness()
        layers = audit_layer_presence()
        all_operational = all(layers.values())
        return {
            "foundation_valid": completeness.get("all_layers_present", False),
            "foundation_operational": all_operational,
            "completeness_percent": completeness.get("completeness_percent", 0),
            "layer_status": layers
        }
    except Exception as e:
        return {
            "foundation_valid": False,
            "foundation_operational": False,
            "error": str(e)
        }
