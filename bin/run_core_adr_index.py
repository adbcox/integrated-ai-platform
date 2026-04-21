#!/usr/bin/env python3
"""P0-02: Build and emit the core ADR index artifact."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_INPUT_PATHS = [
    REPO_ROOT / "docs/authority_inputs/revised_target_architecture_handoff_v4.docx",
    REPO_ROOT / "docs/authority_inputs/revised_target_architecture_handoff_v7.docx",
    REPO_ROOT / "docs/authority_inputs/control_window_architecture_adoption_packet.md",
    REPO_ROOT / "artifacts/governance/phase_authority_inventory.json",
]

ADR_FILES = [
    ("ADR-0001", REPO_ROOT / "docs/adr/ADR-0001-canonical-session-job-schema.md"),
    ("ADR-0002", REPO_ROOT / "docs/adr/ADR-0002-typed-tool-system.md"),
    ("ADR-0003", REPO_ROOT / "docs/adr/ADR-0003-workspace-contract.md"),
    ("ADR-0004", REPO_ROOT / "docs/adr/ADR-0004-inference-gateway.md"),
    ("ADR-0005", REPO_ROOT / "docs/adr/ADR-0005-permission-model.md"),
    ("ADR-0006", REPO_ROOT / "docs/adr/ADR-0006-artifact-bundle.md"),
    ("ADR-0007", REPO_ROOT / "docs/adr/ADR-0007-autonomy-scorecard.md"),
]

ARTIFACT_PATH = REPO_ROOT / "artifacts/governance/core_adr_index.json"

_STATUS_RE = re.compile(r"\*\*Status\*\*:\s*(\S+)", re.IGNORECASE)
_TITLE_RE = re.compile(r"^#\s+(.+)", re.MULTILINE)
_PHASE_RE = re.compile(r"\*\*Phase linkage\*\*:\s*(.+)", re.IGNORECASE)
_AUTH_RE = re.compile(r"\*\*Authority sources\*\*:\s*(.+)", re.IGNORECASE)


def _verify_inputs() -> bool:
    all_ok = True
    for p in REQUIRED_INPUT_PATHS:
        exists = p.exists()
        if not exists:
            print(f"  input [MISSING]: {p.relative_to(REPO_ROOT)}", file=sys.stderr)
            all_ok = False
        else:
            print(f"  input [OK]: {p.relative_to(REPO_ROOT)}")
    return all_ok


def _parse_adr(adr_id: str, path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    title_m = _TITLE_RE.search(text)
    title = title_m.group(1).strip() if title_m else adr_id
    status_m = _STATUS_RE.search(text)
    status = status_m.group(1).strip() if status_m else "unknown"
    phase_m = _PHASE_RE.search(text)
    phase_linkage = phase_m.group(1).strip() if phase_m else ""
    auth_m = _AUTH_RE.search(text)
    authority_sources = [s.strip() for s in auth_m.group(1).split(",")] if auth_m else []
    return {
        "adr_id": adr_id,
        "title": title,
        "status": status,
        "path": str(path.relative_to(REPO_ROOT)),
        "phase_linkage": phase_linkage,
        "authority_sources": authority_sources,
    }


def build_index() -> dict:
    adrs = [_parse_adr(adr_id, path) for adr_id, path in ADR_FILES]
    return {
        "artifact_id": "P0-02-CORE-ADR-INDEX-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "adr_count": len(adrs),
        "adr_ids": [a["adr_id"] for a in adrs],
        "adr_titles": {a["adr_id"]: a["title"] for a in adrs},
        "adr_statuses": {a["adr_id"]: a["status"] for a in adrs},
        "phase_linkage": {a["adr_id"]: a["phase_linkage"] for a in adrs},
        "authority_sources": {a["adr_id"]: a["authority_sources"] for a in adrs},
        "adrs": adrs,
    }


def main() -> None:
    print("P0-02-CORE-ADR-INDEX-1: verifying inputs...")
    if not _verify_inputs():
        print("HARD STOP: required inputs not readable", file=sys.stderr)
        sys.exit(1)

    print("Building core ADR index...")
    index = build_index()

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")

    print(f"adr_count:  {index['adr_count']}")
    for adr_id in index["adr_ids"]:
        print(f"  {adr_id}: {index['adr_titles'][adr_id]} [{index['adr_statuses'][adr_id]}]")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
