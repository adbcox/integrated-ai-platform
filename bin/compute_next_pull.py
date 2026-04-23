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
BLOCKER_OUTPUT_PATH = REPO_ROOT / "artifacts/planning/blocker_registry.json"

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
AUTONOMOUS_EXECUTION_STATUSES = {"eligible", "eligible_with_guardrails", "blocked"}
EXECUTION_CONTRACT_REQUIRED_FIELDS = [
    "autonomous_execution_status",
    "next_bounded_slice",
    "max_autonomous_scope",
    "validation_contract",
    "artifact_contract",
    "completion_contract",
    "truth_surface_updates_required",
    "external_dependency_readiness",
]
VALIDATION_CONTRACT_REQUIRED_FIELDS = ["required_validations", "pass_criteria"]
ARTIFACT_CONTRACT_REQUIRED_FIELDS = ["required_artifacts", "evidence_outputs"]
COMPLETION_CONTRACT_REQUIRED_FIELDS = [
    "substep_complete_when",
    "bounded_slice_complete_when",
    "item_complete_when",
    "blocker_chain_cleared_when",
    "small_patch_is_not_completion",
]


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


def missing_execution_contract_fields(item: dict) -> list[str]:
    contract = item.get("execution_contract") or {}
    missing = []
    for field in EXECUTION_CONTRACT_REQUIRED_FIELDS:
        value = contract.get(field)
        if value in (None, "", [], {}):
            missing.append(field)

    validation_contract = contract.get("validation_contract") or {}
    for field in VALIDATION_CONTRACT_REQUIRED_FIELDS:
        value = validation_contract.get(field)
        if value in (None, "", [], {}):
            missing.append(f"validation_contract.{field}")

    artifact_contract = contract.get("artifact_contract") or {}
    for field in ARTIFACT_CONTRACT_REQUIRED_FIELDS:
        value = artifact_contract.get(field)
        if value in (None, "", [], {}):
            missing.append(f"artifact_contract.{field}")

    completion_contract = contract.get("completion_contract") or {}
    for field in COMPLETION_CONTRACT_REQUIRED_FIELDS:
        value = completion_contract.get(field)
        if value in (None, "", [], {}):
            missing.append(f"completion_contract.{field}")

    return missing


def external_dependency_block(contract: dict) -> tuple[bool, str]:
    external = contract.get("external_dependency_readiness") or {}
    required = bool(external.get("required", False))
    blocks = bool(external.get("blocks_autonomous_execution", False))
    status = normalize(external.get("readiness_status"))
    if required and blocks and status != "ready":
        return True, f"external_dependency_not_ready={status or 'unset'}"
    return False, ""


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
    missing_execution_contract = missing_execution_contract_fields(item)
    governance = item.get("governance") or {}
    missing_governance = [field for field in REQUIRED_GOVERNANCE_FIELDS if not governance.get(field)]
    execution_contract = item.get("execution_contract") or {}
    autonomous_status = normalize(execution_contract.get("autonomous_execution_status"))
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
    if status in PLANNABLE_STATUSES and missing_execution_contract:
        eligibility = "ineligible"
        reasons.append(f"missing_execution_contract={','.join(missing_execution_contract)}")
    if status in PLANNABLE_STATUSES and autonomous_status not in AUTONOMOUS_EXECUTION_STATUSES:
        eligibility = "ineligible"
        reasons.append(
            f"invalid_autonomous_execution_status={autonomous_status or 'unset'}"
        )
    if status in PLANNABLE_STATUSES and autonomous_status == "blocked":
        eligibility = "blocked_external_dependency"
        reasons.append("autonomous_execution_status=blocked")

    external_blocked, external_reason = external_dependency_block(execution_contract)
    if status in PLANNABLE_STATUSES and external_blocked:
        eligibility = "blocked_external_dependency"
        reasons.append(external_reason)

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

    priority_score = {"p0": 16, "p1": 12, "p2": 8, "p3": 4, "p4": 0}.get(
        normalize(item.get("priority")), 0
    )
    scoring = item.get("scoring") or {}
    strategic_value = int(scoring.get("strategic_value") or 0)
    architecture_fit = int(scoring.get("architecture_fit") or 0)
    readiness = int(scoring.get("readiness") or 0)
    execution_risk = int(scoring.get("execution_risk") or 0)
    dependency_burden = int(scoring.get("dependency_burden") or 0)
    grouped_execution_relevance = 2 if (item.get("grouping") or {}).get("package_group") else 0
    autonomy_weight = {"eligible": 3, "eligible_with_guardrails": 2, "blocked": 0}.get(
        autonomous_status, 0
    )
    pull_score = (
        priority_score
        + strategic_value
        + architecture_fit
        + readiness
        + autonomy_weight
        + grouped_execution_relevance
        + min(dependent_count, 4)
        - execution_risk
        - dependency_burden
    )

    return {
        "id": item_id,
        "title": item.get("title", ""),
        "category": item.get("category"),
        "priority": item.get("priority"),
        "status": item.get("status"),
        "archive_status": item.get("archive_status"),
        "execution_status": execution_status,
        "validation_status": validation_status,
        "autonomous_execution_status": execution_contract.get("autonomous_execution_status"),
        "execution_contract_present": bool(execution_contract),
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
    # Keep this list focused on non-terminal items that may become eligible after
    # bounded fixes; archived/ready-for-archive/terminal items are tracked separately.
    conditionally_eligible = sorted(
        [
            k
            for k, v in classified.items()
            if v["eligibility"] == "ineligible"
            and normalize(v.get("archive_status")) not in {"archived", "ready_for_archive"}
            and normalize(v.get("status")) not in TERMINAL_STATUSES
        ]
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
    blocked_external_dependency = sorted(
        [item_id for item_id, v in classified.items() if v["eligibility"] == "blocked_external_dependency"]
    )
    true_blockers = sorted(
        [
            item_id
            for item_id, v in classified.items()
            if v["eligibility"] in {"blocked_dependency", "blocked_external_dependency"}
            or (
                normalize(v.get("status")) in PLANNABLE_STATUSES
                and any(reason.startswith("missing_execution_contract=") for reason in v.get("reasons", []))
            )
        ]
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
            "blocked_external_dependency_count": len(blocked_external_dependency),
            "true_blocker_count": len(true_blockers),
            "completed_ready_for_archive_count": len(completed_ready_for_archive),
            "archived_count": len(archived),
            "next_pull_sequence": [n["id"] for n in eligible_nodes[:5]],
        },
        "next_pull_candidates": eligible_nodes,
        "chosen_next_item": chosen,
        "blocked_dependency_items": blocked_dependency,
        "blocked_external_dependency_items": blocked_external_dependency,
        "blocked_placeholder_items": blocked_placeholder,
        "true_blocker_items": true_blockers,
        "completed_ready_for_archive": completed_ready_for_archive,
        "archived_items": archived,
        "nodes": classified,
        "status": status,
    }


def build_blocker_registry(next_pull: dict) -> dict:
    nodes = next_pull.get("nodes", {})
    true_blockers = []
    non_blocking_remaining_work = []
    completed_ready_for_archive = set(next_pull.get("completed_ready_for_archive", []))
    archived_items = set(next_pull.get("archived_items", []))
    for item_id, node in sorted(nodes.items()):
        eligibility = node.get("eligibility")
        reasons = node.get("reasons", [])
        if item_id in set(next_pull.get("true_blocker_items", [])):
            if eligibility == "blocked_dependency":
                blocker_type = "dependency_blocker"
            elif eligibility == "blocked_external_dependency":
                blocker_type = "external_dependency_blocker"
            elif any(str(reason).startswith("missing_execution_contract=") for reason in reasons):
                blocker_type = "missing_execution_contract"
            else:
                blocker_type = "other_blocker"
            true_blockers.append(
                {
                    "id": item_id,
                    "blocker_type": blocker_type,
                    "reasons": reasons,
                }
            )
        elif eligibility == "eligible":
            non_blocking_remaining_work.append(
                {
                    "id": item_id,
                    "status": node.get("status"),
                    "reason": "eligible_next_work",
                    "pull_score": node.get("pull_score"),
                }
            )
        elif item_id in completed_ready_for_archive:
            non_blocking_remaining_work.append(
                {
                    "id": item_id,
                    "status": node.get("status"),
                    "reason": "completed_ready_for_archive",
                    "pull_score": node.get("pull_score"),
                }
            )
        elif item_id in archived_items:
            non_blocking_remaining_work.append(
                {
                    "id": item_id,
                    "status": node.get("status"),
                    "reason": "archived_terminal",
                    "pull_score": node.get("pull_score"),
                }
            )

    return {
        "generated_at": next_pull.get("generated_at"),
        "source_of_truth": "docs/roadmap/items/RM-*.yaml",
        "selector_status": next_pull.get("status"),
        "summary": {
            "true_blocker_count": len(true_blockers),
            "eligible_next_work_count": len(next_pull.get("next_pull_candidates", [])),
            "blocked_placeholder_count": len(next_pull.get("blocked_placeholder_items", [])),
            "blocked_external_dependency_count": len(next_pull.get("blocked_external_dependency_items", [])),
            "non_blocking_remaining_work_count": len(non_blocking_remaining_work),
        },
        "true_blockers": true_blockers,
        "eligible_next_work": next_pull.get("next_pull_candidates", []),
        "blocked_placeholder_items": next_pull.get("blocked_placeholder_items", []),
        "blocked_external_dependency_items": next_pull.get("blocked_external_dependency_items", []),
        "non_blocking_remaining_work": non_blocking_remaining_work,
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
    blocker_registry = build_blocker_registry(next_pull)

    write_json(NEXT_PULL_OUTPUT_PATH, next_pull)
    write_json(BLOCKER_OUTPUT_PATH, blocker_registry)
    write_yaml(GRAPH_OUTPUT_PATH, graph)

    print("Governed next-pull computation complete")
    print(f"Eligible items: {next_pull['planner_summary']['eligible_count']}/{len(items)}")
    print(f"Blocked (dependency): {next_pull['planner_summary']['blocked_dependency_count']}")
    print(f"Blocked (placeholder): {next_pull['planner_summary']['blocked_placeholder_count']}")
    print(
        f"Blocked (external dependency): {next_pull['planner_summary']['blocked_external_dependency_count']}"
    )
    print(f"Chosen next item: {next_pull['chosen_next_item']}")
    print(f"next_pull artifact: {NEXT_PULL_OUTPUT_PATH}")
    print(f"blocker registry artifact: {BLOCKER_OUTPUT_PATH}")
    print(f"dependency graph: {GRAPH_OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
