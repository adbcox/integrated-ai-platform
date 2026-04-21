"""Standalone devloop benchmark proof script.

Runs 5 deterministic synthetic tasks through the file-local bounded coding loop
and writes a JSON artifact to artifacts/devloop_benchmark/devloop_benchmark_result.json.

Usage:
    python3 bin/devloop_benchmark_run.py [--artifact-root PATH]
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.devloop_benchmark import DevloopBenchmarkRunner, SYNTHETIC_TASK_FAMILY
from framework.typed_permission_gate import PermissionRule, ToolPermission, TypedPermissionGate
from framework.workspace_scope import ToolPathScope


@dataclass
class _Session:
    session_id: str


@dataclass
class _Workspace:
    source_root: Path
    scratch_root: Path
    artifact_root: Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run devloop benchmark")
    parser.add_argument(
        "--artifact-root",
        default=str(REPO_ROOT / "artifacts" / "devloop_benchmark"),
        help="Directory to write benchmark artifacts",
    )
    args = parser.parse_args()
    artifact_root = Path(args.artifact_root)

    with tempfile.TemporaryDirectory(prefix="devloop_bench_") as tmpdir:
        task_tmpdir = Path(tmpdir) / "tasks"
        task_tmpdir.mkdir()
        src_dir = Path(tmpdir) / "src"
        src_dir.mkdir()
        scratch_dir = Path(tmpdir) / "scratch"
        scratch_dir.mkdir()
        ws_artifacts = Path(tmpdir) / "artifacts"
        ws_artifacts.mkdir()

        scope = ToolPathScope(
            source_root=src_dir,
            writable_roots=(task_tmpdir, scratch_dir, ws_artifacts),
        )
        session = _Session(session_id="devloop-benchmark")
        workspace = _Workspace(
            source_root=src_dir,
            scratch_root=scratch_dir,
            artifact_root=ws_artifacts,
        )
        gate = TypedPermissionGate(default_permission=ToolPermission.ALLOW)

        runner = DevloopBenchmarkRunner(artifact_root=artifact_root)
        result = runner.run(
            SYNTHETIC_TASK_FAMILY,
            task_tmpdir=task_tmpdir,
            session_like=session,
            workspace_like=workspace,
            gate=gate,
            scope=scope,
        )

    print(f"\n{'='*50}")
    print(f"  Devloop Benchmark Result")
    print(f"{'='*50}")
    print(f"  Total tasks : {result.total_tasks}")
    print(f"  Passed      : {result.passed}")
    print(f"  Failed      : {result.failed}")
    print(f"  Outcome     : {result.outcome.upper()}")
    print(f"{'='*50}")
    if result.artifact_path:
        print(f"  Artifact    : {result.artifact_path}")
    print()
    for tr in result.task_results:
        status = "PASS" if tr["passed"] else "FAIL"
        print(f"  [{status}] {tr['task_id']} ({tr['task_kind']})")
    print()

    return 0 if result.outcome == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
