#!/usr/bin/env python3
"""Run one integrated governed ops/home/intel/inventory expansion slice."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

from framework.integrated_ops_home_intel_inventory import (  # noqa: E402
    build_integrated_artifact,
    build_ops_queue,
    derive_home_actions,
    derive_intel_recommendations,
)
from procurement_evaluator import evaluate_bom  # noqa: E402
from runtime.runtime_executor import build_session_job  # noqa: E402

POLICY_PATH = REPO_ROOT / "governance" / "integrated_ops_home_intel_inventory_policy.v1.yaml"
WATCHTOWER_PATH = REPO_ROOT / "governance" / "oss_watchtower_candidates.v1.yaml"
CONTROL_WINDOW_PATH = REPO_ROOT / "artifacts" / "rm_ui005" / "control_window_state.json"
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "operations" / "integrated_ops_expansion_run.json"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _default_home_requests() -> list[dict]:
    return [
        {"domain": "lighting", "intent": "evening_scene", "target": "living-room"},
        {"domain": "climate", "intent": "pre_cool", "target": "bedroom"},
        {"domain": "safety", "intent": "night_lockdown", "target": "main-entry"},
    ]


def _default_bom() -> dict:
    return {
        "project_id": "home-edge-hub-v1",
        "components": [
            {
                "part_number": "ESP32-S3-WROOM-1-N8",
                "description": "Edge automation controller",
                "quantity": 2,
                "unit_cost": 4.5,
                "supplier": "Espressif",
                "lead_time_days": 5,
            },
            {
                "part_number": "SCD40",
                "description": "CO2 + temp sensor",
                "quantity": 4,
                "unit_cost": 8.2,
                "supplier": "Sensirion",
                "lead_time_days": 7,
            },
            {
                "part_number": "HLK-PM01",
                "description": "AC-DC power module",
                "quantity": 2,
                "unit_cost": 2.1,
                "supplier": "Hi-Link",
                "lead_time_days": 6,
            },
        ],
        "total_cost": 45.8,
    }


def run(output_path: Path) -> dict:
    policy = _read_yaml(POLICY_PATH)
    watchtower = _read_yaml(WATCHTOWER_PATH)
    control_window_state = _read_json(CONTROL_WINDOW_PATH)

    runtime_session = build_session_job(
        objective="Integrated ops/home/intel/inventory governed expansion",
        task_id="RM-OPS-006+RM-HOME-005+RM-INTEL-003+RM-INV-003",
        allowed_files=["framework/**", "bin/**", "governance/**", "artifacts/**", "docs/roadmap/**", "tests/**"],
        forbidden_files=[".github/**", "node_modules/**", "venv/**"],
    )

    home_actions = derive_home_actions(
        _default_home_requests(),
        policy.get("home_operating_semantics", {}),
    )

    intel_semantics = policy.get("intel_operating_semantics", {})
    intel_recommendations = derive_intel_recommendations(
        watchtower.get("candidates", []),
        intel_semantics.get("recommendation_class_priority", {}),
        set(intel_semantics.get("exclude_classes", [])),
        int(intel_semantics.get("max_recommendations_per_run", 5)),
    )

    procurement_result = evaluate_bom(_default_bom())
    ops_queue = build_ops_queue(home_actions, intel_recommendations, procurement_result)

    artifact = build_integrated_artifact(
        runtime_session=runtime_session,
        control_window_state=control_window_state,
        home_actions=home_actions,
        intel_recommendations=intel_recommendations,
        procurement_result=procurement_result,
        ops_queue=ops_queue,
        policy_path=str(POLICY_PATH.relative_to(REPO_ROOT)),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(description="Run integrated ops/home/intel/inventory expansion")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path for integrated artifact output",
    )
    args = parser.parse_args()

    out = Path(args.output)
    if not out.is_absolute():
        out = REPO_ROOT / out

    artifact = run(out)
    print(json.dumps({"status": "ok", "output": str(out), "queue_size": artifact["ops_execution"]["queue_size"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
