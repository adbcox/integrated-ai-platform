from framework.schema_registry import SCHEMA_REGISTRY
from framework.registry_index import build_registry_index, find_contracts_by_module, find_contracts_by_prefix
from framework.contract_coverage_analyzer import analyze_coverage, get_module_coverage

def generate_registry_index_validation_report():
    index = build_registry_index()
    coverage = analyze_coverage()
    module_coverage = get_module_coverage()

    all_indexed_names = set()
    for names in index["by_module"].values():
        all_indexed_names.update(names)
    for names in index["by_prefix"].values():
        all_indexed_names.update(names)

    registry_names = set(SCHEMA_REGISTRY.keys())
    missing_from_index = sorted(registry_names - all_indexed_names)

    index_module_count = len(index["by_module"])
    prefix_count = len(index["by_prefix"])

    category_total = sum(coverage["category_distribution"].values())
    module_total = sum(coverage["module_distribution"].values())

    all_modules_accessible = all(
        find_contracts_by_module(module) == module_coverage[module]
        for module in index["by_module"].keys()
    )

    all_prefixes_accessible = all(
        len(find_contracts_by_prefix(prefix)) > 0
        for prefix in index["by_prefix"].keys()
    )

    index_validation_passed = (
        not missing_from_index and
        len(all_indexed_names) == len(registry_names) and
        category_total == len(registry_names) and
        module_total == len(registry_names) and
        all_modules_accessible and
        all_prefixes_accessible
    )

    return {
        "total_registry_entries": len(registry_names),
        "indexed_entries": len(all_indexed_names),
        "missing_from_index": missing_from_index,
        "module_count": index_module_count,
        "prefix_count": prefix_count,
        "category_distribution": coverage["category_distribution"],
        "category_total": category_total,
        "module_total": module_total,
        "all_modules_accessible": all_modules_accessible,
        "all_prefixes_accessible": all_prefixes_accessible,
        "index_validation_passed": index_validation_passed,
    }
