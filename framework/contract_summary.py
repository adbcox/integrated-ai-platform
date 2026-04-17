from typing import Any

def summarize_contracts_by_category(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    summary = {}
    categories = manifest.get("categories", {})
    for cat, count in sorted(categories.items()):
        actual_count = count if isinstance(count, int) else 0
        summary[cat] = {
            "count": actual_count,
            "contracts": [],
        }
    return summary

def get_largest_categories(manifest: dict[str, Any], top_n: int = 5) -> list[tuple[str, int]]:
    categories = manifest.get("categories", {})
    category_counts = []
    for cat, value in categories.items():
        actual_count = value if isinstance(value, int) else 0
        category_counts.append((cat, actual_count))
    category_counts.sort(key=lambda x: (-x[1], x[0]))
    return category_counts[:top_n]

def generate_contract_distribution(manifest: dict[str, Any]) -> dict[str, Any]:
    categories = manifest.get("categories", {})
    total_contracts = sum(v for v in categories.values() if isinstance(v, int))
    distribution = {}
    for cat, value in sorted(categories.items()):
        count = value if isinstance(value, int) else 0
        pct = (count / total_contracts * 100) if total_contracts > 0 else 0
        distribution[cat] = {"count": count, "percentage": round(pct, 1)}
    return distribution
