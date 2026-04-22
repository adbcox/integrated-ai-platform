#!/usr/bin/env python3
"""Project verified harvest output into actionable watchtower recommendation artifact."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--harvest",
        default="governance/verified_oss_capability_harvest_rm_intel_002.v1.yaml",
    )
    parser.add_argument(
        "--out",
        default="artifacts/governance/oss_watchtower_projection.json",
    )
    args = parser.parse_args()

    harvest_path = REPO_ROOT / args.harvest
    out_path = REPO_ROOT / args.out

    harvest = _load_yaml(harvest_path)
    candidates = harvest.get("candidates") or []

    projected: list[dict[str, Any]] = []
    for row in candidates:
        name = str(row.get("name") or "")
        rec = str(row.get("recommendation_class") or "watch")
        links = row.get("roadmap_linkage") or []
        projected.append(
            {
                "name": name,
                "recommendation_class": rec,
                "roadmap_linkage": links,
                "integration_role": row.get("category"),
                "compatibility_decision": row.get("compatibility_decision"),
                "rationale": {
                    "architecture_compatibility": row.get("architecture_compatibility"),
                    "duplication_risk": row.get("duplication_risk"),
                    "privacy_local_first_constraints": row.get("privacy_local_first_constraints"),
                    "architecture_drift_risk": row.get("architecture_drift_risk"),
                },
                "feeds": {
                    "rm_dev_005": "RM-DEV-005" in links,
                    "rm_dev_003": "RM-DEV-003" in links,
                    "rm_dev_002": "RM-DEV-002" in links,
                },
            }
        )

    grouped: dict[str, list[str]] = {key: [] for key in ["adopt-now", "evaluate", "watch", "reject"]}
    for row in projected:
        grouped.setdefault(row["recommendation_class"], []).append(row["name"])

    payload = {
        "schema_version": 1,
        "artifact_type": "oss_watchtower_projection",
        "generated_at": _iso_now(),
        "source_harvest": str(harvest_path.relative_to(REPO_ROOT)),
        "projection": projected,
        "grouped_recommendations": {k: sorted(v) for k, v in grouped.items()},
        "integrated_chain": {
            "rm_intel_002_to_rm_intel_001": True,
            "feeds_rm_dev_005": any(item["feeds"]["rm_dev_005"] for item in projected),
            "feeds_rm_dev_003": any(item["feeds"]["rm_dev_003"] for item in projected),
            "feeds_rm_dev_002": any(item["feeds"]["rm_dev_002"] for item in projected),
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"artifact={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
