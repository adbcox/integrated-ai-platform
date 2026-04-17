from typing import Any

def filter_contracts_by_module(contracts: list[dict[str, Any]], module_name: str) -> list[dict[str, Any]]:
    filtered = []
    for item in contracts:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        metadata = item.get("metadata")
        if not isinstance(name, str):
            continue
        if isinstance(metadata, dict) and metadata.get("module") == module_name:
            filtered.append(item)
    return filtered

def filter_contracts_by_pattern(contracts: list[dict[str, Any]], pattern: str) -> list[dict[str, Any]]:
    filtered = []
    lower_pattern = pattern.lower()
    for item in contracts:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if isinstance(name, str) and lower_pattern in name.lower():
            filtered.append(item)
    return filtered

def search_contracts_by_name_substring(all_contracts: list[dict[str, Any]], substring: str) -> list[dict[str, Any]]:
    results = []
    lower_sub = substring.lower()
    for item in all_contracts:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if isinstance(name, str) and lower_sub in name.lower():
            results.append(item)
    return results

def rank_contracts_by_relevance(contracts: list[dict[str, Any]], query: str) -> list[tuple[dict[str, Any], int]]:
    scored = []
    lower_query = query.lower()
    for item in contracts:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str):
            continue
        lower_name = name.lower()
        if lower_name == lower_query:
            score = 100
        elif lower_query in lower_name:
            score = 50
        else:
            score = 0
        if score > 0:
            scored.append((item, score))
    scored.sort(key=lambda x: (-x[1], x[0].get("name", "")))
    return scored

def get_contracts_by_name_length(all_contracts: list[dict[str, Any]], min_len: int, max_len: int) -> list[dict[str, Any]]:
    filtered = []
    for item in all_contracts:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if isinstance(name, str) and min_len <= len(name) <= max_len:
            filtered.append(item)
    return filtered
