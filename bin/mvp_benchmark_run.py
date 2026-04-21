"""Standalone MVP benchmark proof script.

Runs 5 deterministic synthetic tasks through the bounded MVP coding loop and
writes a JSON artifact to artifacts/mvp_benchmark/mvp_benchmark_result.json.

Usage:
    python3 bin/mvp_benchmark_run.py [--artifact-root PATH]
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.mvp_benchmark import MVPBenchmarkRunner, MVP_SYNTHETIC_TASKS
from framework.runtime_adoption_proof import make_bounded_context
from framework.session_job_adapters import make_session_adapter
from framework.typed_permission_gate import ToolPermission, TypedPermissionGate
from framework.workspace_scope import ToolPathScope


@dataclass
class _Workspace:
    source_root: Path
    scratch_root: Path
    artifact_root: Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MVP benchmark")
    parser.add_argument(
        "--artifact-root",
        default=str(REPO_ROOT / "artifacts" / "mvp_benchmark"),
        help="Directory to write benchmark artifacts",
    )
    args = parser.parse_args()
    artifact_root = Path(args.artifact_root)

    with tempfile.TemporaryDirectory(prefix="mvp_bench_") as tmpdir:
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
        session = make_session_adapter(
            "mvp-benchmark",
            "mvp-bench-task",
            task_class="bounded_coding",
            objective="MVP benchmark proof",
        )
        workspace = _Workspace(
            source_root=src_dir,
            scratch_root=scratch_dir,
            artifact_root=ws_artifacts,
        )
        gate = TypedPermissionGate(default_permission=ToolPermission.ALLOW)

        bench_runner = MVPBenchmarkRunner(artifact_root=artifact_root)
        result = bench_runner.run(
            MVP_SYNTHETIC_TASKS,
            task_tmpdir=task_tmpdir,
            session_like=session,
            workspace_like=workspace,
            gate=gate,
            scope=scope,
        )

    print(f"\n{'='*52}")
    print(f"  MVP Benchmark Result")
    print(f"{'='*52}")
    print(f"  Total tasks : {result.total_tasks}")
    print(f"  Passed      : {result.passed}")
    print(f"  Failed      : {result.failed}")
    print(f"  Outcome     : {result.outcome.upper()}")
    print(f"{'='*52}")
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
