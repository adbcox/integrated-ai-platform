"""Standalone emitter for the routing policy artifact."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.routing_policy_artifact import build_routing_policy_artifact, emit_routing_policy
from framework.routing_config import DEFAULT_ROUTING_CONFIG


def main() -> int:
    artifact_dir = REPO_ROOT / "artifacts" / "routing_policy"
    artifact = build_routing_policy_artifact(routing_config=DEFAULT_ROUTING_CONFIG)
    out_path = emit_routing_policy(artifact, artifact_dir=artifact_dir)
    data = json.loads(Path(out_path).read_text())
    print(f"\n{'='*50}")
    print(f"  Routing Policy Artifact")
    print(f"{'='*50}")
    print(f"  Current threshold : {data['current_threshold']}")
    print(f"  Overall signal    : {data['overall_signal']}")
    print(f"  Readiness verdict : {data['readiness_verdict']}")
    print(f"  Policy health     : {data['policy_health']}")
    print(f"  Artifact          : {out_path}")
    print(f"{'='*50}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
