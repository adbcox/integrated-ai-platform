from framework.schema_registry import SCHEMA_REGISTRY
from framework.contract_lookup import get_contract_by_name, list_contracts_in_category, all_contracts, contract_exists
from framework.contract_category_accessor import get_category_contracts, get_all_categories

def generate_contract_query_validation_report() -> dict[str, object]:
    all_by_lookup = all_contracts()
    all_by_registry = {k: SCHEMA_REGISTRY[k] for k in sorted(SCHEMA_REGISTRY.keys())}
    lookup_matches_registry = all_by_lookup == all_by_registry

    all_cats = get_all_categories()
    all_names_in_categories = set()
    for names in all_cats.values():
        all_names_in_categories.update(names)

    registry_names = set(SCHEMA_REGISTRY.keys())
    uncategorized = sorted(registry_names - all_names_in_categories)

    all_registry_accessible = all(contract_exists(name) for name in SCHEMA_REGISTRY.keys())
    all_registry_queryable = all(get_contract_by_name(name) is not None for name in SCHEMA_REGISTRY.keys())

    category_counts = {
        "session_contracts": len(all_cats["session_contracts"]),
        "execution_contracts": len(all_cats["execution_contracts"]),
        "validation_contracts": len(all_cats["validation_contracts"]),
        "artifact_contracts": len(all_cats["artifact_contracts"]),
        "routing_contracts": len(all_cats["routing_contracts"]),
    }

    total_categorized = sum(category_counts.values())

    query_validation_passed = (
        lookup_matches_registry and
        not uncategorized and
        all_registry_accessible and
        all_registry_queryable and
        total_categorized == len(SCHEMA_REGISTRY)
    )

    return {
        "total_registry_entries": len(SCHEMA_REGISTRY),
        "total_categorized_entries": total_categorized,
        "uncategorized_entries": uncategorized,
        "lookup_matches_registry": lookup_matches_registry,
        "all_registry_accessible": all_registry_accessible,
        "all_registry_queryable": all_registry_queryable,
        "category_counts": category_counts,
        "query_validation_passed": query_validation_passed,
    }
