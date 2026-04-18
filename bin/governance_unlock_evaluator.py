#!/usr/bin/env python3
"""RECON-W2 tactical unlock evaluator.

Deterministically generates:

- governance/tactical_unlock_criteria.json
- governance/next_package_class.json

Every family in this packet remains ``locked``. The file encodes the
preconditions that a later reconciliation package must satisfy in order to
promote a family to ``eligible_for_review`` or ``unlocked``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DIR = REPO_ROOT / "governance"

SCHEMA_VERSION = 2
AUTHORITY_OWNER = "governance"
BASELINE_COMMIT = "53ae4d4f177b176a7bffaa63988f63fa0efa622c"

SUPERSEDES: Sequence[str] = (
    "config/promotion_manifest.json (legacy; frozen pending migration)",
    "docs/* narrative roadmaps (advisory only)",
)

FAMILIES: Sequence[Dict[str, Any]] = (
    {
        "family_id": "eo",
        "prefixes": ["eo_"],
        "unlock_preconditions": [
            "canonical phase authority permits EO work",
            "runtime-primitive adoption measured in runtime_adoption_report.json",
            "named offline regression scenario covers EO",
        ],
        "currently_met_preconditions": [],
        "notes": "no eo_* files at baseline_commit",
    },
    {
        "family_id": "ed",
        "prefixes": ["ed_"],
        "unlock_preconditions": [
            "canonical phase authority permits ED work",
            "runtime-primitive adoption measured in runtime_adoption_report.json",
            "named offline regression scenario covers ED",
        ],
        "currently_met_preconditions": [],
        "notes": "no ed_* files at baseline_commit",
    },
    {
        "family_id": "mc",
        "prefixes": ["mc_", "multi_phase_"],
        "unlock_preconditions": [
            "canonical phase 4 authority explicitly authorizes MC family",
            "runtime-primitive adoption measured for multi_phase_* helpers",
            "named offline regression scenario covers multi-phase autonomy",
        ],
        "currently_met_preconditions": [],
        "notes": "evidence surface is framework/multi_phase_*",
    },
    {
        "family_id": "live_bridge",
        "prefixes": ["live_bridge_"],
        "unlock_preconditions": [
            "ADR 0003 pause explicitly lifted",
            "canonical phase 6 authority permits LOB work",
            "runtime-primitive adoption measured for live_bridge_* helpers",
            "named offline regression scenario covers live_bridge operations",
        ],
        "currently_met_preconditions": [],
        "notes": "LOB-W3 remains paused under ADR 0003",
    },
    {
        "family_id": "ort",
        "prefixes": ["ort_"],
        "unlock_preconditions": [
            "canonical phase 5 authority permits ORT work",
            "runtime-primitive adoption measured for ort_* helpers",
            "named offline regression scenario covers ORT integration",
        ],
        "currently_met_preconditions": [],
        "notes": "ORT committed surface is provisional_precursor",
    },
    {
        "family_id": "pgs",
        "prefixes": ["pgs_"],
        "unlock_preconditions": [
            "canonical phase 5 authority permits PGS work",
            "runtime-primitive adoption measured for pgs_* helpers",
            "named offline regression scenario covers PGS governance helpers",
        ],
        "currently_met_preconditions": [],
        "notes": "PGS committed surface is provisional_precursor",
    },
)


def _run_git(args: Sequence[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def _head_iso() -> str:
    return _run_git(["log", "-1", "--format=%cI", BASELINE_COMMIT])


def _discover_prefixes() -> Dict[str, int]:
    files = [p for p in _run_git(["ls-files"]).splitlines() if p.startswith("framework/")]
    counts: Dict[str, int] = {}
    for family in FAMILIES:
        total = 0
        for prefix in family["prefixes"]:
            total += sum(1 for f in files if f[len("framework/"):].startswith(prefix))
        counts[family["family_id"]] = total
    return counts


def _build_unlock_criteria() -> Dict[str, Any]:
    counts = _discover_prefixes()
    families = []
    for family in FAMILIES:
        unlock_state = "locked"
        met = list(family["currently_met_preconditions"])
        review_required = True
        entry = {
            "family_id": family["family_id"],
            "prefixes": list(family["prefixes"]),
            "unlock_preconditions": list(family["unlock_preconditions"]),
            "currently_met_preconditions": met,
            "unlock_state": unlock_state,
            "review_packet_required": review_required,
            "notes": family["notes"],
            "total_family_files": counts[family["family_id"]],
        }
        if family["family_id"] == "live_bridge":
            entry["adr_ref"] = "governance/authority_adr_0003_lob_w3_classification.md"
        families.append(entry)
    return {
        "schema_version": SCHEMA_VERSION,
        "authority_owner": AUTHORITY_OWNER,
        "generated_at": _head_iso(),
        "supersedes": list(SUPERSEDES),
        "baseline_commit": BASELINE_COMMIT,
        "families": families,
        "ratified_by_adr": "governance/authority_adr_0006_tactical_unlock_criteria.md",
    }


def _build_next_package_class() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "authority_owner": AUTHORITY_OWNER,
        "generated_at": _head_iso(),
        "supersedes": list(SUPERSEDES),
        "baseline_commit": BASELINE_COMMIT,
        "current_allowed_class": "ratification_only",
        "transitions": [
            {
                "from": "ratification_only",
                "to": "capability_session",
                "gate": (
                    "Phase 2 closure evidence (real-capability measurement_session) "
                    "must be ratified by a later reconciliation package"
                ),
                "blocked_until": "phase2_adoption_decision.json decision == closed",
            },
            {
                "from": "ratification_only",
                "to": "tactical_review",
                "gate": (
                    "per-family unlock review packet that satisfies the "
                    "preconditions recorded in tactical_unlock_criteria.json"
                ),
                "blocked_until": "all tactical families remain locked at baseline_commit",
            },
        ],
        "justification": (
            "RECON-W2 closes Phase 0 and Phase 1 and records Phase 2 as "
            "adopted_partial. No tactical family is unlocked; the next "
            "allowed package class is therefore ratification_only."
        ),
        "ratified_by_adr": "governance/authority_adr_0007_next_class_ratification_only.md",
    }


def build_all() -> Dict[str, Dict[str, Any]]:
    return {
        "tactical_unlock_criteria.json": _build_unlock_criteria(),
        "next_package_class.json": _build_next_package_class(),
    }


def _serialize(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def cmd_write() -> int:
    GOV_DIR.mkdir(parents=True, exist_ok=True)
    for name, payload in build_all().items():
        (GOV_DIR / name).write_text(_serialize(payload), encoding="utf-8")
    return 0


def cmd_check() -> int:
    diff = False
    for name, payload in build_all().items():
        expected = _serialize(payload)
        path = GOV_DIR / name
        if not path.exists():
            print(f"MISSING: {path}", file=sys.stderr)
            diff = True
            continue
        if path.read_text(encoding="utf-8") != expected:
            print(f"DIFF: {path}", file=sys.stderr)
            diff = True
    return 3 if diff else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RECON-W2 unlock evaluator")
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
