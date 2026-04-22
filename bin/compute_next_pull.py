#!/usr/bin/env python3
"""
Compute autonomous next-pull candidates from canonical roadmap items.

This is the governed-loop selector for routine autonomous execution:
- source of truth: docs/roadmap/items/RM-*.yaml
- excludes archived and completed items
- excludes placeholder state conflicts
- enforces bounded execution shape via ai_operability contract
"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ITEMS_DIR = REPO_ROOT / "docs/roadmap/items"
GRAPH_OUTPUT_PATH = REPO_ROOT / "governance/roadmap_dependency_graph.v1.yaml"
NEXT_PULL_OUTPUT_PATH = REPO_ROOT / "artifacts/planning/next_pull.json"

TERMINAL_STATUSES = {"complete", "completed"}
PLANNABLE_STATUSES = {"proposed", "planned", "ready", "in_progress", "in_execution", "planned_for_execution"}
TERMINAL_EXECUTION = {"complete", "completed"}
TERMINAL_VALIDATION = {"complete", "completed", "passed"}
REQUIRED_AI_FIELDS = [
    "allowed_files",
    "forbidden_files",
    "validation_order",
    "rollback_rule",
    "artifact_outputs",
]
REQUIRED_GOVERNANCE_FIELDS = ["phase_target", "architectural_lane"]


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def load_items() -> dict[str, dict]:
    items: dict[str, dict] = {}
    for item_file in sorted(ITEMS_DIR.glob("RM-*.yaml")):
        try:
            with item_file.open("r", encoding="utf-8") as handle:
                item = yaml.safe_load(handle) or {}
        except Exception as exc:
            print(f"Warning: failed to parse {item_file}: {exc}", file=sys.stderr)
            continue
        item_id = item.get("id") or item_file.stem
        item["_source_path"] = str(item_file)
        items[item_id] = item
    return items


def dependency_ids(item: dict) -> list[str]:
    deps = item.get("dependencies") or {}
    depends_on = deps.get("depends_on") or deps.get("blocked_by") or []
    return [dep for dep in depends_on if isinstance(dep, str) and dep.strip()]


def missing_ai_fields(item: dict) -> list[str]:
    ai = item.get("ai_operability") or {}
    missing = []
    for field in REQUIRED_AI_FIELDS:
        value = ai.get(field)
        if value in (None, "", [], {}):
            missing.append(field)
    return missing


def placeholder_state_conflict(item: dict) -> bool:
    status = normalize(item.get("status"))
    execution_status = normalize((item.get("execution") or {}).get("execution_status"))
    validation_status = normalize((item.get("validation") or {}).get("validation_status"))
    return (
        status in PLANNABLE_STATUSES
        and execution_status in TERMINAL_EXECUTION
        and validation_status in TERMINAL_VALIDATION
    )


def classify_item(item_id: str, item: dict, items: dict[str, dict], dependent_count: int) -> dict:
    status = normalize(item.get("status"))
    archive_status = normalize(item.get("archive_status"))
    execution_status = normalize((item.get("execution") or {}).get("execution_status"))
    validation_status = normalize((item.get("validation") or {}).get("validation_status"))
    dependencies = dependency_ids(item)
    missing_ai = missing_ai_fields(item)
    governance = item.get("governance") or {}
    missing_governance = [field for field in REQUIRED_GOVERNANCE_FIELDS if not governance.get(field)]
    reasons: list[str] = []
    eligibility = "eligible"

    if archive_status in {"archived", "ready_for_archive"}:
        eligibility = "ineligible"
        reasons.append(f"archive_status={archive_status}")
    if status in TERMINAL_STATUSES:
        eligibility = "ineligible"
        reasons.append(f"terminal_status={status}")
    if status not in TERMINAL_STATUSES | PLANNABLE_STATUSES:
        eligibility = "ineligible"
        reasons.append(f"unsupported_status={status or 'unset'}")
    if placeholder_state_conflict(item):
        eligibility = "blocked_placeholder"
        reasons.append("status_plannable_but_execution_and_validation_terminal")
    if missing_ai:
        eligibility = "ineligible"
        reasons.append(f"missing_ai_operability={','.join(missing_ai)}")
    if missing_governance:
        eligibility = "ineligible"
        reasons.append(f"missing_governance={','.join(missing_governance)}")

    unsatisfied: list[str] = []
    for dep_id in dependencies:
        dep = items.get(dep_id)
        dep_status = normalize((dep or {}).get("status"))
        if not dep:
            unsatisfied.append(f"{dep_id}:missing")
        elif dep_status not in TERMINAL_STATUSES:
            unsatisfied.append(f"{dep_id}:{dep_status or 'unset'}")

    if unsatisfied:
        if eligibility == "eligible":
            eligibility = "blocked_dependency"
        reasons.append("unsatisfied_dependencies=" + ",".join(unsatisfied))

    priority_score = {"p0": 4, "p1": 3, "p2": 2, "p3": 1, "p4": 0}.get(
        normalize(item.get("priority")), 0
    )
    pull_score = priority_score + min(dependent_count, 4)

    return {
        "id": item_id,
        "title": item.get("title", ""),
        "category": item.get("category"),
        "priority": item.get("priority"),
        "status": item.get("status"),
        "archive_status": item.get("archive_status"),
        "execution_status": execution_status,
        "validation_status": validation_status,
        "dependencies": dependencies,
        "dependent_count": dependent_count,
        "eligibility": eligibility,
        "eligible_for_pull": eligibility == "eligible",
        "pull_score": pull_score,
        "reasons": reasons or ["meets_autonomous_pull_requirements"],
        "source_path": item["_source_path"],
    }


def build_dependency_graph(items: dict[str, dict], classified: dict[str, dict]) -> dict:
    edges = []
    for item_id, item in items.items():
        for dep_id in dependency_ids(item):
            edges.append(
                {
                    "from": dep_id,
                    "to": item_id,
                    "type": "hard",
                    "description": f"{item_id} depends on {dep_id}",
                }
            )

    eligible = sorted([k for k, v in classified.items() if v["eligibility"] == "eligible"])
    blocked = sorted(
        [
            k
            for k, v in classified.items()
            if v["eligibility"] in {"blocked_dependency", "blocked_placeholder"}
        ]
    )
    archived = sorted(
        [k for k, v in classified.items() if normalize(v.get("archive_status")) == "archived"]
    )
    ready_for_archive = sorted(
        [
            k
            for k, v in classified.items()
            if normalize(v.get("archive_status")) == "ready_for_archive"
        ]
    )
    conditionally_eligible = sorted(
        [k for k, v in classified.items() if v["eligibility"] == "ineligible"]
    )

    nodes = []
    for item_id, item in sorted(items.items()):
        nodes.append(
            {
                "id": item_id,
                "title": item.get("title", ""),
                "category": item.get("category"),
                "priority": item.get("priority"),
                "status": item.get("status"),
                "archive_status": item.get("archive_status"),
            }
        )

    return {
        "schema_version": "1.1",
        "kind": "roadmap_dependency_graph",
        "generated_at": now_utc_iso(),
        "source_of_truth": "docs/roadmap/items/RM-*.yaml",
        "nodes": nodes,
        "edges": edges,
        "blocking_analysis": {
            "eligible_items": eligible,
            "blocked_items": blocked,
            "conditionally_eligible": conditionally_eligible,
            "completed_ready_for_archive": ready_for_archive,
            "archived_items": archived,
        },
    }


def compute_next_pull(items: dict[str, dict]) -> dict:
    dependent_map: dict[str, list[str]] = defaultdict(list)
    for item_id, item in items.items():
        for dep_id in dependency_ids(item):
            dependent_map[dep_id].append(item_id)

    classified = {
        item_id: classify_item(item_id, item, items, len(dependent_map.get(item_id, [])))
        for item_id, item in items.items()
    }

    eligible_nodes = [v for v in classified.values() if v["eligible_for_pull"]]
    eligible_nodes.sort(
        key=lambda node: (
            -node["pull_score"],
            normalize(node.get("priority")),
            node["id"],
        )
    )

    blocked_placeholder = sorted(
        [item_id for item_id, v in classified.items() if v["eligibility"] == "blocked_placeholder"]
    )
    blocked_dependency = sorted(
        [item_id for item_id, v in classified.items() if v["eligibility"] == "blocked_dependency"]
    )
    archived = sorted(
        [item_id for item_id, v in classified.items() if normalize(v.get("archive_status")) == "archived"]
    )
    completed_ready_for_archive = sorted(
        [
            item_id
            for item_id, v in classified.items()
            if normalize(v.get("archive_status")) == "ready_for_archive"
        ]
    )

    chosen = eligible_nodes[0]["id"] if eligible_nodes else None
    status = "ready_for_autonomous_pull" if chosen else "no_eligible_targets"

    return {
        "generated_at": now_utc_iso(),
        "source_of_truth": "docs/roadmap/items/RM-*.yaml",
        "selection_policy_version": "governed-loop-v1",
        "planner_summary": {
            "total_nodes": len(classified),
            "eligible_count": len(eligible_nodes),
            "blocked_dependency_count": len(blocked_dependency),
            "blocked_placeholder_count": len(blocked_placeholder),
            "completed_ready_for_archive_count": len(completed_ready_for_archive),
            "archived_count": len(archived),
            "next_pull_sequence": [n["id"] for n in eligible_nodes[:5]],
        },
        "next_pull_candidates": eligible_nodes,
        "chosen_next_item": chosen,
        "blocked_dependency_items": blocked_dependency,
        "blocked_placeholder_items": blocked_placeholder,
        "completed_ready_for_archive": completed_ready_for_archive,
        "archived_items": archived,
        "nodes": classified,
        "status": status,
    }


def write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def main() -> int:
    items = load_items()
    if not items:
        print("No canonical roadmap items found", file=sys.stderr)
        return 1

    next_pull = compute_next_pull(items)
    graph = build_dependency_graph(items, next_pull["nodes"])

    write_json(NEXT_PULL_OUTPUT_PATH, next_pull)
    write_yaml(GRAPH_OUTPUT_PATH, graph)

    print("Governed next-pull computation complete")
    print(f"Eligible items: {next_pull['planner_summary']['eligible_count']}/{len(items)}")
    print(f"Blocked (dependency): {next_pull['planner_summary']['blocked_dependency_count']}")
    print(f"Blocked (placeholder): {next_pull['planner_summary']['blocked_placeholder_count']}")
    print(f"Chosen next item: {next_pull['chosen_next_item']}")
    print(f"next_pull artifact: {NEXT_PULL_OUTPUT_PATH}")
    print(f"dependency graph: {GRAPH_OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
