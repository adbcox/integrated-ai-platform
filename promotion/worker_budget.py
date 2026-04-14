"""Worker-utilization budget ledger for stage orchestration.

Worker-routing v3 adds bounded adaptive tuning from historical outcomes.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = REPO_ROOT / "artifacts" / "worker" / "budget_ledger.json"
DEFAULT_ADAPTIVE_WINDOW_DAYS = 14
MAX_HISTORY_ITEMS = 5000


@dataclass(frozen=True)
class WorkerBudgetDecision:
    lane: str
    worker_class: str
    allowed: bool
    used: int
    limit: int
    reason: str
    timestamp: str
    base_limit: int = 0
    adaptive_adjustment: int = 0
    family: str = "unknown"
    adaptive_stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _load_ledger(path: Path = LEDGER_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"days": {}, "history": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"days": {}, "history": []}
    if not isinstance(data, dict):
        return {"days": {}, "history": []}
    data.setdefault("days", {})
    history = data.get("history")
    if not isinstance(history, list):
        data["history"] = []
    return data


def _save_ledger(payload: dict[str, Any], path: Path = LEDGER_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _is_within_window(timestamp: str, cutoff_ts: float) -> bool:
    try:
        event_ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return False
    return event_ts >= cutoff_ts


def _adaptive_adjustment(
    *,
    ledger: dict[str, Any],
    lane: str,
    worker_class: str,
    family: str,
    window_days: int,
) -> tuple[int, dict[str, Any], str]:
    history = ledger.get("history") or []
    if not history:
        return 0, {"samples": 0}, "adaptive_insufficient_history"

    cutoff_ts = datetime.now(UTC).timestamp() - (max(1, window_days) * 86400)

    relevant: list[dict[str, Any]] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        if str(item.get("lane") or "") != lane:
            continue
        if str(item.get("worker_class") or "") != worker_class:
            continue
        if str(item.get("family") or "unknown") != family:
            continue
        ts = str(item.get("timestamp") or "")
        if not _is_within_window(ts, cutoff_ts):
            continue
        relevant.append(item)

    # Fall back to class-level stats if family-level evidence is sparse.
    family_scope = "family"
    if len(relevant) < 5:
        relevant = []
        for item in history:
            if not isinstance(item, dict):
                continue
            if str(item.get("lane") or "") != lane:
                continue
            if str(item.get("worker_class") or "") != worker_class:
                continue
            ts = str(item.get("timestamp") or "")
            if not _is_within_window(ts, cutoff_ts):
                continue
            relevant.append(item)
        family_scope = "class"

    total = len(relevant)
    if total < 5:
        return 0, {"samples": total, "scope": family_scope}, "adaptive_insufficient_history"

    success = 0
    failure = 0
    escalated = 0
    rescued = 0
    for item in relevant:
        outcome = str(item.get("outcome") or "unknown")
        if outcome == "success":
            success += 1
        elif outcome in {"failure", "manual_escalation", "deferred"}:
            failure += 1
        if bool(item.get("escalated")):
            escalated += 1
        if bool(item.get("rescued")):
            rescued += 1

    success_rate = success / total
    failure_rate = failure / total
    escalation_rate = escalated / total
    rescue_rate = rescued / total

    adjustment = 0
    reason = "adaptive_neutral"
    if success_rate >= 0.90 and failure_rate <= 0.10 and escalation_rate <= 0.10:
        adjustment = 2
        reason = "adaptive_raise_high_confidence"
    elif success_rate >= 0.80 and failure_rate <= 0.15 and escalation_rate <= 0.20:
        adjustment = 1
        reason = "adaptive_raise"
    elif failure_rate >= 0.40 or escalation_rate >= 0.45:
        adjustment = -2
        reason = "adaptive_lower_high_risk"
    elif failure_rate >= 0.25 or escalation_rate >= 0.30 or rescue_rate >= 0.35:
        adjustment = -1
        reason = "adaptive_lower"

    stats = {
        "samples": total,
        "scope": family_scope,
        "success_rate": round(success_rate, 3),
        "failure_rate": round(failure_rate, 3),
        "escalation_rate": round(escalation_rate, 3),
        "rescue_rate": round(rescue_rate, 3),
    }
    return adjustment, stats, reason


def summarize_worker_family_outcomes(
    *,
    lane: str,
    worker_class: str,
    family: str,
    window_days: int = DEFAULT_ADAPTIVE_WINDOW_DAYS,
    path: Path = LEDGER_PATH,
) -> dict[str, Any]:
    """Summarize family/class outcomes for manager strategy decisions."""

    ledger = _load_ledger(path)
    history = ledger.get("history") or []
    cutoff_ts = datetime.now(UTC).timestamp() - (max(1, window_days) * 86400)

    cls = "grouped" if worker_class == "grouped" else "single"
    family_rows: list[dict[str, Any]] = []
    class_rows: list[dict[str, Any]] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        if str(item.get("lane") or "") != lane:
            continue
        if str(item.get("worker_class") or "") != cls:
            continue
        ts = str(item.get("timestamp") or "")
        if not _is_within_window(ts, cutoff_ts):
            continue
        class_rows.append(item)
        if str(item.get("family") or "unknown") == family:
            family_rows.append(item)

    rows = family_rows if len(family_rows) >= 3 else class_rows
    scope = "family" if rows is family_rows else "class"
    total = len(rows)
    if total == 0:
        return {
            "samples": 0,
            "scope": scope,
            "success_rate": 0.0,
            "failure_rate": 0.0,
            "escalation_rate": 0.0,
            "rescue_rate": 0.0,
        }

    success = 0
    failure = 0
    escalated = 0
    rescued = 0
    for item in rows:
        outcome = str(item.get("outcome") or "unknown")
        if outcome == "success":
            success += 1
        elif outcome in {"failure", "manual_escalation", "deferred"}:
            failure += 1
        if bool(item.get("escalated")):
            escalated += 1
        if bool(item.get("rescued")):
            rescued += 1

    return {
        "samples": total,
        "scope": scope,
        "success_rate": round(success / total, 3),
        "failure_rate": round(failure / total, 3),
        "escalation_rate": round(escalated / total, 3),
        "rescue_rate": round(rescued / total, 3),
    }


def worker_budget_forecast(
    *,
    lane: str,
    worker_class: str,
    grouped_limit: int,
    single_limit: int,
    family: str = "unknown",
    adaptive_window_days: int = DEFAULT_ADAPTIVE_WINDOW_DAYS,
    path: Path = LEDGER_PATH,
) -> dict[str, Any]:
    """Read-only budget forecast used by manager planning before dispatch."""

    ledger = _load_ledger(path)
    cls = "grouped" if worker_class == "grouped" else "single"
    base_limit = int(grouped_limit if cls == "grouped" else single_limit)
    day_key = datetime.now(UTC).date().isoformat()
    day = (ledger.get("days") or {}).get(day_key) or {}
    lane_key = f"{lane}:{cls}"
    used = int(day.get(lane_key, 0))
    adjustment, adaptive_stats, adaptive_reason = _adaptive_adjustment(
        ledger=ledger,
        lane=lane,
        worker_class=cls,
        family=family,
        window_days=adaptive_window_days,
    )
    adaptive_ceiling = max(base_limit * 2, base_limit)
    effective_limit = max(1, min(base_limit + adjustment, adaptive_ceiling))
    remaining = effective_limit - used
    return {
        "lane": lane,
        "worker_class": cls,
        "family": family,
        "base_limit": base_limit,
        "effective_limit": effective_limit,
        "used": used,
        "remaining": remaining,
        "adaptive_adjustment": adjustment,
        "adaptive_stats": {**adaptive_stats, "adaptive_reason": adaptive_reason},
    }


def apply_worker_budget(
    *,
    lane: str,
    worker_class: str,
    grouped_limit: int,
    single_limit: int,
    family: str = "unknown",
    adaptive_window_days: int = DEFAULT_ADAPTIVE_WINDOW_DAYS,
    path: Path = LEDGER_PATH,
) -> WorkerBudgetDecision:
    ledger = _load_ledger(path)
    day_key = datetime.now(UTC).date().isoformat()
    days = ledger.setdefault("days", {})
    day = days.setdefault(day_key, {})

    cls = "grouped" if worker_class == "grouped" else "single"
    base_limit = int(grouped_limit if cls == "grouped" else single_limit)

    adjustment, adaptive_stats, adaptive_reason = _adaptive_adjustment(
        ledger=ledger,
        lane=lane,
        worker_class=cls,
        family=family,
        window_days=adaptive_window_days,
    )
    adaptive_ceiling = max(base_limit * 2, base_limit)
    limit = max(1, min(base_limit + adjustment, adaptive_ceiling))

    lane_key = f"{lane}:{cls}"
    used = int(day.get(lane_key, 0))

    if limit > 0 and used >= limit:
        decision = WorkerBudgetDecision(
            lane=lane,
            worker_class=cls,
            allowed=False,
            used=used,
            limit=limit,
            reason="budget_exhausted",
            timestamp=_now_iso(),
            base_limit=base_limit,
            adaptive_adjustment=adjustment,
            family=family,
            adaptive_stats={**adaptive_stats, "adaptive_reason": adaptive_reason},
        )
        day[f"last_decision:{lane_key}"] = decision.to_dict()
        _save_ledger(ledger, path)
        return decision

    used += 1
    day[lane_key] = used
    decision = WorkerBudgetDecision(
        lane=lane,
        worker_class=cls,
        allowed=True,
        used=used,
        limit=limit,
        reason="budget_available",
        timestamp=_now_iso(),
        base_limit=base_limit,
        adaptive_adjustment=adjustment,
        family=family,
        adaptive_stats={**adaptive_stats, "adaptive_reason": adaptive_reason},
    )
    day[f"last_decision:{lane_key}"] = decision.to_dict()
    _save_ledger(ledger, path)
    return decision


def record_worker_outcome(
    *,
    lane: str,
    worker_class: str,
    family: str,
    status: str,
    escalation_hint: str | None = None,
    path: Path = LEDGER_PATH,
) -> None:
    """Persist execution outcomes to tune future class/family budgets.

    This records bounded signals only; it does not change safety policy.
    """

    ledger = _load_ledger(path)
    history = ledger.setdefault("history", [])

    status_lc = str(status or "unknown").lower()
    outcome = "success"
    if status_lc.startswith("deferred"):
        outcome = "deferred"
    elif status_lc.startswith("dropped") or status_lc in {"failed", "failure", "error"}:
        outcome = "failure"
    elif "manual" in status_lc or "escalat" in status_lc:
        outcome = "manual_escalation"

    escalated = bool(escalation_hint) or outcome == "manual_escalation"
    rescued = "partial_success" in status_lc or "split" in status_lc

    history.append(
        {
            "timestamp": _now_iso(),
            "lane": lane,
            "worker_class": "grouped" if worker_class == "grouped" else "single",
            "family": family or "unknown",
            "status": status,
            "outcome": outcome,
            "escalated": escalated,
            "rescued": rescued,
            "escalation_hint": escalation_hint or "",
        }
    )
    if len(history) > MAX_HISTORY_ITEMS:
        del history[:-MAX_HISTORY_ITEMS]
    _save_ledger(ledger, path)
