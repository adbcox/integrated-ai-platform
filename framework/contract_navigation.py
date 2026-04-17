from typing import Any

def find_related_contracts_by_pattern(contracts: list[dict[str, Any]], contract_name: str) -> dict[str, list[dict[str, Any]]]:
    target = contract_name.lower()
    parent_candidates = []
    sibling_candidates = []
    child_candidates = []
    for item in contracts:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str) or name.lower() == target:
            continue
        lower_name = name.lower()
        if lower_name in target:
            parent_candidates.append(item)
        elif target in lower_name:
            child_candidates.append(item)
        else:
            common_prefix = ""
            for i, pair in enumerate(zip(target, lower_name)):
                c1, c2 = pair
                if c1 == c2:
                    common_prefix = target[:i + 1]
                else:
                    break
            if len(common_prefix) > 4:
                sibling_candidates.append(item)
    parent_candidates.sort(key=lambda x: x.get("name", ""))
    sibling_candidates.sort(key=lambda x: x.get("name", ""))
    child_candidates.sort(key=lambda x: x.get("name", ""))
    return {
        "parents": parent_candidates,
        "siblings": sibling_candidates,
        "children": child_candidates
    }

def get_contract_lineage(contracts: list[dict[str, Any]], contract_name: str) -> dict[str, Any]:
    contract_item = None
    for item in contracts:
        if isinstance(item, dict) and item.get("name") == contract_name:
            contract_item = item
            break
    if not contract_item:
        return {"name": contract_name, "found": False}
    related = find_related_contracts_by_pattern(contracts, contract_name)
    return {
        "name": contract_name,
        "found": True,
        "metadata": contract_item.get("metadata", {}),
        "parent_count": len(related["parents"]),
        "sibling_count": len(related["siblings"]),
        "child_count": len(related["children"])
    }

def browse_contracts_hierarchically(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    root_level = []
    nested_under = {}
    for item in contracts:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name:
            continue
        branch = name
        for i in range(1, len(name)):
            if name[i].isupper():
                branch = name[:i]
                break
        if branch == name:
            root_level.append(name)
        else:
            if branch not in nested_under:
                nested_under[branch] = []
            nested_under[branch].append(name)
    return {
        "root_level_count": len(root_level),
        "root_names": sorted(root_level)[:10],
        "hierarchy_branches": len(nested_under),
        "branch_prefixes": sorted(list(nested_under.keys()))
    }
