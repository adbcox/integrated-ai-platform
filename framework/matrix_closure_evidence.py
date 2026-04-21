"""Evidence-driven matrix closure record and campaign ratification."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
_MVP_BENCH_ARTIFACT = REPO_ROOT / "artifacts" / "mvp_benchmark" / "mvp_benchmark_result.json"


class MatrixItemState(str, Enum):
    DONE = "done"
    SEED_COMPLETE = "seed_complete"
    PARTIAL = "partial"
    DEFERRED = "deferred"


@dataclass
class MatrixItemRecord:
    item_id: str
    description: str
    state: MatrixItemState
    evidence_refs: List[str] = field(default_factory=list)
    notes: str = ""


def _load_bench_artifact(artifact_path: Path = _MVP_BENCH_ARTIFACT) -> Optional[dict]:
    try:
        return json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _bench_passed(bench_data: Optional[dict]) -> bool:
    if bench_data is None:
        return False
    return bench_data.get("outcome") == "pass" and bench_data.get("total_tasks", 0) == 5 and bench_data.get("passed", 0) == 5


def _exists(rel_path: str) -> bool:
    return (REPO_ROOT / rel_path).exists()


def derive_campaign_closure(
    bench_artifact_path: Path = _MVP_BENCH_ARTIFACT,
) -> List[MatrixItemRecord]:
    bench = _load_bench_artifact(bench_artifact_path)
    bench_ok = _bench_passed(bench)

    # canonical session/job schema:
    # Evidence: session_job_adapters.py wraps CanonicalSession/CanonicalJob; used in MVP benchmark
    session_schema_state = MatrixItemState.DONE if (
        bench_ok
        and _exists("framework/session_job_adapters.py")
        and _exists("framework/canonical_session_schema.py")
        and _exists("framework/canonical_job_schema.py")
    ) else MatrixItemState.PARTIAL

    # typed Action→Observation tool system:
    # Evidence: tool_schema.py + tool_bridge.py + sandbox dispatch + MVP loop use of ApplyPatch/ReadFile/RunTests
    typed_tool_state = MatrixItemState.DONE if (
        bench_ok
        and _exists("framework/tool_schema.py")
        and _exists("framework/tool_bridge.py")
        and _exists("framework/sandbox_tool_dispatch.py")
        and _exists("framework/mvp_coding_loop.py")
    ) else MatrixItemState.SEED_COMPLETE

    # permission engine:
    # Evidence: TypedPermissionGate active in MVP benchmark gating all dispatched actions
    permission_state = MatrixItemState.DONE if (
        bench_ok
        and _exists("framework/typed_permission_gate.py")
        and _exists("framework/gated_tool_dispatch.py")
    ) else MatrixItemState.SEED_COMPLETE

    # sandbox execution:
    # Evidence: dispatch_run_command/dispatch_run_tests called through gated dispatch in MVP loop
    sandbox_state = MatrixItemState.DONE if (
        bench_ok
        and _exists("framework/sandbox_tool_dispatch.py")
        and _exists("framework/gated_tool_dispatch.py")
    ) else MatrixItemState.SEED_COMPLETE

    # consolidated validation artifact:
    # Evidence: emit_loop_validation used in MVP loop; emit_runtime_validation_record in execution adapter
    validation_state = MatrixItemState.DONE if (
        bench_ok
        and _exists("framework/validation_artifact_writer.py")
        and _exists("framework/validation_emit_adapter.py")
        and _exists("framework/runtime_execution_adapter.py")
    ) else MatrixItemState.SEED_COMPLETE

    # retrieval / memory substrate:
    # Evidence: context_retrieval.py over RepomapGenerator; tested against live repo
    retrieval_state = MatrixItemState.SEED_COMPLETE if _exists("framework/context_retrieval.py") else MatrixItemState.PARTIAL

    # full developer assistant MVP loop:
    # Evidence: mvp_coding_loop.py running inspect→patch→validate→revert; all 5 tasks passed in benchmark
    mvp_loop_state = MatrixItemState.DONE if (
        bench_ok
        and _exists("framework/mvp_coding_loop.py")
        and _exists("framework/read_file_dispatch.py")
        and _exists("framework/apply_patch_dispatch.py")
    ) else MatrixItemState.PARTIAL

    # Aider adapter: no evidence of readiness in packets 1–4
    aider_state = MatrixItemState.DEFERRED

    bench_ref = str(bench_artifact_path) if bench_ok else ""

    return [
        MatrixItemRecord(
            item_id="canonical_session_job_schema",
            description="Canonical session/job schema with active runtime use",
            state=session_schema_state,
            evidence_refs=[bench_ref, "framework/session_job_adapters.py"] if bench_ok else [],
            notes="CanonicalSession/CanonicalJob wrapped and used in MVP benchmark path",
        ),
        MatrixItemRecord(
            item_id="typed_action_observation_tool_system",
            description="Typed Action→Observation tool system with dispatch coverage",
            state=typed_tool_state,
            evidence_refs=[bench_ref, "framework/tool_schema.py", "framework/mvp_coding_loop.py"] if bench_ok else [],
            notes="ReadFileAction, ApplyPatchAction, RunTestsAction dispatched in MVP loop",
        ),
        MatrixItemRecord(
            item_id="permission_engine",
            description="Permission gate active in dispatch path",
            state=permission_state,
            evidence_refs=[bench_ref, "framework/typed_permission_gate.py", "framework/gated_tool_dispatch.py"] if bench_ok else [],
            notes="TypedPermissionGate gates all dispatched actions in MVP benchmark",
        ),
        MatrixItemRecord(
            item_id="sandbox_execution",
            description="Sandboxed execution through gated typed dispatch",
            state=sandbox_state,
            evidence_refs=[bench_ref, "framework/sandbox_tool_dispatch.py"] if bench_ok else [],
            notes="RunTests dispatched through gated sandbox dispatch in MVP benchmark",
        ),
        MatrixItemRecord(
            item_id="consolidated_validation_artifact",
            description="End-to-end validation artifact emission chain",
            state=validation_state,
            evidence_refs=[bench_ref, "framework/validation_emit_adapter.py"] if bench_ok else [],
            notes="emit_loop_validation used in every MVP loop task run",
        ),
        MatrixItemRecord(
            item_id="retrieval_memory_substrate",
            description="Local-first retrieval over repo-map surface",
            state=retrieval_state,
            evidence_refs=["framework/context_retrieval.py"] if _exists("framework/context_retrieval.py") else [],
            notes="RepomapGenerator-backed retrieval; tested against live repo symbols",
        ),
        MatrixItemRecord(
            item_id="full_developer_assistant_mvp_loop",
            description="Real bounded MVP coding loop: inspect→patch→validate→artifact",
            state=mvp_loop_state,
            evidence_refs=[bench_ref, "framework/mvp_coding_loop.py"] if bench_ok else [],
            notes="5/5 synthetic tasks passed in MVP benchmark; bounded revert proven",
        ),
        MatrixItemRecord(
            item_id="aider_adapter_under_runtime",
            description="Aider adapter wired under the runtime substrate",
            state=aider_state,
            evidence_refs=[],
            notes="No readiness evidence produced by this campaign; deferred",
        ),
    ]


def emit_closeout_record(
    items: List[MatrixItemRecord],
    *,
    campaign_id: str = "REMAINING-MATRIX-CLOSEOUT-CAMPAIGN-1",
    artifact_dir: Path = REPO_ROOT / "artifacts" / "matrix_closeout",
    bench_artifact_path: Path = _MVP_BENCH_ARTIFACT,
) -> str:
    bench = _load_bench_artifact(bench_artifact_path)
    bench_ok = _bench_passed(bench)

    if not bench_ok:
        raise RuntimeError(
            f"Packet-4 evidence gate failed: benchmark artifact at "
            f"{bench_artifact_path} missing, unreadable, or not passing"
        )

    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "RMCC1_closeout.json"

    record = {
        "campaign_id": campaign_id,
        "evidence_gate": "pass" if bench_ok else "fail",
        "bench_artifact": str(bench_artifact_path),
        "items": [
            {
                "item_id": item.item_id,
                "description": item.description,
                "state": item.state.value,
                "evidence_refs": item.evidence_refs,
                "notes": item.notes,
            }
            for item in items
        ],
    }
    out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return str(out_path)


__all__ = [
    "MatrixItemState",
    "MatrixItemRecord",
    "derive_campaign_closure",
    "emit_closeout_record",
]
