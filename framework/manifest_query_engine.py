from typing import Any

def filter_manifest_by_category(manifest: dict[str, Any], category: str) -> dict[str, Any]:
    categories = manifest.get("categories", {})
    if category in categories:
        return {"category": category, "count": categories[category]}
    return {}

def filter_manifest_by_count_range(manifest: dict[str, Any], min_count: int, max_count: int) -> list[str]:
    categories = manifest.get("categories", {})
    matching = []
    for cat, count in categories.items():
        if isinstance(count, int) and min_count <= count <= max_count:
            matching.append(cat)
    return sorted(matching)

def search_manifest_contracts(manifest: dict[str, Any], prefix: str) -> list[str]:
    modules = manifest.get("modules_present", {})
    result = []
    for module_name in modules.keys():
        if isinstance(module_name, str) and module_name.startswith(prefix):
            result.append(module_name)
    return sorted(result)

def manifest_summary_stats(manifest: dict[str, Any]) -> dict[str, Any]:
    categories = manifest.get("categories", {})
    total = sum(v for v in categories.values() if isinstance(v, int))
    return {
        "total_contracts": total,
        "total_categories": len(categories),
        "categories_with_contracts": len([v for v in categories.values() if isinstance(v, int) and v > 0]),
    }
