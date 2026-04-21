#!/usr/bin/env python3
"""P0-01: Produce machine-readable authority-surface inventory and conflict report."""
from __future__ import annotations

import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "governance"

# Required input docs — must be readable before the inventory is considered valid
REQUIRED_INPUT_DOC_PATHS = [
    Path("docs/authority_inputs/revised_target_architecture_handoff_v4.docx"),
    Path("docs/authority_inputs/revised_target_architecture_handoff_v7.docx"),
    Path("docs/authority_inputs/control_window_architecture_adoption_packet.md"),
]

# Baseline governance authority surfaces (always inventoried from on-disk governance/ state)
_GOVERNANCE_SURFACE_DEFS = [
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
        "description": "Per-phase gate classifications and blocking reasons",
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


def _read_docx_text(path: Path) -> str:
    """Extract plain text from a .docx ZIP/XML file without python-docx."""
    try:
        with zipfile.ZipFile(path, "r") as zf:
            xml = zf.read("word/document.xml").decode("utf-8")
        # Extract text nodes from w:t elements
        texts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml, re.DOTALL)
        return "\n".join(t.strip() for t in texts if t.strip())
    except Exception as exc:
        return f"[read_error: {exc}]"


def _read_md_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        return f"[read_error: {exc}]"


def _check_and_read_input_docs() -> tuple[list[dict], bool]:
    """Return (doc_records, all_readable)."""
    records = []
    all_readable = True
    for rel_path in REQUIRED_INPUT_DOC_PATHS:
        abs_path = REPO_ROOT / rel_path
        exists = abs_path.exists()
        readable = False
        text_excerpt = None
        surface_type = None

        if exists:
            if rel_path.suffix == ".docx":
                surface_type = "authority_handoff_docx"
                text = _read_docx_text(abs_path)
                readable = not text.startswith("[read_error")
                text_excerpt = text[:300] if readable else text
            elif rel_path.suffix == ".md":
                surface_type = "architecture_adoption_packet_md"
                text = _read_md_text(abs_path)
                readable = len(text) > 0
                text_excerpt = text[:300]
        else:
            all_readable = False

        if not readable:
            all_readable = False

        records.append({
            "doc": rel_path.name,
            "path": str(rel_path),
            "exists": exists,
            "readable": readable,
            "surface_type": surface_type,
            "text_excerpt": text_excerpt,
        })
    return records, all_readable


def _build_input_doc_surfaces(doc_records: list[dict]) -> list[dict]:
    """Produce authority_surface entries for each readable input doc."""
    surface_map = {
        "revised_target_architecture_handoff_v4.docx": {
            "surface_id": "AS-10-HANDOFF-V4",
            "label": "revised_target_architecture_handoff_v4",
            "description": "Revised target architecture handoff document version 4 — authority surfaces declared in V4 (superseded by V7)",
            "authority_owner": "docs/authority_inputs/revised_target_architecture_handoff_v4.docx",
            "supersedes": [],
        },
        "revised_target_architecture_handoff_v7.docx": {
            "surface_id": "AS-11-HANDOFF-V7",
            "label": "revised_target_architecture_handoff_v7",
            "description": "Revised target architecture handoff document version 7 — authoritative authority surface declarations (supersedes V4)",
            "authority_owner": "docs/authority_inputs/revised_target_architecture_handoff_v7.docx",
            "supersedes": ["docs/authority_inputs/revised_target_architecture_handoff_v4.docx"],
        },
        "control_window_architecture_adoption_packet.md": {
            "surface_id": "AS-12-ADOPTION-PACKET",
            "label": "control_window_architecture_adoption_packet",
            "description": "Control window architecture adoption packet — declared authority order and acknowledged conflicts",
            "authority_owner": "docs/authority_inputs/control_window_architecture_adoption_packet.md",
            "supersedes": [],
        },
    }
    surfaces = []
    for rec in doc_records:
        defn = surface_map.get(rec["doc"])
        if defn and rec["readable"]:
            surfaces.append({
                **defn,
                "primary_file": rec["path"],
                "surface_type": rec["surface_type"],
                "on_disk": rec["exists"],
                "readable": rec["readable"],
                "text_excerpt": rec["text_excerpt"],
            })
    return surfaces


def _detect_conflicts(governance_surfaces: list[dict], input_doc_surfaces: list[dict]) -> list[dict]:
    conflicts = []

    current_phase_data = _read_json_safe(REPO_ROOT / "governance" / "current_phase.json")
    next_class_data = _read_json_safe(REPO_ROOT / "governance" / "next_package_class.json")
    phase_gate_data = _read_json_safe(REPO_ROOT / "governance" / "phase_gate_status.json")

    # CONF-01: phase numbering mismatch between current_phase and next_package_class
    if current_phase_data and next_class_data:
        reported_phase = current_phase_data.get("current_phase_id")
        allowed_class = next_class_data.get("current_allowed_class")
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
                "corroborated_by_input_docs": ["AS-11-HANDOFF-V7", "AS-12-ADOPTION-PACKET"],
                "severity": "high",
            })

    # CONF-02: gate ordering — Phase 0 open while Phase 7 closed
    if phase_gate_data:
        gates = {g["phase_id"]: g["classification"] for g in phase_gate_data.get("gates", [])}
        if gates.get(0) == "open" and gates.get(7) == "closed_ratified":
            conflicts.append({
                "conflict_id": "CONF-02",
                "conflict_type": "gate_ordering_inconsistency",
                "description": (
                    "phase_gate_status.json shows Phase 0 as 'open' while Phase 7 is 'closed_ratified'. "
                    "Phases 1-7 were closed without Phase 0 (governance_source_of_truth_reconciliation) "
                    "receiving a closure record."
                ),
                "surfaces_involved": ["AS-03-PHASE-GATE-STATUS"],
                "corroborated_by_input_docs": ["AS-11-HANDOFF-V7", "AS-12-ADOPTION-PACKET"],
                "severity": "high",
            })

    # CONF-03: legacy promotion_manifest coexistence
    if (REPO_ROOT / "config" / "promotion_manifest.json").exists():
        conflicts.append({
            "conflict_id": "CONF-03",
            "conflict_type": "legacy_authority_coexistence",
            "description": (
                "config/promotion_manifest.json (legacy tactical release authority) still exists on disk. "
                "Migration is explicitly deferred per phase_gate_status.json followup note."
            ),
            "surfaces_involved": ["AS-08-PROMOTION-MANIFEST-LEGACY", "AS-02-CURRENT-PHASE"],
            "corroborated_by_input_docs": ["AS-10-HANDOFF-V4", "AS-12-ADOPTION-PACKET"],
            "severity": "low",
        })

    # CONF-04 (from V7 handoff): LEDT transition not reflected in governance surfaces
    ledt_closeout = REPO_ROOT / "artifacts" / "expansion" / "LEDT" / "LEDT_closeout.json"
    if ledt_closeout.exists():
        ledt_data = _read_json_safe(ledt_closeout)
        if ledt_data and ledt_data.get("campaign_verdict") == "ledt_campaign_complete":
            conflicts.append({
                "conflict_id": "CONF-04",
                "conflict_type": "campaign_not_ratified_in_governance",
                "description": (
                    "LEDT campaign is complete (ledt_campaign_complete verdict in artifacts/) "
                    "but no governance authority surface reflects the local-exec-default transition. "
                    "As noted in handoff V7: LEDT modules are capability_session class and may be "
                    "ratified without tactical-family unlock."
                ),
                "surfaces_involved": [],
                "corroborated_by_input_docs": ["AS-11-HANDOFF-V7"],
                "severity": "medium",
            })

    return conflicts


def _compute_phase0_gate_status() -> dict:
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
            "surface_id": "AS-11-HANDOFF-V7",
            "label": "revised_target_architecture_handoff_v7",
            "rationale": "V7 handoff is the most current external authority declaration; defines the reconciliation order.",
        },
        {
            "rank": 2,
            "surface_id": "AS-01-CANONICAL-ROADMAP",
            "label": "canonical_roadmap",
            "rationale": "Defines the phase structure all other surfaces reference; must be verified first.",
        },
        {
            "rank": 3,
            "surface_id": "AS-03-PHASE-GATE-STATUS",
            "label": "phase_gate_status",
            "rationale": "Per-phase gate classifications are the reconciliation surface for Phase 0 closure.",
        },
        {
            "rank": 4,
            "surface_id": "AS-02-CURRENT-PHASE",
            "label": "current_phase",
            "rationale": "Should be advanced to reflect Phase 0 closure once closure evidence is ratified.",
        },
        {
            "rank": 5,
            "surface_id": "AS-04-NEXT-PACKAGE-CLASS",
            "label": "next_package_class",
            "rationale": "Allowed package class derives from current phase; update after current_phase is reconciled.",
        },
        {
            "rank": 6,
            "surface_id": "AS-05-RUNTIME-CONTRACT",
            "label": "runtime_contract_version",
            "rationale": "Phase 1 hardening requires explicit ratification; downstream of Phase 0 closure.",
        },
        {
            "rank": 7,
            "surface_id": "AS-06-TACTICAL-FAMILY-CLASSIFICATION",
            "label": "tactical_family_classification",
            "rationale": "Family unlock criteria depend on phase authority being correct; after Phase 0/1.",
        },
        {
            "rank": 8,
            "surface_id": "AS-07-SCHEMA-CONTRACT-REGISTRY",
            "label": "schema_contract_registry",
            "rationale": "Schema active/frozen classification is stable; update as new modules are adopted.",
        },
        {
            "rank": 9,
            "surface_id": "AS-08-PROMOTION-MANIFEST-LEGACY",
            "label": "promotion_manifest_legacy",
            "rationale": "Formally retire or migrate after Phase 0/1 authority surfaces are closed.",
        },
    ]


def build_inventory() -> dict:
    doc_records, all_readable = _check_and_read_input_docs()
    input_doc_surfaces = _build_input_doc_surfaces(doc_records)

    # Annotate governance surfaces with on-disk presence
    governance_surfaces = []
    for s in _GOVERNANCE_SURFACE_DEFS:
        path = REPO_ROOT / s["primary_file"]
        governance_surfaces.append({
            **s,
            "on_disk": path.exists(),
            "readable": path.exists() and path.stat().st_size > 0,
        })

    all_surfaces = governance_surfaces + input_doc_surfaces
    conflicts = _detect_conflicts(governance_surfaces, input_doc_surfaces)
    phase0_status = _compute_phase0_gate_status()
    authority_order = _recommended_authority_order()

    return {
        "inventory_id": "P0-01-AUTHORITY-SURFACE-INVENTORY-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "canonical_phase_source": "governance/canonical_roadmap.json",
        "input_doc_check": doc_records,
        "input_docs_all_readable": all_readable,
        "authority_surfaces": all_surfaces,
        "conflicts": conflicts,
        "recommended_authority_order": authority_order,
        "phase0_gate_status": phase0_status,
        "surface_count": len(all_surfaces),
        "governance_surface_count": len(governance_surfaces),
        "input_doc_surface_count": len(input_doc_surfaces),
        "conflict_count": len(conflicts),
        "high_severity_conflicts": sum(1 for c in conflicts if c.get("severity") == "high"),
    }


def main() -> None:
    doc_records, all_readable = _check_and_read_input_docs()
    for rec in doc_records:
        status = "OK" if rec["readable"] else ("MISSING" if not rec["exists"] else "UNREADABLE")
        print(f"  input_doc [{status}]: {rec['doc']}")

    if not all_readable:
        print("HARD STOP: not all required input docs are readable", file=sys.stderr)
        sys.exit(1)

    inventory = build_inventory()

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ARTIFACT_DIR / "phase_authority_inventory.json"
    out_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")

    print(f"inventory_id:          {inventory['inventory_id']}")
    print(f"surfaces_total:        {inventory['surface_count']} ({inventory['governance_surface_count']} governance + {inventory['input_doc_surface_count']} input-doc)")
    print(f"conflicts:             {inventory['conflict_count']} ({inventory['high_severity_conflicts']} high severity)")
    print(f"phase0_gate:           {inventory['phase0_gate_status']['gate_classification']}")
    print(f"input_docs_readable:   3/3")
    print(f"artifact:              {out_path}")


if __name__ == "__main__":
    main()
