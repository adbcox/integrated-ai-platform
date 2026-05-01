#!/usr/bin/env python3
"""D-16-06 — repo-coherence drift checks (local + CI).

Single script holding the local-only checks for the three-leg drift
prevention model (ADR-A-006 single source of truth + one-way sync +
THIS deliverable's drift detection).

Subcommands:

    adr-readme-sync          docs/adr/ADR-A-*.md ↔ docs/adr/README.md
    decision-register-sync   docs/adr/ADR-A-*.md ↔ docs/DECISION_REGISTER.md
    caddy-internal-domains   list .internal site blocks from Caddyfile
    netbox-services-have-adrs   stub — Phase 17 territory
    framework-table-coherence  PROJECT_FRAMEWORK.md §7+§8 deliverable rows
    all                      run everything; exit = max(child exit codes)

Exit codes:
    0  clean
    1  drift detected (with diff printed)
    2  reserved for "advisory finding" (caddy-internal-domains uses this
       for the stub mode where it just reports — never blocking)

Each subcommand is a thin function. The script has no third-party
dependencies (stdlib only) so pre-commit + CI can run it without a
venv.

The framework-table-coherence check imports parsing helpers from
scripts/phase-deliverable-count.py to avoid duplicating the row regex.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ADR_DIR = REPO_ROOT / "docs" / "adr"
ADR_README = ADR_DIR / "README.md"
DECISION_REGISTER = REPO_ROOT / "docs" / "DECISION_REGISTER.md"
CADDYFILE = REPO_ROOT / "docker" / "caddy" / "Caddyfile"
FRAMEWORK = REPO_ROOT / "docs" / "PROJECT_FRAMEWORK.md"

# Same row regex as scripts/phase-deliverable-count.py — kept inline
# (importing the script-as-module would require sys.path gymnastics
# given the hyphen in its name). The duplication is one line; the
# framework-table-coherence check exercises the same parser.
FRAMEWORK_ROW_RE = re.compile(
    r"^\|\s*(D-\d+-[\w.]+)\s*:\s*(.*?)\s*\|\s*([\w \-]+?)\s*\|\s*(.*?)\s*\|\s*$"
)

VALID_STATUS_PREFIXES = {"DONE", "IN PROGRESS", "NOT STARTED", "DEFERRED"}


# ── ADR ↔ README ────────────────────────────────────────────────────────────

def _adr_files() -> list[Path]:
    return sorted(p for p in ADR_DIR.glob("ADR-A-*.md") if p.is_file())


def _readme_links() -> dict[str, str]:
    """Return {adr-id: filename} pairs found in docs/adr/README.md.
    adr-id is normalised to ADR-A-NNN."""
    out: dict[str, str] = {}
    if not ADR_README.is_file():
        return out
    # Match | [ADR-A-NNN](FILENAME.md) | …
    rx = re.compile(r"\[\s*ADR-A-(\d+)\s*\]\(\s*([^)]+\.md)\s*\)")
    for m in rx.finditer(ADR_README.read_text()):
        adr_id = f"ADR-A-{m.group(1).zfill(3)}"
        out[adr_id] = m.group(2).strip()
    return out


def cmd_adr_readme_sync() -> int:
    files = _adr_files()
    file_ids: dict[str, str] = {}
    for p in files:
        m = re.match(r"^ADR-A-(\d+)", p.name)
        if not m:
            continue
        file_ids[f"ADR-A-{m.group(1).zfill(3)}"] = p.name
    links = _readme_links()

    file_set = set(file_ids)
    link_set = set(links)
    missing_in_readme = sorted(file_set - link_set)
    extra_in_readme = sorted(link_set - file_set)

    # Also: each README link must point to an existing file
    bad_targets: list[tuple[str, str]] = []
    for adr_id, fname in links.items():
        target = ADR_DIR / fname
        if not target.is_file():
            bad_targets.append((adr_id, fname))

    drift = bool(missing_in_readme or extra_in_readme or bad_targets)
    if missing_in_readme:
        print("FAIL: ADR files NOT linked from docs/adr/README.md:")
        for a in missing_in_readme:
            print(f"  - {a}  (file: {file_ids[a]})")
    if extra_in_readme:
        print("FAIL: README links pointing at non-existent ADR ids:")
        for a in extra_in_readme:
            print(f"  - {a}  (link target: {links[a]})")
    if bad_targets:
        print("FAIL: README links whose target file is missing:")
        for a, f in bad_targets:
            print(f"  - {a} -> docs/adr/{f}")
    if drift:
        return 1
    print(f"OK: {len(file_ids)} ADR files all linked from docs/adr/README.md")
    return 0


# ── ADR ↔ DECISION_REGISTER ─────────────────────────────────────────────────

def _register_links() -> dict[str, str]:
    """Return {adr-id: filename} from rows like
        | [A-NNN](adr/ADR-A-NNN[-slug].md) | …
    """
    out: dict[str, str] = {}
    if not DECISION_REGISTER.is_file():
        return out
    rx = re.compile(r"\[\s*A-(\d+)\s*\]\(\s*adr/(ADR-A-\d+[^)]*\.md)\s*\)")
    for m in rx.finditer(DECISION_REGISTER.read_text()):
        adr_id = f"ADR-A-{m.group(1).zfill(3)}"
        out[adr_id] = m.group(2).strip()
    return out


def cmd_decision_register_sync() -> int:
    files = _adr_files()
    file_ids: dict[str, str] = {}
    for p in files:
        m = re.match(r"^ADR-A-(\d+)", p.name)
        if not m:
            continue
        file_ids[f"ADR-A-{m.group(1).zfill(3)}"] = p.name
    register = _register_links()

    file_set = set(file_ids)
    register_set = set(register)
    missing_in_register = sorted(file_set - register_set)
    extra_in_register = sorted(register_set - file_set)

    bad_targets: list[tuple[str, str]] = []
    for adr_id, fname in register.items():
        target = ADR_DIR / fname
        if not target.is_file():
            bad_targets.append((adr_id, fname))

    drift = bool(missing_in_register or extra_in_register or bad_targets)
    if missing_in_register:
        print("FAIL: ADR files NOT indexed in docs/DECISION_REGISTER.md:")
        for a in missing_in_register:
            print(f"  - {a}  (file: {file_ids[a]})")
    if extra_in_register:
        print("FAIL: DECISION_REGISTER rows pointing at non-existent ADR ids:")
        for a in extra_in_register:
            print(f"  - {a}  (link target: {register[a]})")
    if bad_targets:
        print("FAIL: DECISION_REGISTER rows whose target file is missing:")
        for a, f in bad_targets:
            print(f"  - {a} -> docs/adr/{f}")
    if drift:
        return 1
    print(f"OK: {len(file_ids)} ADR files all indexed in docs/DECISION_REGISTER.md")
    return 0


# ── Caddy .internal domains ─────────────────────────────────────────────────

def _caddy_internal_domains() -> list[str]:
    """Return the sorted list of `*.internal` site blocks declared in
    docker/caddy/Caddyfile.

    Matches lines that begin with `<host>.internal {` (no leading
    indentation — site blocks are top-level)."""
    if not CADDYFILE.is_file():
        return []
    rx = re.compile(r"^([a-z0-9][a-z0-9\-]*\.internal)\s*\{")
    domains: list[str] = []
    for line in CADDYFILE.read_text().splitlines():
        m = rx.match(line)
        if m:
            domains.append(m.group(1))
    return sorted(set(domains))


def cmd_caddy_internal_domains() -> int:
    domains = _caddy_internal_domains()
    if not domains:
        print("FAIL: no .internal site blocks found in docker/caddy/Caddyfile")
        return 1
    print(f"OK: {len(domains)} .internal site blocks in Caddyfile")
    for d in domains:
        print(f"  {d}")
    return 0


# ── NetBox services have ADRs (stub) ────────────────────────────────────────

def cmd_netbox_services_have_adrs() -> int:
    """Phase 17 territory — see docs/runbooks/drift-detection.md §3.

    Future intent: every NetBox ipam.service tagged `control-center`
    should reference an ADR (governing decision or a service-onboarding
    runbook). Today the linkage doesn't exist as a declared field, so
    this is a stub. Returns 0 with a NotImplemented note so `all`
    doesn't fail."""
    print("SKIP: netbox-services-have-adrs — Phase 17 stub (NotImplemented)")
    return 0


# ── PROJECT_FRAMEWORK deliverable-table coherence ───────────────────────────

def cmd_framework_table_coherence() -> int:
    """Sanity-check every row matched by FRAMEWORK_ROW_RE has:
       - a status word from VALID_STATUS_PREFIXES (after stripping
         trailing prose like "DEFERRED to Phase 16" → "DEFERRED")
       - a non-empty reference column

    Order of rows is preserved on stderr; failure exits 1.
    """
    if not FRAMEWORK.is_file():
        print(f"FAIL: {FRAMEWORK} missing")
        return 1
    bad: list[str] = []
    seen = 0
    for line in FRAMEWORK.read_text().splitlines():
        m = FRAMEWORK_ROW_RE.match(line)
        if not m:
            continue
        seen += 1
        del_id, _title, status, ref = m.groups()
        status_upper = status.strip().upper()
        # Status valid if it begins with one of the valid prefixes
        # (e.g. "DEFERRED to Phase 16" → DEFERRED prefix matches).
        prefix = next(
            (p for p in VALID_STATUS_PREFIXES if status_upper == p or status_upper.startswith(p + " ")),
            None,
        )
        if prefix is None:
            bad.append(
                f"  {del_id:<14} status=`{status.strip()}` "
                f"(no valid prefix; expected one of {sorted(VALID_STATUS_PREFIXES)})"
            )
            continue
        if not ref.strip():
            bad.append(f"  {del_id:<14} status=`{status.strip()}` reference is EMPTY")
    if bad:
        print(f"FAIL: PROJECT_FRAMEWORK.md row coherence ({len(bad)} bad rows of {seen} parsed):")
        for b in bad:
            print(b)
        return 1
    print(f"OK: PROJECT_FRAMEWORK.md row coherence — {seen} rows parsed, all valid")
    return 0


# ── all ─────────────────────────────────────────────────────────────────────

CHECKS = {
    "adr-readme-sync": cmd_adr_readme_sync,
    "decision-register-sync": cmd_decision_register_sync,
    "caddy-internal-domains": cmd_caddy_internal_domains,
    "netbox-services-have-adrs": cmd_netbox_services_have_adrs,
    "framework-table-coherence": cmd_framework_table_coherence,
}


def cmd_all() -> int:
    rc = 0
    for name, fn in CHECKS.items():
        print(f"── {name} " + "─" * (60 - len(name)))
        rc = max(rc, fn())
        print()
    print("=" * 64)
    print(f"all: exit {rc}")
    return rc


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check-repo-coherence.py <subcommand>", file=sys.stderr)
        print("Subcommands:", file=sys.stderr)
        for name in CHECKS:
            print(f"  {name}", file=sys.stderr)
        print("  all", file=sys.stderr)
        return 2
    name = sys.argv[1]
    if name == "all":
        return cmd_all()
    if name not in CHECKS:
        print(f"ERROR: unknown subcommand {name!r}", file=sys.stderr)
        return 2
    return CHECKS[name]()


if __name__ == "__main__":
    sys.exit(main())
