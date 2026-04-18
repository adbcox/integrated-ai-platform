#!/usr/bin/env python3
"""RECON-W1 governance authority reconciler.

Deterministic generator and checker for machine-readable governance JSON
artifacts in the ``governance/`` directory.

Modes:

  --write          (re)generate the governance JSON artifacts
  --check          validate existing artifacts against freshly computed state
  --fail-on-diff   exit non-zero on any diff (implied by --check; may be
                   combined with --write for a post-write re-check)

The script is bounded to the ``governance/`` directory. It only reads from the
working tree (no network). The ``generated_at`` timestamp is derived from the
committer date of ``as_of_commit`` so that ``--write`` followed by ``--check``
is idempotent even when HEAD advances beyond the pinned reconciliation
baseline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DIR = REPO_ROOT / "governance"

SCHEMA_VERSION = "1.0.0"
SCHEMA_VERSION_V2 = 2
AUTHORITY_OWNER = "governance/authority_adr_0001_source_of_truth.md"
AUTHORITY_OWNER_V2 = "governance"
BASELINE_COMMIT_V2 = "53ae4d4f177b176a7bffaa63988f63fa0efa622c"
# Legacy RECON-W1 artifacts keep their original as_of_commit so their
# deterministic ``generated_at`` is pinned to RECON-W1's baseline.
RECON_W1_BASELINE = "cc8e510261e7ec1a89c383db826f05c1ad32988d"

RUNTIME_PRIMITIVES: Sequence[str] = (
    "framework/worker_runtime.py",
    "framework/job_schema.py",
    "framework/session_schema.py",
    "framework/tool_system.py",
    "framework/workspace.py",
    "framework/permission_engine.py",
    "framework/sandbox.py",
)

ADOPTION_PRIMITIVES: Sequence[str] = (
    "worker_runtime",
    "tool_system",
    "workspace",
    "permission_engine",
    "sandbox",
)

TACTICAL_FAMILIES: Sequence[Dict[str, Any]] = (
    {
        "family_id": "eo",
        "family_prefixes": ["eo_"],
        "current_classification": "provisional_precursor",
        "canonical_phase_dependency": 2,
        "runtime_adoption_required": True,
        "regression_requirement": "named offline regression scenario",
        "next_reconciliation_action": (
            "classify precursor evidence and decide whether to ratify, pause, "
            "or retire before any new EO tactical package"
        ),
        "notes": "No files in framework/ match eo_ prefix at as_of_commit.",
    },
    {
        "family_id": "ed",
        "family_prefixes": ["ed_"],
        "current_classification": "provisional_precursor",
        "canonical_phase_dependency": 2,
        "runtime_adoption_required": True,
        "regression_requirement": "named offline regression scenario",
        "next_reconciliation_action": (
            "classify precursor evidence and decide whether to ratify, pause, "
            "or retire before any new ED tactical package"
        ),
        "notes": "No files in framework/ match ed_ prefix at as_of_commit.",
    },
    {
        "family_id": "mc",
        "family_prefixes": ["mc_", "multi_phase_"],
        "current_classification": "provisional_precursor",
        "canonical_phase_dependency": 4,
        "runtime_adoption_required": True,
        "regression_requirement": "named offline regression scenario covering "
        "multi-phase autonomy helpers",
        "next_reconciliation_action": (
            "evaluate multi_phase_* helper surface for runtime adoption and "
            "decide ratification vs. pause before any new MC tactical package"
        ),
        "notes": (
            "Evidence surface is the framework/multi_phase_* helper family "
            "committed through MC-W8/MC-W9."
        ),
    },
    {
        "family_id": "live_bridge",
        "family_prefixes": ["live_bridge_"],
        "current_classification": "provisional_precursor",
        "canonical_phase_dependency": 6,
        "runtime_adoption_required": True,
        "regression_requirement": "named offline regression scenario for "
        "live_bridge operations",
        "next_reconciliation_action": (
            "LOB-W3 is paused per ADR 0003; retain committed live_bridge "
            "code as provisional_precursor until reconciliation ratifies it"
        ),
        "notes": "See governance/authority_adr_0003_lob_w3_classification.md.",
    },
    {
        "family_id": "ort",
        "family_prefixes": ["ort_"],
        "current_classification": "provisional_precursor",
        "canonical_phase_dependency": 5,
        "runtime_adoption_required": True,
        "regression_requirement": "named offline regression scenario for ORT "
        "integration",
        "next_reconciliation_action": (
            "classify ORT precursor evidence and decide whether to ratify, "
            "pause, or retire before any new ORT tactical package"
        ),
        "notes": (
            "Committed ORT surface predates machine-readable authority; not "
            "yet mapped to a canonical phase."
        ),
    },
    {
        "family_id": "pgs",
        "family_prefixes": ["pgs_"],
        "current_classification": "provisional_precursor",
        "canonical_phase_dependency": 5,
        "runtime_adoption_required": True,
        "regression_requirement": "named offline regression scenario for PGS "
        "governance helpers",
        "next_reconciliation_action": (
            "classify PGS precursor evidence and decide whether to ratify, "
            "pause, or retire before any new PGS tactical package"
        ),
        "notes": (
            "Committed PGS surface predates machine-readable authority; not "
            "yet mapped to a canonical phase."
        ),
    },
)

CANONICAL_PHASES: Sequence[Dict[str, Any]] = (
    {
        "phase_id": 0,
        "phase_name": "governance_source_of_truth_reconciliation",
        "status": "open",
        "milestone_ref": None,
        "governance_evidence": [
            "governance/README.md",
            "governance/canonical_roadmap.json",
            "governance/current_phase.json",
            "governance/runtime_contract_version.json",
            "governance/phase_gate_status.json",
            "governance/runtime_adoption_report.json",
            "governance/tactical_family_classification.json",
            "governance/authority_adr_0001_source_of_truth.md",
            "governance/authority_adr_0002_tactical_family_classification.md",
            "governance/authority_adr_0003_lob_w3_classification.md",
        ],
        "code_anchors": [
            "bin/governance_reconcile.py",
            "tests/test_governance_reconcile.py",
        ],
        "blocking_reasons": [
            "machine-readable authority artifacts are being introduced by "
            "RECON-W1 and have not yet been ratified as closed",
        ],
        "notes": (
            "Phase 0 stays open until a subsequent reconciliation package "
            "ratifies these artifacts and mints a closure record."
        ),
    },
    {
        "phase_id": 1,
        "phase_name": "runtime_contract_foundation",
        "status": "materially_implemented_open_governance",
        "milestone_ref": None,
        "governance_evidence": [
            "governance/runtime_contract_version.json",
            "governance/phase_gate_status.json",
        ],
        "code_anchors": list(RUNTIME_PRIMITIVES),
        "blocking_reasons": [
            "runtime primitives exist in framework/ but no governance "
            "artifact has yet ratified the contract version",
        ],
        "notes": (
            "Runtime primitives are present and bound in "
            "runtime_contract_version.json; Phase 1 closes only when "
            "governance explicitly ratifies that contract version."
        ),
    },
    {
        "phase_id": 2,
        "phase_name": "inner_loop_autonomous_repair_and_shared_runtime_adoption",
        "status": "partially_adopted_open_governance",
        "milestone_ref": None,
        "governance_evidence": [
            "governance/runtime_adoption_report.json",
        ],
        "code_anchors": [
            "framework/worker_runtime.py",
            "bin/framework_control_plane.py",
        ],
        "blocking_reasons": [
            "tactical families have not been reclassified onto the shared "
            "runtime; adoption is partial and unratified",
        ],
        "notes": (
            "worker_runtime emits bounded retry, tool_permission_decision, "
            "and tool_observation traces; phase stays open on governance "
            "until adoption coverage is measured and ratified."
        ),
    },
    {
        "phase_id": 3,
        "phase_name": "codebase_understanding_retrieval_backed_runtime",
        "status": "provisionally_evidenced_unratified",
        "milestone_ref": None,
        "governance_evidence": [
            "governance/phase_gate_status.json",
        ],
        "code_anchors": [
            "framework/codebase_repomap.py",
            "bin/stage_rag4_plan_probe.py",
        ],
        "blocking_reasons": [
            "retrieval/repomap evidence exists in code but has not been "
            "ratified as phase advancement",
        ],
        "notes": (
            "Provisional evidence in stage_rag4 and codebase_repomap; no "
            "authority artifact currently ratifies Phase 3 advancement."
        ),
    },
    {
        "phase_id": 4,
        "phase_name": "autonomy_hardening_safety_policy_uplift",
        "status": "open",
        "milestone_ref": None,
        "governance_evidence": [],
        "code_anchors": [],
        "blocking_reasons": [
            "not canonically authorized until Phase 2/3 governance closure",
        ],
        "notes": (
            "No canonical work is authorized for Phase 4 at as_of_commit."
        ),
    },
    {
        "phase_id": 5,
        "phase_name": "qualification_promotion_learning_convergence",
        "status": "open",
        "milestone_ref": None,
        "governance_evidence": [],
        "code_anchors": [],
        "blocking_reasons": [
            "not canonically authorized until Phase 4 closure",
        ],
        "notes": (
            "No canonical work is authorized for Phase 5 at as_of_commit."
        ),
    },
    {
        "phase_id": 6,
        "phase_name": "controlled_expansion",
        "status": "open",
        "milestone_ref": None,
        "governance_evidence": [],
        "code_anchors": [],
        "blocking_reasons": [
            "not canonically authorized until Phase 5 closure",
        ],
        "notes": (
            "Only permitted after canonical authorization of prior phases."
        ),
    },
)

SUPERSEDES: Sequence[str] = (
    "docs/claude-code-roadmap.md (narrative only; not machine authority)",
    "docs/version15-master-roadmap.md (historical/legacy narrative only)",
    "docs/system_milestone_roadmap.md (out-of-scope for runtime authority)",
    "config/promotion_manifest.json (legacy tactical release authority; "
    "frozen pending explicit migration)",
)


def _run_git(args: Sequence[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _git_head() -> str:
    return _run_git(["rev-parse", "HEAD"])


def _git_commit_iso(commit: str) -> str:
    return _run_git(["log", "-1", "--format=%cI", commit])


def _git_ls_files() -> List[str]:
    out = _run_git(["ls-files"])
    return [line for line in out.splitlines() if line]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _line_count(path: Path) -> int:
    with open(path, "rb") as fh:
        return sum(1 for _ in fh)


def _determine_as_of_commit() -> str:
    current_phase_path = GOV_DIR / "current_phase.json"
    if current_phase_path.exists():
        try:
            data = json.loads(current_phase_path.read_text(encoding="utf-8"))
            value = data.get("as_of_commit")
            if isinstance(value, str) and value:
                return value
        except json.JSONDecodeError:
            pass
    return _git_head()


def _common_header(as_of_commit: str) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "authority_owner": AUTHORITY_OWNER,
        "generated_at": _git_commit_iso(as_of_commit),
        "supersedes": list(SUPERSEDES),
    }


def _primitive_records() -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for rel in RUNTIME_PRIMITIVES:
        abs_path = REPO_ROOT / rel
        if not abs_path.exists():
            raise RuntimeError(f"runtime primitive missing: {rel}")
        records.append(
            {
                "name": Path(rel).stem,
                "path": rel,
                "sha256": _sha256(abs_path),
                "line_count": _line_count(abs_path),
            }
        )
    return records


def _contract_version(primitive_records: Sequence[Dict[str, Any]]) -> str:
    fingerprint = hashlib.sha256()
    for record in primitive_records:
        fingerprint.update(record["path"].encode("utf-8"))
        fingerprint.update(b"\0")
        fingerprint.update(record["sha256"].encode("utf-8"))
        fingerprint.update(b"\n")
    return f"rt-1.0.0+{fingerprint.hexdigest()[:12]}"


_IMPORT_PATTERNS: Dict[str, re.Pattern[str]] = {
    name: re.compile(
        rf"^\s*(?:from\s+framework\.{name}\b|"
        rf"import\s+framework\.{name}\b|"
        rf"from\s+framework\s+import\s+[^\n]*\b{name}\b)"
    )
    for name in ADOPTION_PRIMITIVES
}


def _scan_adoption() -> Tuple[List[Dict[str, Any]], Dict[str, List[str]]]:
    """Return (direct_runtime_paths, per-primitive adopters)."""

    py_files = sorted(p for p in _git_ls_files() if p.endswith(".py"))
    direct_paths: List[Dict[str, Any]] = []
    per_primitive: Dict[str, List[str]] = {name: [] for name in ADOPTION_PRIMITIVES}

    for rel in py_files:
        abs_path = REPO_ROOT / rel
        if not abs_path.exists():
            continue
        try:
            text = abs_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matched: List[str] = []
        for name, pattern in _IMPORT_PATTERNS.items():
            if any(pattern.search(line) for line in text.splitlines()):
                matched.append(name)
        if matched:
            direct_paths.append(
                {
                    "path": rel,
                    "primitives_used": sorted(matched),
                }
            )
            for name in matched:
                per_primitive[name].append(rel)

    for name in per_primitive:
        per_primitive[name].sort()
    return direct_paths, per_primitive


def _family_for_path(rel: str) -> str:
    if not rel.startswith("framework/"):
        return ""
    stem = rel[len("framework/") :]
    for family in TACTICAL_FAMILIES:
        for prefix in family["family_prefixes"]:
            if stem.startswith(prefix):
                return family["family_id"]
    return ""


def _tactical_family_adoption(
    direct_paths: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    py_files = [p for p in _git_ls_files() if p.endswith(".py")]
    totals = {family["family_id"]: 0 for family in TACTICAL_FAMILIES}
    for rel in py_files:
        fam = _family_for_path(rel)
        if fam:
            totals[fam] += 1

    adopters_by_family: Dict[str, List[str]] = {
        family["family_id"]: [] for family in TACTICAL_FAMILIES
    }
    for record in direct_paths:
        fam = _family_for_path(record["path"])
        if fam:
            adopters_by_family[fam].append(record["path"])

    adoption: List[Dict[str, Any]] = []
    non_adopting: List[str] = []
    for family in TACTICAL_FAMILIES:
        fid = family["family_id"]
        files = sorted(adopters_by_family[fid])
        entry = {
            "family_id": fid,
            "total_family_files": totals[fid],
            "adopting_files": len(files),
            "adopting_paths": files,
            "classification": family["current_classification"],
        }
        adoption.append(entry)
        if totals[fid] > 0 and not files:
            non_adopting.append(fid)
    return adoption, non_adopting


def build_canonical_roadmap(as_of_commit: str) -> Dict[str, Any]:
    header = _common_header(as_of_commit)
    phases = []
    for phase in CANONICAL_PHASES:
        phases.append(
            {
                "phase_id": phase["phase_id"],
                "phase_name": phase["phase_name"],
                "status": phase["status"],
                "milestone_ref": phase["milestone_ref"],
                "code_anchors": list(phase["code_anchors"]),
                "governance_evidence": list(phase["governance_evidence"]),
                "blocking_reasons": list(phase["blocking_reasons"]),
                "notes": phase["notes"],
            }
        )
    return {**header, "phases": phases}


def build_current_phase(as_of_commit: str) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_V2,
        "authority_owner": AUTHORITY_OWNER_V2,
        "generated_at": _git_commit_iso(BASELINE_COMMIT_V2),
        "supersedes": list(SUPERSEDES),
        "baseline_commit": BASELINE_COMMIT_V2,
        "as_of_commit": BASELINE_COMMIT_V2,
        "current_phase_id": 2,
        "current_phase_name": "Phase 2",
        "current_phase_status": "adopted_partial",
        "phase0_status": "closed_ratified",
        "phase1_status": "closed_ratified",
        "phase2_status": "adopted_partial",
        "next_allowed_package_class": "ratification_only",
        "blocked_package_classes": [
            "canonical_phase_advancement",
            "capability_session",
            "feature_expansion",
            "tactical_family_extension",
        ],
        "blocked_tactical_families": [
            family["family_id"] for family in TACTICAL_FAMILIES
        ],
        "ratified_by_adrs": [
            "governance/authority_adr_0004_phase1_closure.md",
            "governance/authority_adr_0005_phase2_partial_adoption.md",
            "governance/authority_adr_0006_tactical_unlock_criteria.md",
            "governance/authority_adr_0007_next_class_ratification_only.md",
        ],
        "notes": (
            "Post-RECON-W2: Phase 0 closed_ratified, Phase 1 closed_ratified, "
            "Phase 2 adopted_partial; next allowed package class is "
            "ratification_only. See ADR 0005 — Phase 2 is explicitly NOT closed."
        ),
    }


def build_runtime_contract_version(
    as_of_commit: str,
    primitive_records: Sequence[Dict[str, Any]],
    direct_paths: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    header = _common_header(as_of_commit)
    return {
        **header,
        "contract_version": _contract_version(primitive_records),
        "primitives": list(primitive_records),
        "observed_adoption_paths": [record["path"] for record in direct_paths],
        "notes": (
            "contract_version fingerprint derives from the sha256 of each "
            "primitive; any primitive change advances the contract version."
        ),
    }


_RATIFIED_OVERRIDES = {
    0: {
        "classification": "closed_ratified",
        "blocking_reason_if_open": None,
        "ratified_by_adr": "governance/authority_adr_0004_phase1_closure.md",
    },
    1: {
        "classification": "closed_ratified",
        "blocking_reason_if_open": None,
        "ratified_by_adr": "governance/authority_adr_0004_phase1_closure.md",
    },
    2: {
        "classification": "adopted_partial",
        "blocking_reason_if_open": (
            "tactical families not reclassified onto the shared runtime; "
            "real-capability evidence not yet captured"
        ),
        "ratified_by_adr": "governance/authority_adr_0005_phase2_partial_adoption.md",
    },
}


def build_phase_gate_status(as_of_commit: str) -> Dict[str, Any]:
    gates: List[Dict[str, Any]] = []
    for phase in CANONICAL_PHASES:
        entry: Dict[str, Any] = {
            "phase_id": phase["phase_id"],
            "phase_name": phase["phase_name"],
            "code_evidence": list(phase["code_anchors"]),
            "governance_evidence": list(phase["governance_evidence"]),
            "classification": phase["status"],
            "blocking_reason_if_open": (
                phase["blocking_reasons"][0]
                if phase["blocking_reasons"]
                else None
            ),
            "notes": phase["notes"],
        }
        override = _RATIFIED_OVERRIDES.get(phase["phase_id"])
        if override:
            entry["classification"] = override["classification"]
            entry["blocking_reason_if_open"] = override["blocking_reason_if_open"]
            entry["ratified_by_adr"] = override["ratified_by_adr"]
        gates.append(entry)
    return {
        "schema_version": SCHEMA_VERSION_V2,
        "authority_owner": AUTHORITY_OWNER_V2,
        "generated_at": _git_commit_iso(BASELINE_COMMIT_V2),
        "supersedes": list(SUPERSEDES),
        "baseline_commit": BASELINE_COMMIT_V2,
        "gates": gates,
        "followups": [
            "promotion/__init__.py reconciliation skipped by RECON-W1 per "
            "packet guidance; revisit when promotion manifest migration is "
            "explicitly authorized.",
        ],
    }


def build_runtime_adoption_report(
    as_of_commit: str,
    direct_paths: Sequence[Dict[str, Any]],
    tactical_family_adoption: Sequence[Dict[str, Any]],
    non_adopting: Sequence[str],
) -> Dict[str, Any]:
    header = _common_header(as_of_commit)
    summary = {
        "direct_runtime_paths_count": len(direct_paths),
        "primitives_measured": list(ADOPTION_PRIMITIVES),
        "tactical_families_measured": [
            family["family_id"] for family in TACTICAL_FAMILIES
        ],
    }
    return {
        **header,
        "direct_runtime_paths": list(direct_paths),
        "tactical_family_adoption": list(tactical_family_adoption),
        "adoption_summary": summary,
        "non_adopting_families": list(non_adopting),
        "notes": (
            "Adoption is measured by static import of framework.{worker_runtime"
            ",tool_system,workspace,permission_engine,sandbox}; dynamic use "
            "via plugin registries is not counted."
        ),
    }


def build_tactical_family_classification(as_of_commit: str) -> Dict[str, Any]:
    header = _common_header(as_of_commit)
    families = []
    for family in TACTICAL_FAMILIES:
        families.append(
            {
                "family_id": family["family_id"],
                "family_prefixes": list(family["family_prefixes"]),
                "current_classification": family["current_classification"],
                "canonical_phase_dependency": family["canonical_phase_dependency"],
                "runtime_adoption_required": family["runtime_adoption_required"],
                "regression_requirement": family["regression_requirement"],
                "next_reconciliation_action": family["next_reconciliation_action"],
                "notes": family["notes"],
            }
        )
    return {**header, "families": families}


ARTIFACT_BUILDERS = (
    "canonical_roadmap.json",
    "current_phase.json",
    "runtime_contract_version.json",
    "phase_gate_status.json",
    "runtime_adoption_report.json",
    "tactical_family_classification.json",
)


def build_all(as_of_commit: str) -> Dict[str, Dict[str, Any]]:
    primitive_records = _primitive_records()
    direct_paths, _ = _scan_adoption()
    family_adoption, non_adopting = _tactical_family_adoption(direct_paths)
    # Legacy RECON-W1 artifacts are pinned to the RECON-W1 baseline so their
    # deterministic ``generated_at`` does not drift when a later packet lands.
    legacy_commit = RECON_W1_BASELINE
    return {
        "canonical_roadmap.json": build_canonical_roadmap(legacy_commit),
        "current_phase.json": build_current_phase(as_of_commit),
        "runtime_contract_version.json": build_runtime_contract_version(
            legacy_commit, primitive_records, direct_paths
        ),
        "phase_gate_status.json": build_phase_gate_status(as_of_commit),
        "runtime_adoption_report.json": build_runtime_adoption_report(
            legacy_commit, direct_paths, family_adoption, non_adopting
        ),
        "tactical_family_classification.json": build_tactical_family_classification(
            legacy_commit
        ),
    }


def _serialize(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


REQUIRED_METADATA_KEYS = (
    "schema_version",
    "authority_owner",
    "generated_at",
    "supersedes",
)


def _validate_schema(payload: Dict[str, Any], name: str) -> List[str]:
    errors: List[str] = []
    for key in REQUIRED_METADATA_KEYS:
        if key not in payload:
            errors.append(f"{name}: missing required key {key!r}")
    if name == "canonical_roadmap.json":
        phases = payload.get("phases", [])
        ids = sorted(p.get("phase_id") for p in phases)
        if ids != list(range(0, 7)):
            errors.append(
                f"canonical_roadmap.json: phases must be exactly 0..6, got {ids}"
            )
    if name == "current_phase.json":
        if payload.get("next_allowed_package_class") != "ratification_only":
            errors.append(
                "current_phase.json: next_allowed_package_class must be "
                "'ratification_only' after RECON-W2"
            )
        if "as_of_commit" not in payload:
            errors.append("current_phase.json: missing 'as_of_commit'")
        if "baseline_commit" not in payload:
            errors.append("current_phase.json: missing 'baseline_commit'")
    if name == "tactical_family_classification.json":
        fids = {f.get("family_id") for f in payload.get("families", [])}
        required = {"eo", "ed", "mc", "live_bridge", "ort", "pgs"}
        if not required.issubset(fids):
            errors.append(
                "tactical_family_classification.json: must cover eo/ed/mc/"
                "live_bridge/ort/pgs"
            )
    return errors


def cmd_write() -> int:
    as_of_commit = _determine_as_of_commit()
    GOV_DIR.mkdir(parents=True, exist_ok=True)
    payloads = build_all(as_of_commit)
    errors: List[str] = []
    for name, payload in payloads.items():
        errors.extend(_validate_schema(payload, name))
    if errors:
        for err in errors:
            print(f"SCHEMA ERROR: {err}", file=sys.stderr)
        return 2
    for name, payload in payloads.items():
        (GOV_DIR / name).write_text(_serialize(payload), encoding="utf-8")
    return 0


def cmd_check(fail_on_diff: bool = True) -> int:
    as_of_commit = _determine_as_of_commit()
    payloads = build_all(as_of_commit)
    errors: List[str] = []
    for name, payload in payloads.items():
        errors.extend(_validate_schema(payload, name))
    if errors:
        for err in errors:
            print(f"SCHEMA ERROR: {err}", file=sys.stderr)
        return 2
    diff_found = False
    for name, payload in payloads.items():
        expected = _serialize(payload)
        path = GOV_DIR / name
        if not path.exists():
            print(f"MISSING: {path}", file=sys.stderr)
            diff_found = True
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            print(f"DIFF: {path}", file=sys.stderr)
            diff_found = True
    if diff_found and fail_on_diff:
        return 3
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="RECON-W1 governance authority reconciler",
    )
    parser.add_argument("--write", action="store_true", help="regenerate artifacts")
    parser.add_argument("--check", action="store_true", help="validate artifacts")
    parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        help="exit non-zero on any diff against freshly computed state",
    )
    args = parser.parse_args(argv)

    if not (args.write or args.check or args.fail_on_diff):
        parser.error("one of --write, --check, or --fail-on-diff is required")

    if args.write:
        rc = cmd_write()
        if rc != 0:
            return rc
        if args.fail_on_diff or args.check:
            return cmd_check(fail_on_diff=True)
        return 0
    return cmd_check(fail_on_diff=True)


if __name__ == "__main__":
    sys.exit(main())
