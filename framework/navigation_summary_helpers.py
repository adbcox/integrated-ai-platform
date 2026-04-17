from typing import Any

def summarize_navigation_results(related: dict[str, Any]) -> dict[str, Any]:
    parents = related.get("parents", [])
    siblings = related.get("siblings", [])
    children = related.get("children", [])
    total_related = len(parents) + len(siblings) + len(children)
    return {
        "total_related": total_related,
        "parent_count": len(parents),
        "sibling_count": len(siblings),
        "child_count": len(children),
        "has_parent": len(parents) > 0,
        "has_siblings": len(siblings) > 0,
        "has_children": len(children) > 0
    }

def generate_lineage_report(lineages: list[dict[str, Any]]) -> dict[str, Any]:
    found_count = sum(1 for l in lineages if isinstance(l, dict) and l.get("found"))
    total_parents = sum(l.get("parent_count", 0) for l in lineages if isinstance(l, dict))
    total_siblings = sum(l.get("sibling_count", 0) for l in lineages if isinstance(l, dict))
    total_children = sum(l.get("child_count", 0) for l in lineages if isinstance(l, dict))
    average_related = 0
    if lineages:
        average_related = round((total_parents + total_siblings + total_children) / float(len(lineages)), 1)
    return {
        "total_lineages_checked": len(lineages),
        "found_contracts": found_count,
        "total_parent_relationships": total_parents,
        "total_sibling_relationships": total_siblings,
        "total_child_relationships": total_children,
        "average_related_per_contract": average_related
    }

def get_deepest_lineage(lineages: list[dict[str, Any]]) -> dict[str, Any]:
    if not lineages:
        return {"name": None, "depth": 0}
    max_depth = 0
    deepest = None
    for item in lineages:
        if not isinstance(item, dict) or not item.get("found"):
            continue
        depth = item.get("parent_count", 0) + item.get("child_count", 0)
        if depth > max_depth:
            max_depth = depth
            deepest = item
    if not deepest:
        return {"name": None, "depth": 0}
    return {
        "name": deepest.get("name"),
        "depth": max_depth,
        "parent_count": deepest.get("parent_count", 0),
        "child_count": deepest.get("child_count", 0)
    }

def find_orphan_contracts(contracts: list[dict[str, Any]], lineages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lineage_map = {}
    for item in lineages:
        if isinstance(item, dict) and item.get("found") and item.get("name"):
            lineage_map[item.get("name")] = item
    orphans = []
    for item in contracts:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str):
            continue
        lineage = lineage_map.get(name)
        if lineage and lineage.get("parent_count", 0) == 0 and lineage.get("sibling_count", 0) == 0 and lineage.get("child_count", 0) == 0:
            orphans.append(item)
    orphans.sort(key=lambda x: x.get("name", ""))
    return orphans
