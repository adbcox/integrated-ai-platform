"""LACE1-P8-PLANNER-EXECUTOR-HANDOFF-SEAM-1: typed handoff from DecomposedTaskBundle to ordered ExecutionOrders."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.task_decomposition_substrate import DecomposedTaskBundle, SubTask
from framework.repair_policy_gate import RepairPolicyGate

assert "subtasks" in DecomposedTaskBundle.__dataclass_fields__, "INTERFACE MISMATCH: DecomposedTaskBundle.subtasks"
assert "bundle_id" in DecomposedTaskBundle.__dataclass_fields__, "INTERFACE MISMATCH: DecomposedTaskBundle.bundle_id"
assert "kind" in SubTask.__dataclass_fields__, "INTERFACE MISMATCH: SubTask.kind"
assert "target_file" in SubTask.__dataclass_fields__, "INTERFACE MISMATCH: SubTask.target_file"
assert callable(RepairPolicyGate), "INTERFACE MISMATCH: RepairPolicyGate not callable"

_VALID_REPAIR_ACTIONS = {"retry", "escalate_critique", "hard_stop"}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass(frozen=True)
class ExecutionOrder:
    order_index: int
    subtask_id: str
    target_file: str
    kind: str
    description: str
    acceptance_signal: str
    repair_action_on_failure: str


@dataclass
class HandoffSpec:
    handoff_id: str
    source_bundle_id: str
    execution_orders: List[ExecutionOrder]
    total_orders: int
    handoff_policy: str      # always "sequential"
    emitted_at: str
    artifact_path: Optional[str] = None


class PlannerExecutorHandoff:
    """Converts a DecomposedTaskBundle into a sequenced HandoffSpec."""

    def build(
        self,
        bundle: DecomposedTaskBundle,
        *,
        repair_action_on_failure: str = "retry",
    ) -> HandoffSpec:
        if repair_action_on_failure not in _VALID_REPAIR_ACTIONS:
            raise ValueError(
                f"repair_action_on_failure={repair_action_on_failure!r} must be one of {_VALID_REPAIR_ACTIONS}"
            )

        orders = [
            ExecutionOrder(
                order_index=i,
                subtask_id=st.subtask_id,
                target_file=st.target_file,
                kind=st.kind,
                description=st.description,
                acceptance_signal=st.acceptance_signal,
                repair_action_on_failure=repair_action_on_failure,
            )
            for i, st in enumerate(bundle.subtasks)
        ]

        handoff_id = f"HANDOFF-{bundle.bundle_id}-{_ts()}"
        return HandoffSpec(
            handoff_id=handoff_id,
            source_bundle_id=bundle.bundle_id,
            execution_orders=orders,
            total_orders=len(orders),
            handoff_policy="sequential",
            emitted_at=_iso_now(),
        )

    def emit(self, spec: HandoffSpec, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / f"{spec.handoff_id}.json"
        out_path.write_text(
            json.dumps(
                {
                    "handoff_id": spec.handoff_id,
                    "source_bundle_id": spec.source_bundle_id,
                    "execution_orders": [asdict(o) for o in spec.execution_orders],
                    "total_orders": spec.total_orders,
                    "handoff_policy": spec.handoff_policy,
                    "emitted_at": spec.emitted_at,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        spec.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["ExecutionOrder", "HandoffSpec", "PlannerExecutorHandoff"]
