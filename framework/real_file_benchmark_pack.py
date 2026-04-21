"""LACE2-P7-REAL-FILE-BENCHMARK-PACK-SEAM-1: 8-task real-file benchmark pack from frozen repo content slices."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from framework.local_autonomy_benchmark_pack import LocalAutonomyTask, LACE1_TASK_PACK

assert len(LACE1_TASK_PACK) >= 12, "INTERFACE MISMATCH: LACE1_TASK_PACK too small"

_REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class RealFileTask:
    task_id: str
    task_kind: str
    description: str
    source_fixture_file: str
    initial_content: str
    old_string: str
    new_string: str
    expected_content: str
    loe_points: int
    acceptance_grep: str


def _read_source(relative_path: str) -> str:
    full = _REPO_ROOT / relative_path
    if not full.exists():
        raise RuntimeError(f"REAL_FILE_PACK_BUILD_FAILED: {relative_path} not found")
    return full.read_text(encoding="utf-8")


def _mk_rf(
    task_id: str,
    task_kind: str,
    description: str,
    source_fixture_file: str,
    old_string: str,
    new_string: str,
    loe_points: int,
    acceptance_grep: str,
) -> RealFileTask:
    content = _read_source(source_fixture_file)
    if old_string not in content:
        raise RuntimeError(
            f"REAL_FILE_PACK_BUILD_FAILED: old_string not found in {source_fixture_file!r}:\n  {old_string!r}"
        )
    initial_content = old_string
    expected_content = old_string.replace(old_string, new_string, 1)
    return RealFileTask(
        task_id=task_id,
        task_kind=task_kind,
        description=description,
        source_fixture_file=source_fixture_file,
        initial_content=initial_content,
        old_string=old_string,
        new_string=new_string,
        expected_content=expected_content,
        loe_points=loe_points,
        acceptance_grep=acceptance_grep,
    )


LACE2_REAL_FILE_PACK: tuple = (
    # --- text_replacement × 2 ---
    _mk_rf(
        "LACE2-RF-01", "text_replacement",
        "Replace result_state default from complete to pending in ExecutionTraceResult",
        "framework/execution_trace_result_schema.py",
        '    result_state: str = "complete"',
        '    result_state: str = "pending"',
        1,
        r'result_state.*pending',
    ),
    _mk_rf(
        "LACE2-RF-02", "text_replacement",
        "Replace max_attempts default from 1 to 3 in RetryPolicy",
        "framework/retry_policy_schema.py",
        "    max_attempts: int = 1",
        "    max_attempts: int = 3",
        1,
        r"max_attempts.*3",
    ),
    # --- insert_block × 2 ---
    _mk_rf(
        "LACE2-RF-03", "insert_block",
        "Insert comment annotation after notes field in ExecutionTraceResult",
        "framework/execution_trace_result_schema.py",
        '    notes: str = ""',
        '    notes: str = ""\n    # enriched: bool = False',
        2,
        r"# enriched: bool = False",
    ),
    _mk_rf(
        "LACE2-RF-04", "insert_block",
        "Insert comment annotation after status field in RetryPolicy",
        "framework/retry_policy_schema.py",
        '    status: str = "active"',
        '    status: str = "active"\n    # cooldown_seconds: int = 0',
        2,
        r"# cooldown_seconds: int = 0",
    ),
    # --- add_guard × 2 ---
    _mk_rf(
        "LACE2-RF-05", "add_guard",
        "Add guard comment before decide() method in RepairPolicyGate",
        "framework/repair_policy_gate.py",
        "    def decide(self, failure: FailureRecord) -> RepairDecision:",
        "    # guard: failure_kind must be non-empty\n    def decide(self, failure: FailureRecord) -> RepairDecision:",
        2,
        r"# guard: failure_kind must be non-empty",
    ),
    _mk_rf(
        "LACE2-RF-06", "add_guard",
        "Add guard comment before _run_task() method in Lace1BenchmarkRunner",
        "framework/lace1_benchmark_runner.py",
        "    def _run_task(self, task: LocalAutonomyTask) -> TaskRunResult:",
        "    # guard: old_string must be non-empty\n    def _run_task(self, task: LocalAutonomyTask) -> TaskRunResult:",
        2,
        r"# guard: old_string must be non-empty",
    ),
    # --- add_field × 2 ---
    _mk_rf(
        "LACE2-RF-07", "add_field",
        "Add enriched_by comment annotation after enriched_at field in EnrichedTrace",
        "framework/execution_trace_enricher.py",
        "    enriched_at: str",
        "    enriched_at: str\n    # enriched_by: str = \"local\"",
        2,
        r"# enriched_by: str",
    ),
    _mk_rf(
        "LACE2-RF-08", "add_field",
        "Add notes comment annotation after acceptance_grep field in LocalAutonomyTask",
        "framework/local_autonomy_benchmark_pack.py",
        "    acceptance_grep: str",
        "    acceptance_grep: str\n    # notes: str = \"\"",
        2,
        r"# notes: str",
    ),
)


def validate_real_file_greps(tasks: tuple) -> List[str]:
    """Return list of task_ids with non-compilable acceptance_grep patterns."""
    bad = []
    for t in tasks:
        try:
            re.compile(t.acceptance_grep)
        except re.error:
            bad.append(t.task_id)
    return bad


def emit_real_file_pack(tasks: tuple, artifact_dir: Path) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "real_file_benchmark_pack.json"
    counts: dict = {}
    for t in tasks:
        counts[t.task_kind] = counts.get(t.task_kind, 0) + 1
    out_path.write_text(
        json.dumps({
            "pack_id": "LACE2-REAL-FILE-BENCHMARK-PACK",
            "task_count": len(tasks),
            "kind_summary": counts,
            "tasks": [asdict(t) for t in tasks],
        }, indent=2),
        encoding="utf-8",
    )
    return str(out_path)


def load_real_file_pack(path: Path) -> List[RealFileTask]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [RealFileTask(**t) for t in data["tasks"]]


__all__ = [
    "RealFileTask",
    "LACE2_REAL_FILE_PACK",
    "validate_real_file_greps",
    "emit_real_file_pack",
    "load_real_file_pack",
]
