#!/usr/bin/env python3
"""Refresh/compare verified harvest vs watchtower and emit machine-readable delta."""
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


def _norm_links(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--harvest",
        default="governance/verified_oss_capability_harvest_rm_intel_002.v1.yaml",
    )
    parser.add_argument(
        "--watchtower",
        default="governance/oss_watchtower_candidates.v1.yaml",
    )
    parser.add_argument(
        "--out",
        default="artifacts/governance/oss_refresh_delta.json",
    )
    args = parser.parse_args()

    harvest_path = REPO_ROOT / args.harvest
    watchtower_path = REPO_ROOT / args.watchtower
    out_path = REPO_ROOT / args.out

    harvest = _load_yaml(harvest_path)
    watchtower = _load_yaml(watchtower_path)

    harvest_candidates = {str(row.get("name")): row for row in (harvest.get("candidates") or [])}
    watchtower_candidates = {str(row.get("name")): row for row in (watchtower.get("candidates") or [])}

    harvest_names = set(harvest_candidates)
    watchtower_names = set(watchtower_candidates)

    added_to_watchtower = sorted(harvest_names - watchtower_names)
    missing_from_watchtower = sorted(harvest_names - watchtower_names)
    missing_from_harvest = sorted(watchtower_names - harvest_names)

    changed: list[dict[str, Any]] = []
    unchanged: list[str] = []
    for name in sorted(harvest_names & watchtower_names):
        hc = harvest_candidates[name]
        wc = watchtower_candidates[name]
        rec_h = str(hc.get("recommendation_class") or "")
        rec_w = str(wc.get("recommendation_class") or "")
        links_h = sorted(set(_norm_links(hc.get("roadmap_linkage"))))
        links_w = sorted(set(_norm_links(wc.get("roadmap_linkage"))))
        link_gaps = [link for link in links_h if link not in links_w]
        if rec_h != rec_w or link_gaps:
            changed.append(
                {
                    "name": name,
                    "recommendation_class": {"harvest": rec_h, "watchtower": rec_w},
                    "missing_watchtower_links": link_gaps,
                }
            )
        else:
            unchanged.append(name)

    recommendation_totals: dict[str, int] = {}
    for row in harvest_candidates.values():
        rec = str(row.get("recommendation_class") or "unknown")
        recommendation_totals[rec] = recommendation_totals.get(rec, 0) + 1

    payload = {
        "schema_version": 1,
        "artifact_type": "oss_refresh_delta",
        "generated_at": _iso_now(),
        "source": {
            "harvest": str(harvest_path.relative_to(REPO_ROOT)),
            "watchtower": str(watchtower_path.relative_to(REPO_ROOT)),
        },
        "summary": {
            "harvest_candidate_count": len(harvest_candidates),
            "watchtower_candidate_count": len(watchtower_candidates),
            "changed_count": len(changed),
            "unchanged_count": len(unchanged),
            "missing_from_watchtower_count": len(missing_from_watchtower),
            "missing_from_harvest_count": len(missing_from_harvest),
            "recommendation_totals": recommendation_totals,
        },
        "delta": {
            "changed": changed,
            "missing_from_watchtower": missing_from_watchtower,
            "missing_from_harvest": missing_from_harvest,
            "added_to_watchtower_needed": added_to_watchtower,
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"artifact={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
