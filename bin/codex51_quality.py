#!/usr/bin/env python3
"""Deterministic first-attempt quality scoring from plan execution outcomes."""

from __future__ import annotations

from typing import Any

SUCCESS_STATUSES = {"success", "resumed_skip_completed"}
GUARD_STATUSES = {"dropped_preflight", "deferred_worker_budget", "deferred_manager_policy"}


def _is_success_status(status: str) -> bool:
    return status in SUCCESS_STATUSES


def _root_subplan_id(subplan_id: str, expected_ids: list[str]) -> str:
    if subplan_id in expected_ids:
        return subplan_id
    for root in sorted(expected_ids, key=len, reverse=True):
        if subplan_id.startswith(f"{root}-"):
            return root
    return subplan_id


def _status_return_code(row: dict[str, Any]) -> int:
    value = row.get("return_code")
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _rollback_strategy(row: dict[str, Any]) -> str:
    return str((row.get("rollback_contract") or {}).get("strategy") or "")


def _rollback_verified_ok(row: dict[str, Any]) -> bool | None:
    verification = row.get("rollback_verification")
    if not isinstance(verification, dict):
        return None
    value = verification.get("ok")
    return bool(value)


def _dispatch_observed(row: dict[str, Any]) -> bool:
    verification = row.get("rollback_verification")
    if isinstance(verification, dict) and "dispatch" in verification:
        return bool(verification.get("dispatch"))
    status = str(row.get("status") or "")
    if status.startswith("deferred") or status == "dropped_preflight":
        return False
    if "no_dispatch" in _rollback_strategy(row):
        return False
    return True


def _count_dropped_targets(row: dict[str, Any]) -> int:
    dropped = row.get("dropped_targets")
    if not isinstance(dropped, list):
        return 0
    return len([x for x in dropped if x])


def _coverage_flags(plan_payload: dict[str, Any]) -> tuple[bool, bool]:
    reconciliation = plan_payload.get("stage_reconciliation")
    if not isinstance(reconciliation, dict):
        return False, False
    coverage_ok = bool((reconciliation.get("subplan_coverage") or {}).get("coverage_ok"))
    outcome = reconciliation.get("outcome_guarantee") or {}
    outcome_ok = bool(outcome.get("all_subplans_accounted")) and bool(outcome.get("all_checked_contracts_valid"))
    return coverage_ok, outcome_ok


def score_first_attempt_quality(
    *,
    plan_payload: dict[str, Any],
    statuses: list[dict[str, Any]],
    state: str,
    failure_code: int,
) -> dict[str, Any]:
    """Score first-attempt quality from concrete first-vs-final execution signals.

    Returns deterministic score + component signals for auditability.
    """

    subplans = [row for row in (plan_payload.get("subplans") or []) if isinstance(row, dict)]
    expected_ids = [str(sp.get("subplan_id") or "") for sp in subplans if str(sp.get("subplan_id") or "")]
    expected_id_set = set(expected_ids)
    total_subplans = len(expected_ids)

    grouped: dict[str, list[dict[str, Any]]] = {key: [] for key in expected_ids}
    for row in statuses:
        if not isinstance(row, dict):
            continue
        sid = str(row.get("subplan_id") or "")
        if not sid:
            continue
        root = _root_subplan_id(sid, expected_ids)
        if root in expected_id_set:
            grouped[root].append(row)

    first_rows: list[dict[str, Any]] = []
    final_rows: list[dict[str, Any]] = []
    missing_roots = 0
    for root in expected_ids:
        rows = grouped.get(root) or []
        if not rows:
            missing_roots += 1
            continue
        first_rows.append(rows[0])
        final_rows.append(rows[-1])

    first_success = sum(1 for row in first_rows if _is_success_status(str(row.get("status") or "")))
    final_success = sum(1 for row in final_rows if _is_success_status(str(row.get("status") or "")))
    first_rate = round(first_success / total_subplans, 3) if total_subplans else 0.0
    final_rate = round(final_success / total_subplans, 3) if total_subplans else 0.0

    first_nonzero_rc = sum(1 for row in first_rows if _status_return_code(row) != 0)
    final_nonzero_rc = sum(1 for row in final_rows if _status_return_code(row) != 0)

    rescue_count = sum(
        1
        for row in statuses
        if str(row.get("strategy") or "") == "split_subplan"
        or bool(row.get("retry"))
        or str(row.get("retry_strategy") or "")
    ) + len([x for x in (plan_payload.get("recoveries") or []) if isinstance(x, dict)])

    escalation_count = sum(
        1
        for row in statuses
        if str(row.get("status") or "").startswith("deferred")
        or str(row.get("status") or "") == "dropped_family_budget"
        or bool(row.get("escalation_hint"))
    )

    guard_count = sum(
        1
        for row in statuses
        if str(row.get("status") or "") in GUARD_STATUSES or "no_dispatch" in _rollback_strategy(row)
    )

    first_dropped_targets = sum(_count_dropped_targets(row) for row in first_rows)
    final_dropped_targets = sum(_count_dropped_targets(row) for row in final_rows)

    rollback_checked = 0
    rollback_failed = 0
    dispatch_count = 0
    for row in final_rows:
        verified_ok = _rollback_verified_ok(row)
        if verified_ok is not None:
            rollback_checked += 1
            if not verified_ok:
                rollback_failed += 1
        if _dispatch_observed(row):
            dispatch_count += 1

    coverage_ok, outcome_ok = _coverage_flags(plan_payload)

    delta_improvement = max(0.0, final_rate - first_rate)
    delta_drop = max(0.0, first_rate - final_rate)

    first_rc_ratio = (first_nonzero_rc / total_subplans) if total_subplans else 0.0
    final_rc_ratio = (final_nonzero_rc / total_subplans) if total_subplans else 0.0
    rollback_failed_ratio = (rollback_failed / rollback_checked) if rollback_checked else 0.0
    dispatch_ratio = (dispatch_count / total_subplans) if total_subplans else 0.0

    final_success_signal = float(failure_code == 0 and state in {"succeeded", "partial_success"})

    base = (0.55 * first_rate) + (0.2 * final_rate)
    bonus = 0.0
    if final_success_signal > 0:
        bonus += 0.1
    if coverage_ok:
        bonus += 0.05
    if outcome_ok:
        bonus += 0.05
    if rollback_checked > 0 and rollback_failed == 0:
        bonus += 0.03
    if dispatch_ratio >= 0.5:
        bonus += 0.02

    penalty = 0.0
    penalty += 0.25 * delta_improvement
    penalty += 0.15 * delta_drop
    penalty += min(0.2, 0.05 * rescue_count)
    penalty += min(0.2, 0.04 * escalation_count)
    penalty += min(0.15, 0.03 * guard_count)
    penalty += min(0.1, 0.05 * first_rc_ratio)
    penalty += min(0.1, 0.05 * final_rc_ratio)
    penalty += min(0.1, 0.02 * first_dropped_targets)
    penalty += min(0.1, 0.02 * final_dropped_targets)
    penalty += 0.1 * rollback_failed_ratio
    if total_subplans > 0 and missing_roots > 0:
        penalty += min(0.15, 0.08 * (missing_roots / total_subplans))
    if not coverage_ok:
        penalty += 0.1
    if not outcome_ok:
        penalty += 0.1

    score = max(0.0, min(1.0, base + bonus - penalty))

    return {
        "total_subplans": total_subplans,
        "first_attempt_success_count": first_success,
        "first_attempt_success_rate": round(first_rate, 3),
        "final_success_count": final_success,
        "final_success_rate": round(final_rate, 3),
        "first_to_final_improvement": round(delta_improvement, 3),
        "first_attempt_quality_score": round(score, 3),
        "rescue_count": rescue_count,
        "escalation_count": escalation_count,
        "guard_count": guard_count,
        "signal_components": {
            "first_nonzero_return_codes": first_nonzero_rc,
            "final_nonzero_return_codes": final_nonzero_rc,
            "first_dropped_targets": first_dropped_targets,
            "final_dropped_targets": final_dropped_targets,
            "rollback_checked": rollback_checked,
            "rollback_failed": rollback_failed,
            "dispatch_ratio": round(dispatch_ratio, 3),
            "coverage_ok": coverage_ok,
            "outcome_guarantee_ok": outcome_ok,
            "missing_subplan_roots": missing_roots,
            "final_success_signal": final_success_signal,
        },
    }
