"""Integrated ops/home/intel/inventory expansion helpers for one governed runtime path."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def derive_home_actions(home_requests: list[dict[str, Any]], home_policy: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    semantics = home_policy.get("bounded_actions", {})

    for idx, request in enumerate(home_requests):
        domain = str(request.get("domain") or "lighting").strip().lower()
        rule = semantics.get(domain, semantics.get("lighting", {}))
        actions.append(
            {
                "action_id": f"home-action-{idx + 1}",
                "domain": domain,
                "intent": str(request.get("intent") or "unspecified"),
                "target": str(request.get("target") or "local-zone"),
                "required_confirmation": bool(rule.get("required_confirmation", False)),
                "bounded_max_actions": int(rule.get("max_actions_per_run", 1)),
                "mode": "recommendation_only",
            }
        )

    return actions


def derive_intel_recommendations(
    candidates: list[dict[str, Any]],
    class_priority: dict[str, int],
    excluded_classes: set[str],
    max_recommendations: int,
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []

    for row in candidates:
        rec_class = str(row.get("recommendation_class") or "watch")
        if rec_class in excluded_classes:
            continue

        ranked.append(
            {
                "name": str(row.get("name") or "unknown"),
                "category": str(row.get("category") or "unknown"),
                "recommendation_class": rec_class,
                "priority_score": int(class_priority.get(rec_class, 0)),
                "integration_role": str(row.get("integration_role") or "unspecified"),
                "roadmap_linkage": list(row.get("roadmap_linkage") or []),
            }
        )

    ranked.sort(key=lambda item: item["priority_score"], reverse=True)
    return ranked[:max_recommendations]


def build_ops_queue(
    home_actions: list[dict[str, Any]],
    intel_recommendations: list[dict[str, Any]],
    procurement_result: dict[str, Any],
) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []

    for action in home_actions:
        queue.append(
            {
                "queue_id": f"ops-home-{action['action_id']}",
                "task_type": "home_operation",
                "priority": "high" if action["required_confirmation"] else "medium",
                "linked_item": "RM-HOME-005",
                "evidence_ref": "artifacts/operations/integrated_ops_expansion_run.json#home_operations",
            }
        )

    for idx, intel in enumerate(intel_recommendations):
        queue.append(
            {
                "queue_id": f"ops-intel-{idx + 1}",
                "task_type": "intel_watch",
                "priority": "high" if intel["recommendation_class"] == "adopt-now" else "medium",
                "linked_item": "RM-INTEL-003",
                "evidence_ref": "artifacts/operations/integrated_ops_expansion_run.json#intel_watch",
            }
        )

    queue.append(
        {
            "queue_id": "ops-inventory-1",
            "task_type": "inventory_decision_support",
            "priority": "high",
            "linked_item": "RM-INV-003",
            "evidence_ref": "artifacts/operations/integrated_ops_expansion_run.json#inventory_decision",
            "total_procurement_cost": procurement_result.get("summary", {}).get("total_procurement_cost", 0.0),
        }
    )

    return queue


def build_integrated_artifact(
    *,
    runtime_session: dict[str, Any],
    control_window_state: dict[str, Any],
    home_actions: list[dict[str, Any]],
    intel_recommendations: list[dict[str, Any]],
    procurement_result: dict[str, Any],
    ops_queue: list[dict[str, Any]],
    policy_path: str,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "kind": "integrated_ops_home_intel_inventory_run",
        "generated_at": utc_now(),
        "roadmap_items": ["RM-OPS-006", "RM-HOME-005", "RM-INTEL-003", "RM-INV-003"],
        "runtime_session": {
            "session_id": runtime_session.get("session_id"),
            "job_id": runtime_session.get("job_id"),
            "objective": runtime_session.get("objective"),
            "allowed_files": runtime_session.get("allowed_files", []),
            "forbidden_files": runtime_session.get("forbidden_files", []),
        },
        "control_window_truth": {
            "artifact_ref": "artifacts/rm_ui005/control_window_state.json",
            "current_lane": control_window_state.get("current_lane"),
            "current_branch": control_window_state.get("current_branch"),
            "selected_route_lane": (control_window_state.get("route_decision") or {}).get("selected_lane"),
        },
        "home_operations": {
            "policy_mode": "recommendation_only",
            "actions": home_actions,
        },
        "intel_watch": {
            "recommendations": intel_recommendations,
        },
        "inventory_decision": procurement_result,
        "ops_execution": {
            "queue": ops_queue,
            "queue_size": len(ops_queue),
        },
        "governance_links": {
            "policy_path": policy_path,
            "watchtower_source": "governance/oss_watchtower_candidates.v1.yaml",
            "procurement_source": "bin/procurement_evaluator.py",
        },
    }
