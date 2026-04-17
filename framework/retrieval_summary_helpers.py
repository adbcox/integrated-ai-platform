from typing import Any

def summarize_retrieval_results(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    total_count = len(contracts)
    unique_names = len({c.get("name") for c in contracts if isinstance(c, dict) and c.get("name")})
    categories = set()
    for item in contracts:
        if isinstance(item, dict) and isinstance(item.get("metadata"), dict):
            cat = item["metadata"].get("category")
            if cat:
                categories.add(cat)
    return {
        "total_contracts": total_count,
        "unique_contracts": unique_names,
        "unique_categories": len(categories),
        "categories_found": sorted(list(categories))
    }

def compute_retrieval_statistics(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    if not contracts:
        return {"average_metadata_fields": 0, "min_name_length": 0, "max_name_length": 0, "total_name_chars": 0}
    valid_names = [c.get("name") for c in contracts if isinstance(c, dict) and isinstance(c.get("name"), str)]
    if not valid_names:
        return {"average_metadata_fields": 0, "min_name_length": 0, "max_name_length": 0, "total_name_chars": 0}
    name_lengths = [len(n) for n in valid_names]
    avg_meta_fields = sum(len(c.get("metadata", {})) for c in contracts if isinstance(c, dict) and isinstance(c.get("metadata"), dict)) / float(len(contracts))
    return {
        "average_metadata_fields": round(avg_meta_fields, 1),
        "min_name_length": min(name_lengths),
        "max_name_length": max(name_lengths),
        "total_name_chars": sum(name_lengths)
    }

def group_contracts_by_metadata_field(contracts: list[dict[str, Any]], field_name: str) -> dict[str, list[dict[str, Any]]]:
    groups = {}
    for item in contracts:
        if not isinstance(item, dict):
            continue
        meta = item.get("metadata")
        if not isinstance(meta, dict):
            continue
        key = meta.get(field_name, "unknown")
        key_str = str(key) if key else "unknown"
        if key_str not in groups:
            groups[key_str] = []
        groups[key_str].append(item)
    return {k: groups[k] for k in sorted(groups.keys())}

def get_contracts_by_name_prefix(contracts: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
    result = []
    for item in contracts:
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name.startswith(prefix):
                result.append(item)
    result.sort(key=lambda x: x.get("name", ""))
    return result
