#!/usr/bin/env python3
"""P0-01: Produce machine-readable authority-surface inventory and conflict report."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "governance"

# Required input docs listed in the package spec
REQUIRED_INPUT_DOCS = [
    "revised_target_architecture_handoff_v4.docx",
    "revised_target_architecture_handoff_v7.docx",
    "control_window_architecture_adoption_packet.md",
]

# Authority surfaces to inventory
AUTHORITY_SURFACE_DEFS = [
    {
        "surface_id": "AS-01-CANONICAL-ROADMAP",
        "label": "canonical_roadmap",
        "description": "Machine-readable canonical phase definitions (Phases 0-7)",
        "primary_file": "governance/canonical_roadmap.json",
        "authority_owner": "governance/authority_adr_0001_source_of_truth.md",
        "surface_type": "machine_readable_json",
        "supersedes": [
            "docs/claude-code-roadmap.md",
            "docs/version15-master-roadmap.md",
            "docs/system_milestone_roadmap.md",
        ],
    },
    {
        "surface_id": "AS-02-CURRENT-PHASE",
        "label": "current_phase",
        "description": "Current canonical phase pointer, allowed package class, and tactical family lock state",
        "primary_file": "governance/current_phase.json",
        "authority_owner": "governance/authority_adr_0001_source_of_truth.md",
        "surface_type": "machine_readable_json",
        "supersedes": [
            "config/promotion_manifest.json",
            "docs/* narrative roadmaps",
        ],
    },
    {
        "surface_id": "AS-03-PHASE-GATE-STATUS",
        "label": "phase_gate_status",
        "description": "Per-phase gate classifications and blocking reasons (open / closed_ratified / materially_implemented_open_governance)",
        "primary_file": "governance/phase_gate_status.json",
        "authority_owner": "governance/authority_adr_0001_source_of_truth.md",
        "surface_type": "machine_readable_json",
        "supersedes": [
            "docs/claude-code-roadmap.md",
            "config/promotion_manifest.json",
        ],
    },
    {
        "surface_id": "AS-04-NEXT-PACKAGE-CLASS",
        "label": "next_package_class",
        "description": "Currently allowed package class and transition history",
        "primary_file": "governance/next_package_class.json",
        "authority_owner": "governance",
        "surface_type": "machine_readable_json",
        "supersedes": [
            "config/promotion_manifest.json",
            "docs/* narrative roadmaps",
        ],
    },
    {
        "surface_id": "AS-05-RUNTIME-CONTRACT",
        "label": "runtime_contract_version",
        "description": "Runtime primitive surface and contract version fingerprint",
        "primary_file": "governance/runtime_contract_version.json",
        "authority_owner": "governance/authority_adr_0001_source_of_truth.md",
        "surface_type": "machine_readable_json",
        "supersedes": [
            "framework/ module versions (code only; no governance ratification)",
        ],
    },
    {
        "surface_id": "AS-06-TACTICAL-FAMILY-CLASSIFICATION",
        "label": "tactical_family_classification",
        "description": "EO/ED/MC/LOB/ORT/PGS family lock state and unlock preconditions",
        "primary_file": "governance/tactical_family_classification.json",
        "authority_owner": "governance/authority_adr_0002_tactical_family_classification.md",
        "surface_type": "machine_readable_json",
        "supersedes": [],
    },
    {
        "surface_id": "AS-07-SCHEMA-CONTRACT-REGISTRY",
        "label": "schema_contract_registry",
        "description": "Active vs legacy_frozen schema classification for framework modules",
        "primary_file": "governance/schema_contract_registry.json",
        "authority_owner": "governance/authority_adr_0001_source_of_truth.md",
        "surface_type": "machine_readable_json",
        "supersedes": [],
    },
    {
        "surface_id": "AS-08-PROMOTION-MANIFEST-LEGACY",
        "label": "promotion_manifest_legacy",
        "description": "Legacy tactical release authority (frozen pending migration)",
        "primary_file": "config/promotion_manifest.json",
        "authority_owner": "config/promotion_manifest.json",
        "surface_type": "legacy_frozen_json",
        "supersedes": [],
    },
    {
        "surface_id": "AS-09-NARRATIVE-ROADMAP-DOCS",
        "label": "narrative_roadmap_docs",
        "description": "docs/claude-code-roadmap.md and related narrative roadmap documents (advisory only)",
        "primary_file": "docs/claude-code-roadmap.md",
        "authority_owner": "narrative_only",
        "surface_type": "narrative_advisory_md",
        "supersedes": [],
    },
]


def _read_json_safe(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _check_input_docs() -> list[dict]:
    results = []
    for doc in REQUIRED_INPUT_DOCS:
        candidates = list(REPO_ROOT.rglob(doc))
        results.append({
            "doc": doc,
            "found": len(candidates) > 0,
            "path": str(candidates[0].relative_to(REPO_ROOT)) if candidates else None,
        })
    return results


def _detect_conflicts(surfaces: list[dict]) -> list[dict]:
    conflicts = []

    current_phase_data = _read_json_safe(REPO_ROOT / "governance" / "current_phase.json")
    next_class_data = _read_json_safe(REPO_ROOT / "governance" / "next_package_class.json")
    phase_gate_data = _read_json_safe(REPO_ROOT / "governance" / "phase_gate_status.json")

    # Conflict 1: current_phase.json reports phase 0 open, but next_package_class
    # reflects Phase 7 closure (ratification_only), creating a phase-numbering gap
    if current_phase_data and next_class_data:
        reported_phase = current_phase_data.get("current_phase_id")
        allowed_class = next_class_data.get("current_allowed_class")
        # Phase 7 closure should be reflected in current_phase_id advancement
        if reported_phase == 0 and allowed_class == "ratification_only":
            conflicts.append({
                "conflict_id": "CONF-01",
                "conflict_type": "phase_numbering_mismatch",
                "description": (
                    "current_phase.json reports current_phase_id=0 (governance_source_of_truth_reconciliation, open) "
                    "but next_package_class.json reflects Phase 7 closure (current_allowed_class=ratification_only). "
                    "Phase 0 has been procedurally bypassed without a formal closure record."
                ),
                "surfaces_involved": ["AS-02-CURRENT-PHASE", "AS-04-NEXT-PACKAGE-CLASS"],
                "severity": "high",
            })

    # Conflict 2: phase_gate_status Phase 0 is still 'open' while phases 2-7 are closed_ratified
    if phase_gate_data:
        gates = {g["phase_id"]: g["classification"] for g in phase_gate_data.get("gates", [])}
        if gates.get(0) == "open" and gates.get(7) == "closed_ratified":
            conflicts.append({
                "conflict_id": "CONF-02",
                "conflict_type": "gate_ordering_inconsistency",
                "description": (
                    "phase_gate_status.json shows Phase 0 as 'open' while Phase 7 is 'closed_ratified'. "
                    "Phases 1 through 7 were closed without Phase 0 (governance_source_of_truth_reconciliation) "
                    "receiving a closure record, leaving an unresolved foundational gate."
                ),
                "surfaces_involved": ["AS-03-PHASE-GATE-STATUS"],
                "severity": "high",
            })

    # Conflict 3: Legacy promotion_manifest coexists with governance authority surfaces
    promo_path = REPO_ROOT / "config" / "promotion_manifest.json"
    if promo_path.exists():
        conflicts.append({
            "conflict_id": "CONF-03",
            "conflict_type": "legacy_authority_coexistence",
            "description": (
                "config/promotion_manifest.json (legacy tactical release authority) still exists on disk "
                "and has not been migrated or formally retired. It supersedes nothing but is itself "
                "superseded by governance/ JSON surfaces per ADR 0001. "
                "Migration is explicitly deferred per phase_gate_status.json followup note."
            ),
            "surfaces_involved": ["AS-08-PROMOTION-MANIFEST-LEGACY", "AS-02-CURRENT-PHASE"],
            "severity": "low",
        })

    # Conflict 4: Absent required input docs
    doc_results = _check_input_docs()
    absent_docs = [r["doc"] for r in doc_results if not r["found"]]
    if absent_docs:
        conflicts.append({
            "conflict_id": "CONF-04",
            "conflict_type": "required_input_docs_absent",
            "description": (
                f"Package P0-01 required {len(absent_docs)} input document(s) that are not present on disk: "
                + ", ".join(absent_docs)
                + ". Inventory was produced from existing on-disk governance/ state only. "
                "These docs may contain target-architecture claims that conflict with current governance state; "
                "their absence is itself a documentation gap."
            ),
            "surfaces_involved": [],
            "severity": "medium",
            "absent_docs": absent_docs,
        })

    return conflicts


def _compute_phase0_gate_status() -> dict:
    current_phase_data = _read_json_safe(REPO_ROOT / "governance" / "current_phase.json")
    phase_gate_data = _read_json_safe(REPO_ROOT / "governance" / "phase_gate_status.json")

    gate_class = "unknown"
    blocking_reason = None
    if phase_gate_data:
        for g in phase_gate_data.get("gates", []):
            if g["phase_id"] == 0:
                gate_class = g["classification"]
                blocking_reason = g.get("blocking_reason_if_open")
                break

    closure_record_exists = (REPO_ROOT / "governance" / "phase0_closure_decision.json").exists()

    return {
        "gate_classification": gate_class,
        "closure_record_on_disk": closure_record_exists,
        "blocking_reason": blocking_reason,
        "assessment": (
            "OPEN — Phase 0 has no closure record. "
            "The governance_source_of_truth_reconciliation phase requires an explicit closure package "
            "before the authority surface inventory is considered fully ratified."
        ),
    }


def _recommended_authority_order() -> list[dict]:
    return [
        {
            "rank": 1,
            "surface_id": "AS-01-CANONICAL-ROADMAP",
            "label": "canonical_roadmap",
            "rationale": "Defines the phase structure that all other surfaces reference; must be correct before any closure decision.",
        },
        {
            "rank": 2,
            "surface_id": "AS-03-PHASE-GATE-STATUS",
            "label": "phase_gate_status",
            "rationale": "Per-phase gate classifications are the reconciliation surface for Phase 0 closure; must reflect real state.",
        },
        {
            "rank": 3,
            "surface_id": "AS-02-CURRENT-PHASE",
            "label": "current_phase",
            "rationale": "Should be updated to reflect Phase 0 closure once closure evidence is ratified; currently stale.",
        },
        {
            "rank": 4,
            "surface_id": "AS-04-NEXT-PACKAGE-CLASS",
            "label": "next_package_class",
            "rationale": "Allowed package class derives from current phase; update after current_phase is reconciled.",
        },
        {
            "rank": 5,
            "surface_id": "AS-05-RUNTIME-CONTRACT",
            "label": "runtime_contract_version",
            "rationale": "Phase 1 hardening requires this surface to be explicitly ratified; downstream of Phase 0 closure.",
        },
        {
            "rank": 6,
            "surface_id": "AS-06-TACTICAL-FAMILY-CLASSIFICATION",
            "label": "tactical_family_classification",
            "rationale": "Family unlock criteria depend on phase authority being correct; reconcile after Phase 0/1 closure.",
        },
        {
            "rank": 7,
            "surface_id": "AS-07-SCHEMA-CONTRACT-REGISTRY",
            "label": "schema_contract_registry",
            "rationale": "Schema active/frozen classification is stable; update as new modules are adopted.",
        },
        {
            "rank": 8,
            "surface_id": "AS-08-PROMOTION-MANIFEST-LEGACY",
            "label": "promotion_manifest_legacy",
            "rationale": "Formally retire or migrate after Phase 0/1 authority surfaces are closed.",
        },
    ]


def build_inventory() -> dict:
    input_doc_status = _check_input_docs()
    conflicts = _detect_conflicts(AUTHORITY_SURFACE_DEFS)
    phase0_status = _compute_phase0_gate_status()
    authority_order = _recommended_authority_order()

    # Annotate each surface with on-disk presence
    surfaces = []
    for s in AUTHORITY_SURFACE_DEFS:
        path = REPO_ROOT / s["primary_file"]
        surfaces.append({
            **s,
            "on_disk": path.exists(),
            "readable": path.exists() and (path.stat().st_size > 0),
        })

    return {
        "inventory_id": "P0-01-AUTHORITY-SURFACE-INVENTORY-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "canonical_phase_source": "governance/canonical_roadmap.json",
        "input_doc_check": input_doc_status,
        "authority_surfaces": surfaces,
        "conflicts": conflicts,
        "recommended_authority_order": authority_order,
        "phase0_gate_status": phase0_status,
        "surface_count": len(surfaces),
        "conflict_count": len(conflicts),
        "high_severity_conflicts": sum(1 for c in conflicts if c.get("severity") == "high"),
    }


def main() -> None:
    inventory = build_inventory()

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ARTIFACT_DIR / "phase_authority_inventory.json"
    out_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")

    print(f"inventory_id:     {inventory['inventory_id']}")
    print(f"surfaces:         {inventory['surface_count']}")
    print(f"conflicts:        {inventory['conflict_count']} ({inventory['high_severity_conflicts']} high severity)")
    print(f"phase0_gate:      {inventory['phase0_gate_status']['gate_classification']}")
    print(f"input_docs_found: {sum(1 for d in inventory['input_doc_check'] if d['found'])}/{len(REQUIRED_INPUT_DOCS)}")
    print(f"artifact:         {out_path}")


if __name__ == "__main__":
    main()
