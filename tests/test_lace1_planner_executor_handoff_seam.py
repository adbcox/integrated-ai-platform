"""Seam tests for LACE1-P8-PLANNER-EXECUTOR-HANDOFF-SEAM-1."""
from __future__ import annotations
import json, sys, pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.planner_executor_handoff import PlannerExecutorHandoff, HandoffSpec, ExecutionOrder
from framework.task_decomposition_substrate import TaskDecompositionSubstrate


def _bundle(desc="add guard clause", files=None):
    files = files or ["framework/scheduler.py"]
    return TaskDecompositionSubstrate().decompose(desc, files, bundle_id="TEST-BUNDLE")


def test_import_handoff():
    from framework.planner_executor_handoff import PlannerExecutorHandoff
    assert callable(PlannerExecutorHandoff)


def test_build_returns_handoff_spec():
    spec = PlannerExecutorHandoff().build(_bundle())
    assert isinstance(spec, HandoffSpec)


def test_order_count_matches_subtasks():
    bundle = _bundle(files=["a.py", "b.py", "c.py"])
    spec = PlannerExecutorHandoff().build(bundle)
    assert len(spec.execution_orders) == 3
    assert spec.total_orders == 3


def test_order_index_sequential():
    bundle = _bundle(files=["a.py", "b.py"])
    spec = PlannerExecutorHandoff().build(bundle)
    assert [o.order_index for o in spec.execution_orders] == [0, 1]


def test_invalid_repair_action_raises():
    with pytest.raises(ValueError):
        PlannerExecutorHandoff().build(_bundle(), repair_action_on_failure="invalid")


def test_emit_writes_json(tmp_path):
    spec = PlannerExecutorHandoff().build(_bundle())
    path = PlannerExecutorHandoff().emit(spec, artifact_dir=tmp_path)
    assert Path(path).exists()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "handoff_id" in data
    assert len(data["execution_orders"]) == 1
