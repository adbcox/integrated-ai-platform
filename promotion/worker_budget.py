"""Worker-utilization budget ledger for stage orchestration."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = REPO_ROOT / "artifacts" / "worker" / "budget_ledger.json"


@dataclass(frozen=True)
class WorkerBudgetDecision:
    lane: str
    worker_class: str
    allowed: bool
    used: int
    limit: int
    reason: str
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _load_ledger(path: Path = LEDGER_PATH) -> dict:
    if not path.exists():
        return {"days": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"days": {}}
    if not isinstance(data, dict):
        return {"days": {}}
    data.setdefault("days", {})
    return data


def _save_ledger(payload: dict, path: Path = LEDGER_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def apply_worker_budget(
    *,
    lane: str,
    worker_class: str,
    grouped_limit: int,
    single_limit: int,
    path: Path = LEDGER_PATH,
) -> WorkerBudgetDecision:
    ledger = _load_ledger(path)
    day_key = datetime.now(UTC).date().isoformat()
    days = ledger.setdefault("days", {})
    day = days.setdefault(day_key, {})

    cls = "grouped" if worker_class == "grouped" else "single"
    limit = int(grouped_limit if cls == "grouped" else single_limit)
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
    )
    day[f"last_decision:{lane_key}"] = decision.to_dict()
    _save_ledger(ledger, path)
    return decision
