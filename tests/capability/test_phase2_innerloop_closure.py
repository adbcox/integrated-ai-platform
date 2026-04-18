"""CAP-P2-CLOSE-1 positive capability test.

Drives ``WorkerRuntime._execute_inner_loop`` against a tmp_path ``victim.py``
through two failing validate cycles followed by a successful third cycle,
confirming that the bounded inner loop converges to a ``completed`` terminal
``WorkerOutcome`` after consuming two repair edits.
"""

from __future__ import annotations

import json
from pathlib import Path

from framework.worker_runtime import WorkerOutcome

from .conftest import VALIDATE_COMMAND


FRAMEWORK_RELATIVE = "framework"


def _read_trace_events(store_traces_dir: Path) -> list[dict]:
    path = store_traces_dir / "events.jsonl"
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def test_positive_inner_loop_closes_with_completed_outcome(
    runtime, capability_job, victim_workspace, state_store
):
    repair_edits = [
        {"path": "victim.py", "find": "return 0\n", "replace": "return 1\n"},
        {"path": "victim.py", "find": "return 1\n", "replace": "return 2\n"},
    ]
    config = {
        "enabled": True,
        "validate_command": VALIDATE_COMMAND,
        "repair_edits": repair_edits,
        "max_cycles": 3,
        "tracked_paths": ["victim.py"],
    }
    workspace = runtime._workspace_controller.for_job(capability_job)

    repo_root = Path(__file__).resolve().parents[2]
    framework_before = sorted(
        (p.relative_to(repo_root), p.read_bytes())
        for p in (repo_root / FRAMEWORK_RELATIVE).rglob("*")
        if p.is_file()
    )

    outcome: WorkerOutcome = runtime._execute_inner_loop(
        job=capability_job,
        workspace=workspace,
        inference_output="",
        config=config,
        output_snapshot_before={},
    )

    framework_after = sorted(
        (p.relative_to(repo_root), p.read_bytes())
        for p in (repo_root / FRAMEWORK_RELATIVE).rglob("*")
        if p.is_file()
    )
    assert framework_before == framework_after, (
        "capability test must not mutate framework/ source files"
    )

    assert outcome.status == "completed", outcome
    assert outcome.failure_class == ""
    assert outcome.retry_recommended is False
    assert outcome.validation.get("passed") is True

    final_source = (victim_workspace / "victim.py").read_text(encoding="utf-8")
    assert "return 2" in final_source
    assert "return 0" not in final_source

    events = _read_trace_events(state_store.traces_dir)
    cycles = [row for row in events if row.get("kind") == "inner_loop_cycle"]
    assert len(cycles) >= 2, f"expected >=2 inner_loop_cycle traces, got {len(cycles)}"
    cycle_numbers = [int(row.get("cycle") or 0) for row in cycles]
    assert cycle_numbers[0] == 1
    assert cycle_numbers[-1] >= 2
