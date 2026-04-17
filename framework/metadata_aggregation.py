from typing import Any

def aggregate_metadata_by_field(contracts: list[dict[str, Any]], field_name: str) -> dict[str, Any]:
    aggregated = {}
    for item in contracts:
        if not isinstance(item, dict):
            continue
        meta = item.get("metadata")
        if not isinstance(meta, dict):
            continue
        value = meta.get(field_name)
        if value is None:
            continue
        key = str(value)
        if key not in aggregated:
            aggregated[key] = {"count": 0, "contracts": []}
        aggregated[key]["count"] += 1
        aggregated[key]["contracts"].append(item.get("name"))
    for key in aggregated:
        aggregated[key]["contracts"] = sorted([c for c in aggregated[key]["contracts"] if isinstance(c, str)])
    return {k: aggregated[k] for k in sorted(aggregated.keys())}

def generate_metadata_overview(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    all_fields = set()
    for item in contracts:
        if isinstance(item, dict) and isinstance(item.get("metadata"), dict):
            all_fields.update(item["metadata"].keys())
    field_stats = {}
    for field in sorted(all_fields):
        count = sum(1 for c in contracts if isinstance(c, dict) and isinstance(c.get("metadata"), dict) and field in c.get("metadata", {}))
        field_stats[field] = {"contracts_with_field": count}
    return {
        "total_contracts": len(contracts),
        "unique_metadata_fields": len(all_fields),
        "fields_present": sorted(list(all_fields)),
        "field_statistics": field_stats
    }

def compute_metadata_coverage(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(contracts)
    if total == 0:
        return {"total_contracts": 0, "contracts_with_metadata": 0, "coverage_percent": 0, "contracts_without_metadata": 0}
    with_metadata = sum(1 for c in contracts if isinstance(c, dict) and isinstance(c.get("metadata"), dict) and len(c["metadata"]) > 0)
    coverage = round(with_metadata / float(total) * 100, 1)
    return {
        "total_contracts": total,
        "contracts_with_metadata": with_metadata,
        "coverage_percent": coverage,
        "contracts_without_metadata": total - with_metadata
    }

def summarize_metadata_fields(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    field_value_counts = {}
    for item in contracts:
        if not isinstance(item, dict):
            continue
        meta = item.get("metadata")
        if not isinstance(meta, dict):
            continue
        for field, value in meta.items():
            if field not in field_value_counts:
                field_value_counts[field] = {}
            key = str(value)
            field_value_counts[field][key] = field_value_counts[field].get(key, 0) + 1
    return {field: field_value_counts[field] for field in sorted(field_value_counts.keys())}
