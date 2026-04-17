from framework.schema_registry import SCHEMA_REGISTRY
from framework.registry_index import build_registry_index, contracts_per_module
from framework.runtime_contract_catalog_factory import build_runtime_contract_catalog

def analyze_coverage():
    catalog = build_runtime_contract_catalog()
    registry_size = len(SCHEMA_REGISTRY)
    category_distribution = {
        "session_contracts": len(catalog.session_contracts),
        "execution_contracts": len(catalog.execution_contracts),
        "validation_contracts": len(catalog.validation_contracts),
        "artifact_contracts": len(catalog.artifact_contracts),
        "routing_contracts": len(catalog.routing_contracts),
    }
    module_counts = contracts_per_module()
    module_distribution = {module: count for module, count in sorted(module_counts.items())}
    prefix_names = {}
    for class_name in SCHEMA_REGISTRY.keys():
        prefix = class_name[0] if class_name else ''
        if prefix not in prefix_names:
            prefix_names[prefix] = 0
        prefix_names[prefix] += 1
    prefix_distribution = {prefix: count for prefix, count in sorted(prefix_names.items())}
    return {
        "total_contracts": registry_size,
        "category_distribution": category_distribution,
        "module_distribution": module_distribution,
        "prefix_distribution": prefix_distribution,
    }

def get_module_coverage():
    index = build_registry_index()
    return {module: sorted(names) for module, names in sorted(index["by_module"].items())}
