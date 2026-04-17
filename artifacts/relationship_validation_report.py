from framework.schema_registry import SCHEMA_REGISTRY
from framework.contract_relationships import find_related_contracts, category_members_count, contracts_sharing_module_prefix
from framework.contract_grouping_helpers import group_by_category, group_by_module, group_by_semantic_prefix

def generate_relationship_validation_report():
    all_names = list(SCHEMA_REGISTRY.keys())
    category_counts = category_members_count()
    category_total = sum(category_counts.values())

    all_related_found = all(find_related_contracts(name)["category"] is not None for name in all_names)

    modules = group_by_module()
    module_total = sum(len(names) for names in modules.values())

    prefixes = group_by_semantic_prefix()
    prefix_total = sum(len(names) for names in prefixes.values())

    relationships_valid = (
        category_total == 99 and
        module_total == 99 and
        prefix_total == 99 and
        all_related_found
    )

    return {
        "total_contracts": len(SCHEMA_REGISTRY),
        "category_counts": category_counts,
        "module_count": len(modules),
        "semantic_prefix_groups": len(prefixes),
        "all_related_found": all_related_found,
        "category_coverage": category_total,
        "module_coverage": module_total,
        "prefix_coverage": prefix_total,
        "relationships_valid": relationships_valid,
    }
