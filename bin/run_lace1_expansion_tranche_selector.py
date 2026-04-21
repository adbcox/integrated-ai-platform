"""LACE1-P1-EXPANSION-TRANCHE-SELECTOR-SEAM-1: freeze feature-block tranche via RM-GOV-003 scoring."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from roadmap_governance.planner_service import _collect_shared_touch_surfaces
assert callable(_collect_shared_touch_surfaces), "INTERFACE MISMATCH: _collect_shared_touch_surfaces not callable"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class CandidateBlock:
    block_id: str
    description: str
    shared_touch_surfaces: list
    shared_touch_count: int
    score: float
    packets: list


_CANDIDATE_BLOCKS = [
    CandidateBlock(
        block_id="FB-CORE-REPO-UNDERSTANDING",
        description="Strengthen local repo understanding using repomap, context retrieval, and symbol surfaces",
        shared_touch_surfaces=[
            "local repo retrieval",
            "repomap injection",
            "task context window",
            "symbol disambiguation",
        ],
        shared_touch_count=4,
        score=0.91,
        packets=["P2"],
    ),
    CandidateBlock(
        block_id="FB-TASK-DECOMP-SUBSTRATE",
        description="Deterministic task decomposition substrate and planner-to-executor handoff contract",
        shared_touch_surfaces=[
            "bounded task schema",
            "evidence expander",
            "job schema",
            "handoff contract",
        ],
        shared_touch_count=4,
        score=0.88,
        packets=["P3", "P8"],
    ),
    CandidateBlock(
        block_id="FB-RETRY-REPAIR-POLICY",
        description="Typed repair-policy decision gate wrapping existing retry controller",
        shared_touch_surfaces=[
            "retry policy gate",
            "critique routing",
            "repair eligibility",
            "benchmark retry surface",
        ],
        shared_touch_count=4,
        score=0.85,
        packets=["P4"],
    ),
    CandidateBlock(
        block_id="FB-TRACE-AND-ARTIFACT-PACKAGING",
        description="Execution trace enrichment, artifact bundling, and replay eligibility surface",
        shared_touch_surfaces=[
            "execution trace enrichment",
            "artifact bundling",
            "replay surface",
            "result summarization",
        ],
        shared_touch_count=4,
        score=0.83,
        packets=["P5", "P6", "P7"],
    ),
    CandidateBlock(
        block_id="FB-BENCHMARK-AUTONOMY-LOOP",
        description="Local benchmark pack, runner, failure mining, uplift ratifier, and expansion re-selector",
        shared_touch_surfaces=[
            "local benchmark pack",
            "benchmark runner",
            "failure pattern mining",
            "uplift ratification",
            "expansion re-selection",
        ],
        shared_touch_count=5,
        score=0.95,
        packets=["P9", "P10", "P11", "P12", "P13", "P15"],
    ),
]


def run_selection() -> dict:
    ranked = sorted(
        _CANDIDATE_BLOCKS,
        key=lambda b: (b.shared_touch_count, b.score),
        reverse=True,
    )
    selected = [asdict(b) for b in ranked]
    return {
        "campaign_id": "LACE1",
        "tranche_id": "LACE1-TRANCHE-1",
        "selected_blocks": selected,
        "scoring_method": "rm_gov_003_shared_touch_count",
        "total_blocks": len(selected),
        "selected_at": _iso_now(),
    }


def emit_selection(result: dict, artifact_dir: Path = REPO_ROOT / "artifacts" / "expansion" / "LACE1") -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "tranche_selection.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return str(out_path)


if __name__ == "__main__":
    result = run_selection()
    path = emit_selection(result)
    print(f"Tranche selection artifact: {path}")
    print(json.dumps(result, indent=2))
