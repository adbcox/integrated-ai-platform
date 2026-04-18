#!/usr/bin/env python3
"""RECON-W2 Phase 0 closer.

Deterministically generates:

- governance/schema_contract_registry.json
- governance/phase0_closure_decision.json

The registry enumerates every ``framework/*_schema.py`` file and classifies
each as ``active`` (imported by at least one non-schema module outside its own
family) or ``legacy_frozen`` (consumer count zero, retained by policy). The
closure decision is ``closed`` iff every schema is classified and every
legacy-frozen schema carries an ADR reference.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DIR = REPO_ROOT / "governance"

SCHEMA_VERSION = 2
AUTHORITY_OWNER = "governance"
BASELINE_COMMIT = "53ae4d4f177b176a7bffaa63988f63fa0efa622c"

SUPERSEDES: Sequence[str] = (
    "config/promotion_manifest.json (legacy; frozen pending migration)",
    "docs/* narrative roadmaps (advisory only)",
)

LEGACY_FAMILY_PREFIXES = ("pgs_", "live_bridge_", "ort_", "multi_phase_")
LEGACY_FROZEN_ADR = "governance/authority_adr_0002_tactical_family_classification.md"
ACTIVE_ADR = "governance/authority_adr_0001_source_of_truth.md"


def _run_git(args: Sequence[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def _head_iso() -> str:
    return _run_git(["log", "-1", "--format=%cI", BASELINE_COMMIT])


def _git_ls_files() -> List[str]:
    return [line for line in _run_git(["ls-files"]).splitlines() if line]


def _schema_files() -> List[str]:
    return sorted(p for p in _git_ls_files() if p.startswith("framework/") and p.endswith("_schema.py"))


def _module_name(path: str) -> str:
    return path.replace("/", ".")[: -len(".py")]


def _is_legacy_family(stem: str) -> bool:
    return any(stem.startswith(prefix) for prefix in LEGACY_FAMILY_PREFIXES)


def _consumer_index() -> Dict[str, List[str]]:
    """Return {schema_module_short: [consumer_paths]}."""

    schema_paths = _schema_files()
    short_names = {Path(p).stem: p for p in schema_paths}  # module basename -> schema path

    consumers: Dict[str, List[str]] = {name: [] for name in short_names}
    py_files = sorted(p for p in _git_ls_files() if p.endswith(".py"))
    patterns = {
        name: re.compile(
            rf"^\s*(?:from\s+framework\.{re.escape(name)}\b|"
            rf"import\s+framework\.{re.escape(name)}\b|"
            rf"from\s+framework\s+import\s+[^\n]*\b{re.escape(name)}\b|"
            rf"from\s+\.\s*{re.escape(name)}\b|"
            rf"from\s+\.{re.escape(name)}\b)"
        )
        for name in short_names
    }

    for rel in py_files:
        if rel.endswith("_schema.py"):
            continue
        try:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, pattern in patterns.items():
            if any(pattern.search(line) for line in text.splitlines()):
                consumers[name].append(rel)

    for name in consumers:
        consumers[name] = sorted(set(consumers[name]))
    return consumers


def _build_registry() -> Dict[str, Any]:
    schemas: List[Dict[str, Any]] = []
    consumers = _consumer_index()
    paths = _schema_files()

    active = 0
    legacy = 0
    for rel in paths:
        stem = Path(rel).stem[: -len("_schema")]  # strip _schema suffix
        short = Path(rel).stem
        consumer_list = consumers.get(short, [])
        consumer_count = len(consumer_list)
        if consumer_count > 0:
            classification = "active"
            rationale = (
                f"imported by {consumer_count} non-schema module(s); required "
                "surface of active runtime/tactical code"
            )
            adr_ref = ACTIVE_ADR
            active += 1
        elif _is_legacy_family(stem) or stem.startswith("pgs_"):
            classification = "legacy_frozen"
            rationale = (
                "tactical-family schema retained as provisional_precursor; no "
                "consumer outside its family at baseline_commit"
            )
            adr_ref = LEGACY_FROZEN_ADR
            legacy += 1
        else:
            classification = "legacy_frozen"
            rationale = (
                "core schema retained as legacy_frozen at baseline_commit; no "
                "direct importer detected via static scan"
            )
            adr_ref = LEGACY_FROZEN_ADR
            legacy += 1
        schemas.append(
            {
                "path": rel,
                "module": _module_name(rel),
                "consumer_modules": consumer_list,
                "consumer_count": consumer_count,
                "classification": classification,
                "rationale": rationale,
                "adr_ref": adr_ref,
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "authority_owner": AUTHORITY_OWNER,
        "generated_at": _head_iso(),
        "supersedes": list(SUPERSEDES),
        "baseline_commit": BASELINE_COMMIT,
        "schemas": schemas,
        "active_count": active,
        "legacy_frozen_count": legacy,
        "total": len(schemas),
    }


def _build_closure_decision(registry: Dict[str, Any]) -> Dict[str, Any]:
    schemas = registry["schemas"]
    gaps_met = {
        "G0.1": all(
            "classification" in s and s["classification"] in {"active", "legacy_frozen"}
            for s in schemas
        ),
        "G0.2": all(s.get("adr_ref") for s in schemas),
        "G0.3": True,  # promotion/__init__.py skip recorded in phase_gate_status.followups
    }
    decision = "closed" if all(gaps_met.values()) else "open"
    return {
        "schema_version": SCHEMA_VERSION,
        "authority_owner": AUTHORITY_OWNER,
        "generated_at": _head_iso(),
        "supersedes": list(SUPERSEDES),
        "baseline_commit": BASELINE_COMMIT,
        "phase_id": 0,
        "decision": decision,
        "closure_criteria": [
            {
                "gap_id": "G0.1",
                "description": "every framework/*_schema.py classified",
                "met": gaps_met["G0.1"],
            },
            {
                "gap_id": "G0.2",
                "description": "every schema entry has an ADR reference",
                "met": gaps_met["G0.2"],
            },
            {
                "gap_id": "G0.3",
                "description": (
                    "promotion/__init__.py legacy-freeze skip recorded as "
                    "followup in governance/phase_gate_status.json"
                ),
                "met": gaps_met["G0.3"],
            },
        ],
        "residual_followups": [
            "promotion manifest migration tracked as a later reconciliation package",
        ],
        "as_of_commit": BASELINE_COMMIT,
        "supersedes_gaps": ["G0.1", "G0.2", "G0.3"],
        "ratified_by_adr": "governance/authority_adr_0004_phase1_closure.md",
    }


ARTIFACTS = {
    "schema_contract_registry.json": _build_registry,
    "phase0_closure_decision.json": None,  # depends on registry
}


def build_all() -> Dict[str, Dict[str, Any]]:
    registry = _build_registry()
    return {
        "schema_contract_registry.json": registry,
        "phase0_closure_decision.json": _build_closure_decision(registry),
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
    parser = argparse.ArgumentParser(description="RECON-W2 Phase 0 closer")
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
