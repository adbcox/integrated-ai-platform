from framework.schema_registry import SCHEMA_REGISTRY
from framework.schema_path_resolver import get_schema_path_map
from framework.runtime_contract_catalog_factory import build_runtime_contract_catalog

def generate_runtime_contract_consistency_report() -> dict[str, object]:
    catalog = build_runtime_contract_catalog()
    path_map = get_schema_path_map()

    all_catalog_names = (
        catalog.session_contracts +
        catalog.execution_contracts +
        catalog.validation_contracts +
        catalog.artifact_contracts +
        catalog.routing_contracts
    )

    duplicate_counts = {}
    for name in all_catalog_names:
        duplicate_counts[name] = duplicate_counts.get(name, 0) + 1
    duplicates = sorted([name for name, count in duplicate_counts.items() if count > 1])

    uncategorized = sorted(set(SCHEMA_REGISTRY.keys()) - set(all_catalog_names))

    category_counts = {
        "session_contracts": len(catalog.session_contracts),
        "execution_contracts": len(catalog.execution_contracts),
        "validation_contracts": len(catalog.validation_contracts),
        "artifact_contracts": len(catalog.artifact_contracts),
        "routing_contracts": len(catalog.routing_contracts),
    }

    total_registry = len(SCHEMA_REGISTRY)
    total_catalog = len(all_catalog_names)

    consistency_passed = (
        path_map == SCHEMA_REGISTRY and
        not uncategorized and
        not duplicates and
        total_registry == total_catalog
    )

    return {
        "total_registry_entries": total_registry,
        "total_catalog_entries": total_catalog,
        "uncategorized_registry_keys": uncategorized,
        "duplicate_catalog_entries": duplicates,
        "category_counts": category_counts,
        "consistency_passed": consistency_passed,
    }
