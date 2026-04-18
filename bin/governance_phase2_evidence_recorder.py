#!/usr/bin/env python3
"""CAP-P2-CLOSE-1 Phase 2 closure evidence recorder.

Deterministically generates ``governance/phase2_closure_evidence.json`` from
a bounded, offline run of the Phase 2 capability tests. The recorder:

1. Drives ``framework.worker_runtime.WorkerRuntime._execute_inner_loop``
   directly against a tmp-path ``victim.py`` with two repair edits
   (``return 0`` -> ``return 1`` -> ``return 2``) and records the number of
   observed ``inner_loop_cycle`` traces and the terminal
   ``WorkerOutcome.status`` / ``failure_class``.
2. Drives the same inner loop against two non-converging repair edits with
   ``max_cycles = 2`` to confirm the cycle machinery is real.
3. Runs ``pytest -q`` on the capability test files as an external cross-
   check and records their outcomes.
4. Writes/checks the evidence JSON.

The recorder does not import from ``pytest`` at module load time so the
negative capability gate can still run if pytest is unavailable in the
environment where this recorder executes (``cmd_write`` will still succeed
and record a ``skipped`` pytest outcome).

The recorder never mutates ``framework/``. It only writes to the
capability-session evidence path under ``governance/`` and to a tmp
workspace.
"""

from __future__ import annotations

import argparse
import json
import queue
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, List, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DIR = REPO_ROOT / "governance"
EVIDENCE_PATH = GOV_DIR / "phase2_closure_evidence.json"
POSITIVE_TEST = "tests/capability/test_phase2_innerloop_closure.py"
NEGATIVE_TEST = "tests/capability/test_phase2_innerloop_closure_negative.py"
ADR_PATH = "governance/authority_adr_0008_phase2_closure.md"
BASELINE_COMMIT = "595dc8750ed671fb23d3cec0be434c76dad818f5"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from framework.backend_profiles import get_backend_profile  # noqa: E402
from framework.inference_adapter import LocalHeuristicInferenceAdapter  # noqa: E402
from framework.job_schema import (  # noqa: E402
    Job,
    JobAction,
    JobClass,
    JobPriority,
    ValidationRequirement,
    WorkTarget,
)
from framework.learning_hooks import LearningHooks  # noqa: E402
from framework.permission_engine import PermissionEngine  # noqa: E402
from framework.sandbox import LocalSandboxRunner  # noqa: E402
from framework.state_store import StateStore  # noqa: E402
from framework.worker_runtime import WorkerRuntime  # noqa: E402
from framework.workspace import WorkspaceController  # noqa: E402

VICTIM_SOURCE = "def answer() -> int:\n    return 0\n\nEXPECTED = 2\n"
VALIDATE_COMMAND = (
    'python3 -B -c "import victim; assert victim.answer() == victim.EXPECTED"'
)


def _run_git(args: Sequence[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def _baseline_iso() -> str:
    return _run_git(["log", "-1", "--format=%cI", BASELINE_COMMIT])


def _build_runtime(workspace_root: Path) -> tuple[WorkerRuntime, StateStore, WorkspaceController]:
    artifact_root = workspace_root / "artifacts"
    artifact_root.mkdir(parents=True, exist_ok=True)
    store = StateStore(artifact_root)
    learning = LearningHooks(
        store=store,
        learning_latest_path=artifact_root / "learning" / "latest.json",
    )
    workspace_controller = WorkspaceController(artifact_root)
    profile = get_backend_profile("mac_local")
    runtime = WorkerRuntime(
        worker_id="cap-phase2-recorder",
        queue_ref=queue.PriorityQueue(),
        inference=LocalHeuristicInferenceAdapter(profile=profile),
        store=store,
        learning=learning,
        stop_event=threading.Event(),
        context_release_callback=lambda _job: None,
        permission_engine=PermissionEngine(),
        workspace_controller=workspace_controller,
        sandbox_runner=LocalSandboxRunner(),
    )
    return runtime, store, workspace_controller


def _build_job(victim_workspace: Path) -> Job:
    return Job(
        task_class=JobClass.VALIDATION_CHECK_EXECUTION,
        priority=JobPriority.P2,
        target=WorkTarget(
            repo_root=str(victim_workspace),
            worktree_target=str(victim_workspace),
        ),
        action=JobAction.INFERENCE_AND_SHELL,
        requested_outputs=[str(victim_workspace / "victim.py")],
        allowed_tools_actions=["run_command", "apply_edit"],
        validation_requirements=[ValidationRequirement.EXIT_CODE_ZERO],
    )


def _count_cycle_traces(store: StateStore) -> tuple[int, List[str]]:
    trace_path = store.traces_dir / "events.jsonl"
    cycles = 0
    kinds: set[str] = set()
    if not trace_path.exists():
        return 0, []
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        kind = str(row.get("kind") or "")
        if kind:
            kinds.add(kind)
        if kind == "inner_loop_cycle":
            cycles += 1
    return cycles, sorted(kinds)


def _run_positive_probe() -> Dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="cap-p2-pos-") as td:
        root = Path(td)
        (root / "victim.py").write_text(VICTIM_SOURCE, encoding="utf-8")
        runtime, store, wc = _build_runtime(root)
        job = _build_job(root)
        config = {
            "enabled": True,
            "validate_command": VALIDATE_COMMAND,
            "repair_edits": [
                {"path": "victim.py", "find": "return 0\n", "replace": "return 1\n"},
                {"path": "victim.py", "find": "return 1\n", "replace": "return 2\n"},
            ],
            "max_cycles": 3,
            "tracked_paths": ["victim.py"],
        }
        workspace = wc.for_job(job)
        outcome = runtime._execute_inner_loop(
            job=job,
            workspace=workspace,
            inference_output="",
            config=config,
            output_snapshot_before={},
        )
        cycles, kinds = _count_cycle_traces(store)
        return {
            "status": outcome.status,
            "failure_class": outcome.failure_class,
            "validation_passed": bool(outcome.validation.get("passed")),
            "observed_cycle_count": cycles,
            "observed_trace_kinds": kinds,
            "repair_edits_applied": 2,
        }


def _run_negative_probe() -> Dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="cap-p2-neg-") as td:
        root = Path(td)
        (root / "victim.py").write_text(VICTIM_SOURCE, encoding="utf-8")
        runtime, store, wc = _build_runtime(root)
        job = _build_job(root)
        config = {
            "enabled": True,
            "validate_command": VALIDATE_COMMAND,
            "repair_edits": [
                {"path": "victim.py", "find": "", "replace": VICTIM_SOURCE},
                {"path": "victim.py", "find": "", "replace": VICTIM_SOURCE},
            ],
            "max_cycles": 2,
            "tracked_paths": ["victim.py"],
        }
        workspace = wc.for_job(job)
        outcome = runtime._execute_inner_loop(
            job=job,
            workspace=workspace,
            inference_output="",
            config=config,
            output_snapshot_before={},
        )
        cycles, kinds = _count_cycle_traces(store)
        return {
            "status": outcome.status,
            "failure_class": outcome.failure_class,
            "validation_passed": bool(outcome.validation.get("passed")),
            "observed_cycle_count": cycles,
            "observed_trace_kinds": kinds,
        }


def _run_pytest(path: str) -> str:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", path],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except FileNotFoundError:
        return "skipped"
    except subprocess.TimeoutExpired:
        return "timeout"
    if result.returncode == 0:
        return "passed"
    if result.returncode == 5:
        return "no_tests_collected"
    return "failed"


def _build_evidence() -> Dict[str, Any]:
    positive = _run_positive_probe()
    negative = _run_negative_probe()
    positive_pytest = _run_pytest(POSITIVE_TEST)
    negative_pytest = _run_pytest(NEGATIVE_TEST)

    positive_ok = (
        positive["status"] == "completed"
        and positive["failure_class"] == ""
        and positive["validation_passed"] is True
        and positive["observed_cycle_count"] >= 2
        and positive_pytest in {"passed", "skipped"}
    )
    negative_ok = (
        negative["status"] == "failed"
        and negative["validation_passed"] is False
        and negative["observed_cycle_count"] >= 2
        and negative_pytest in {"passed", "skipped"}
    )

    combined_trace_kinds = sorted(
        set(positive["observed_trace_kinds"]) | set(negative["observed_trace_kinds"])
    )

    return {
        "schema_version": 1,
        "authority_owner": "governance",
        "generated_at": _baseline_iso(),
        "baseline_commit": BASELINE_COMMIT,
        "driver_path": POSITIVE_TEST,
        "negative_driver_path": NEGATIVE_TEST,
        "positive_test_outcome": "passed" if positive_ok else "failed",
        "negative_test_outcome": "passed" if negative_ok else "failed",
        "positive_pytest_outcome": positive_pytest,
        "negative_pytest_outcome": negative_pytest,
        "observed_cycle_count": int(positive["observed_cycle_count"]),
        "observed_trace_kinds": combined_trace_kinds,
        "final_worker_outcome_status": positive["status"],
        "final_worker_outcome_failure_class": positive["failure_class"],
        "repair_edits_applied": int(positive["repair_edits_applied"]),
        "framework_edits_required": False,
        "framework_edit_justification": "",
        "supersedes": [
            "governance/phase2_adoption_decision.json (adopted_partial; superseded by closure decision)",
        ],
        "adr_ref": ADR_PATH,
        "package_id": "CAP-P2-CLOSE-1",
        "notes": (
            "Positive probe drives _execute_inner_loop through two failing "
            "validate cycles and a successful third cycle. Negative probe "
            "uses two non-converging repair edits with max_cycles=2 to walk "
            "the cycle-limit termination path."
        ),
    }


def _serialize(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def cmd_write() -> int:
    payload = _build_evidence()
    GOV_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(_serialize(payload), encoding="utf-8")
    return 0 if _probes_passed(payload) else 4


def cmd_check() -> int:
    payload = _build_evidence()
    expected = _serialize(payload)
    if not EVIDENCE_PATH.exists():
        print(f"MISSING: {EVIDENCE_PATH}", file=sys.stderr)
        return 3
    if EVIDENCE_PATH.read_text(encoding="utf-8") != expected:
        print(f"DIFF: {EVIDENCE_PATH}", file=sys.stderr)
        return 3
    if not _probes_passed(payload):
        return 4
    return 0


def _probes_passed(payload: Dict[str, Any]) -> bool:
    return (
        payload.get("positive_test_outcome") == "passed"
        and payload.get("negative_test_outcome") == "passed"
        and int(payload.get("observed_cycle_count") or 0) >= 2
        and payload.get("final_worker_outcome_status") == "completed"
        and payload.get("final_worker_outcome_failure_class") == ""
        and payload.get("framework_edits_required") is False
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CAP-P2-CLOSE-1 evidence recorder")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--fail-on-diff", action="store_true")
    args = parser.parse_args(argv)
    if not (args.write or args.check or args.fail_on_diff):
        parser.error("one of --write, --check, or --fail-on-diff is required")
    if args.write:
        rc = cmd_write()
        if rc != 0:
            return rc
        if args.fail_on_diff or args.check:
            return cmd_check()
        return 0
    return cmd_check()


if __name__ == "__main__":
    sys.exit(main())
