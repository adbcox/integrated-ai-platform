from typing import Any

def summarize_aggregation_results(field_values: dict[str, Any]) -> dict[str, Any]:
    total_fields = len(field_values)
    total_values = sum(len(v) if isinstance(v, dict) else 0 for v in field_values.values())
    return {
        "total_fields_analyzed": total_fields,
        "total_distinct_values": total_values,
        "average_values_per_field": round(total_values / float(total_fields), 1) if total_fields > 0 else 0
    }

def compute_completeness_score(metadata_coverage: dict[str, Any]) -> float:
    total = metadata_coverage.get("total_contracts", 0)
    with_metadata = metadata_coverage.get("contracts_with_metadata", 0)
    if total == 0:
        return 0.0
    return round(with_metadata / float(total) * 100, 1)

def get_aggregation_distribution_summary(field_stats: dict[str, Any]) -> dict[str, Any]:
    if not field_stats:
        return {"fields_counted": 0, "min_field_count": 0, "max_field_count": 0, "average_field_coverage": 0}
    counts = [stat.get("contracts_with_field", 0) for stat in field_stats.values() if isinstance(stat, dict)]
    if not counts:
        return {"fields_counted": 0, "min_field_count": 0, "max_field_count": 0, "average_field_coverage": 0}
    return {
        "fields_counted": len(counts),
        "min_field_count": min(counts),
        "max_field_count": max(counts),
        "average_field_coverage": round(sum(counts) / float(len(counts)), 1)
    }

def identify_aggregation_gaps(field_stats: dict[str, Any], total_contracts: int) -> list[str]:
    gaps = []
    for field, stat in field_stats.items():
        if not isinstance(stat, dict):
            continue
        count = stat.get("contracts_with_field", 0)
        if count < total_contracts:
            gaps.append(field)
    return sorted(gaps)
