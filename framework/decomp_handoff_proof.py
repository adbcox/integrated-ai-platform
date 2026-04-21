"""LACE2-P3-LIVE-DECOMP-HANDOFF-PROOF-SEAM-1: end-to-end decomp-to-handoff proof on real repo files."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.task_decomposition_substrate import TaskDecompositionSubstrate, DecomposedTaskBundle, SubTask
from framework.planner_executor_handoff import PlannerExecutorHandoff, HandoffSpec, ExecutionOrder

assert "subtasks" in DecomposedTaskBundle.__dataclass_fields__, "INTERFACE MISMATCH: DecomposedTaskBundle.subtasks"
assert "bundle_id" in DecomposedTaskBundle.__dataclass_fields__, "INTERFACE MISMATCH: DecomposedTaskBundle.bundle_id"
assert "execution_orders" in HandoffSpec.__dataclass_fields__, "INTERFACE MISMATCH: HandoffSpec.execution_orders"
assert "total_orders" in HandoffSpec.__dataclass_fields__, "INTERFACE MISMATCH: HandoffSpec.total_orders"
assert "kind" in SubTask.__dataclass_fields__, "INTERFACE MISMATCH: SubTask.kind"
assert "order_index" in ExecutionOrder.__dataclass_fields__, "INTERFACE MISMATCH: ExecutionOrder.order_index"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class DecompHandoffProofRecord:
    proof_id: str
    task_description: str
    target_files: List[str]
    bundle_id: str
    subtask_count: int
    subtask_kinds: List[str]
    handoff_id: str
    total_orders: int
    handoff_policy: str
    repair_action_on_failure: str
    proved_at: str
    artifact_path: Optional[str] = None


class DecompHandoffProofRunner:
    """Chains TaskDecompositionSubstrate → PlannerExecutorHandoff on real repo target files."""

    def run(
        self,
        description: str,
        target_files: List[str],
        *,
        repair_action: str = "retry",
    ) -> DecompHandoffProofRecord:
        bundle: DecomposedTaskBundle = TaskDecompositionSubstrate().decompose(
            description, target_files, bundle_id="LACE2-PROOF"
        )
        spec: HandoffSpec = PlannerExecutorHandoff().build(
            bundle, repair_action_on_failure=repair_action
        )
        return DecompHandoffProofRecord(
            proof_id=f"DHP-LACE2-{_ts()}",
            task_description=description,
            target_files=list(target_files),
            bundle_id=bundle.bundle_id,
            subtask_count=len(bundle.subtasks),
            subtask_kinds=[st.kind for st in bundle.subtasks],
            handoff_id=spec.handoff_id,
            total_orders=spec.total_orders,
            handoff_policy=spec.handoff_policy,
            repair_action_on_failure=repair_action,
            proved_at=_iso_now(),
        )

    def emit(self, record: DecompHandoffProofRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "decomp_handoff_proof.json"
        out_path.write_text(
            json.dumps({
                "proof_id": record.proof_id,
                "task_description": record.task_description,
                "target_files": record.target_files,
                "bundle_id": record.bundle_id,
                "subtask_count": record.subtask_count,
                "subtask_kinds": record.subtask_kinds,
                "handoff_id": record.handoff_id,
                "total_orders": record.total_orders,
                "handoff_policy": record.handoff_policy,
                "repair_action_on_failure": record.repair_action_on_failure,
                "proved_at": record.proved_at,
            }, indent=2),
            encoding="utf-8",
        )
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["DecompHandoffProofRecord", "DecompHandoffProofRunner"]
