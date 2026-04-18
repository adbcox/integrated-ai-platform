"""CAP-P2-CLOSE-1 negative capability guard.

Proves the bounded inner-loop cycle machinery is real by running
``_execute_inner_loop`` against non-converging repair edits capped at
``max_cycles = 2``. Both cycles must execute and emit ``inner_loop_cycle``
traces, and the terminal ``WorkerOutcome`` must report ``failed``.

The capped-``max_cycles`` path is the only way to walk the bounded loop
through two trace emissions without converging: with ``repair_edits = []``
the implementation short-circuits on ``repairs_exhausted`` after a single
cycle. Using two no-op repair edits keeps the repair queue non-empty while
still never resolving the assertion in ``victim.py``, which exercises the
cycle-limit termination path the negative assertion requires.
"""

from __future__ import annotations

import json
from pathlib import Path

from framework.worker_runtime import WorkerOutcome

from .conftest import VICTIM_SOURCE, VALIDATE_COMMAND


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


def test_negative_inner_loop_fails_with_two_cycle_traces(
    runtime, capability_job, victim_workspace, state_store
):
    non_converging_repairs = [
        {"path": "victim.py", "find": "", "replace": VICTIM_SOURCE},
        {"path": "victim.py", "find": "", "replace": VICTIM_SOURCE},
    ]
    config = {
        "enabled": True,
        "validate_command": VALIDATE_COMMAND,
        "repair_edits": non_converging_repairs,
        "max_cycles": 2,
        "tracked_paths": ["victim.py"],
    }
    workspace = runtime._workspace_controller.for_job(capability_job)

    outcome: WorkerOutcome = runtime._execute_inner_loop(
        job=capability_job,
        workspace=workspace,
        inference_output="",
        config=config,
        output_snapshot_before={},
    )

    assert outcome.status == "failed", outcome
    assert outcome.validation.get("passed") is False

    events = _read_trace_events(state_store.traces_dir)
    cycles = [row for row in events if row.get("kind") == "inner_loop_cycle"]
    assert len(cycles) >= 2, f"expected >=2 inner_loop_cycle traces, got {len(cycles)}"
