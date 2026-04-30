#!/usr/bin/env python3
"""
Cross-index validator: ADR <-> Plane coherence check.
Read-only. Emits gap report and exits 0 (no gaps) or 1 (gaps found).

Usage:
    python3 scripts/cross-index-validate.py [--json] [--verbose]
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

REPO_ROOT         = Path(__file__).parent.parent
DECISION_REGISTER = REPO_ROOT / "docs" / "DECISION_REGISTER.md"


def load_adrs() -> list:
    adrs = []
    for line in DECISION_REGISTER.read_text().splitlines():
        # Format: | [A-NNN](adr/ADR-A-NNN[-slug].md) | Title | Summary |
        m = re.match(r"\|\s*\[A-(\d+)\]\(adr/ADR-A-\d+[^)]*\.md\)\s*\|\s*(.+?)\s*\|", line)
        if m:
            adr_id = f"ADR-A-{m.group(1).zfill(3)}"
            adrs.append({
                "id":     adr_id,
                "title":  m.group(2).strip(),
                "status": "Accepted",
            })
    return adrs


def load_plane_adr_issues() -> dict:
    from framework.plane_connector import PlaneAPI, RateLimitError
    api = PlaneAPI()
    try:
        issues = api.list_all_issues()
    except RateLimitError as exc:
        print(f"RATE-LIMIT: {exc}", file=sys.stderr)
        sys.exit(1)
    return {i["external_id"]: i
            for i in issues
            if (i.get("external_id") or "").startswith("ADR-")}


def main() -> int:
    adrs             = load_adrs()
    plane_adr_issues = load_plane_adr_issues()

    gaps, covered = [], []
    for adr in adrs:
        if adr["status"].lower() not in ("accepted", "superseded"):
            continue
        if adr["id"] in plane_adr_issues:
            covered.append(adr["id"])
        else:
            gaps.append(adr)

    report = {
        "adrs_checked":             len(adrs),
        "adrs_covered_in_plane":    len(covered),
        "adrs_missing_plane_issue": len(gaps),
        "gaps":    gaps,
        "covered": covered,
    }

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        print(f"ADRs checked:         {report['adrs_checked']}")
        print(f"Tracked in Plane:     {report['adrs_covered_in_plane']}")
        print(f"Missing Plane issue:  {report['adrs_missing_plane_issue']}")
        if "--verbose" in sys.argv or gaps:
            for g in gaps:
                print(f"  GAP: {g['id']} ({g['status']}) — {g['title']}")

    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main())
