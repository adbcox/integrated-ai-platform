#!/usr/bin/env python3
"""D-16-06 — repo-coherence drift checks (local + CI).

Single script holding the local-only checks for the three-leg drift
prevention model (ADR-A-006 single source of truth + one-way sync +
THIS deliverable's drift detection).

Subcommands:

    adr-readme-sync          docs/adr/ADR-A-*.md ↔ docs/adr/README.md
    decision-register-sync   docs/adr/ADR-A-*.md ↔ docs/DECISION_REGISTER.md
    caddy-internal-domains   list .internal site blocks from Caddyfile
    caddy-dns-parity         each Caddy .internal site has matching DNS host record (D-17-09)
    caddy-unbound-parity     deprecated alias for caddy-dns-parity (one-cycle)
    netbox-services-have-adrs   stub — Phase 17 territory
    framework-table-coherence  PROJECT_FRAMEWORK.md §7+§8 deliverable rows
    launchd-recency          docker/launchd-agents/*.plist installed + recent
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

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ADR_DIR = REPO_ROOT / "docs" / "adr"
ADR_README = ADR_DIR / "README.md"
DECISION_REGISTER = REPO_ROOT / "docs" / "DECISION_REGISTER.md"
CADDYFILE = REPO_ROOT / "docker" / "caddy" / "Caddyfile"
FRAMEWORK = REPO_ROOT / "docs" / "PROJECT_FRAMEWORK.md"
LAUNCHD_AGENTS_REPO = REPO_ROOT / "docker" / "launchd-agents"
LAUNCHD_AGENTS_INSTALLED = Path.home() / "Library" / "LaunchAgents"

# D-17-09 — Caddy↔Unbound parity (status-file pattern). The check is run
# on the operator Mac (cron/launchd or manual) by invoking this script
# with subcommand `caddy-unbound-parity --refresh`; that mode queries
# OPNsense via scripts/opnsense_client.py and writes a status JSON to
# the path below. The default (no --refresh) mode reads the status JSON
# and reports drift — pre-commit and CI run this default mode, so they
# never need OPNsense reachability.
PARITY_STATUS_FILE = Path.home() / ".platform-logs" / "caddy-unbound-parity.json"
PARITY_MAX_AGE_SEC = 36 * 3600   # 36h grace (daily-ish check on operator Mac)
MAC_MINI_IP = "192.168.10.145"   # Caddy host; all .internal A-records target this

# Per-job recency expectations (max age in seconds before considered stale).
# Recency probes a heartbeat file the plist's wrapper touches AFTER each
# script run (so silent-success jobs still register), or for KeepAlive
# jobs, the log file directly (since it gets continuous writes).
LAUNCHD_RECENCY_EXPECTATIONS: dict[str, dict] = {
    "com.iap.backup": {
        "max_age_sec": 36 * 3600,  # daily — 36h grace for sleep + skip days
        "probe_paths": ["/Users/admin/.platform-logs/backup.heartbeat"],
    },
    "com.iap.strava-refresh": {
        "max_age_sec": 2 * 3600,   # 30-min interval — 2h grace
        "probe_paths": ["/Users/admin/.platform-logs/strava-refresh.heartbeat"],
    },
    "com.iap.strava-sync": {
        "max_age_sec": 36 * 3600,
        "probe_paths": ["/Users/admin/.platform-logs/strava-sync.heartbeat"],
    },
    "com.iap.vault-audit-rotate": {
        "max_age_sec": 36 * 3600,
        "probe_paths": ["/Users/admin/.platform-logs/vault-audit-rotate.heartbeat"],
    },
    "com.iap.vault-audit-archive": {
        "max_age_sec": 36 * 3600,
        "probe_paths": ["/Users/admin/.platform-logs/vault-audit-archive.heartbeat"],
    },
    "com.iap.docker-events": {
        # KeepAlive — log file gets continuous writes from `docker events`
        "max_age_sec": 1 * 3600,
        "probe_paths": ["/Users/admin/.platform-logs/docker-events.log"],
    },
    "com.iap.caddy-unbound-parity": {
        # Daily refresh of the parity status file (D-17-09). 36h grace mirrors
        # the per-job pattern used for other daily jobs.
        "max_age_sec": 36 * 3600,
        "probe_paths": ["/Users/admin/.platform-logs/caddy-unbound-parity.heartbeat"],
    },
}

# Same row regex as scripts/phase-deliverable-count.py — kept inline
# (importing the script-as-module would require sys.path gymnastics
# given the hyphen in its name). The duplication is one line; the
# framework-table-coherence check exercises the same parser.
#
# WP-17-04-01.5 (2026-05-02): tolerate "(historical: NN.X)"
# annotation that may appear between the canonical D-NN-NN ID and the
# colon during the migration grace period. The status column also now
# admits parentheses so "DEFERRED to Phase 17 (D-17-15)" parses cleanly.
FRAMEWORK_ROW_RE = re.compile(
    r"^\|\s*(D-\d+-[\w.]+)[^:|]*:\s*(.*?)\s*\|\s*([\w \-()]+?)\s*\|\s*(.*?)\s*\|\s*$"
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


# ── Caddy ↔ DNS parity (D-17-09) ───────────────────────────────────────────────
# Renamed 2026-05-01 from caddy-unbound-parity. Dnsmasq, not Unbound, is the
# DNS authority on this platform — see
# docs/architecture-facts/opnsense-dns-authority.md and KI-009.
# launchd plist + status file path keep the old name for one cycle (rename
# requires launchctl reload + cron coordination; deferred to follow-up).

def _dns_match(caddy_fqdn: str, records: list[dict]) -> dict | None:
    """Return the matching Dnsmasq record for `caddy_fqdn` (e.g.
    "openproject.internal"), or None.

    Dnsmasq host entries on this platform appear in three shapes:
      1) host=<x>, domain=internal              → fqdn = "<x>.internal"
      2) host=<x>.internal, domain=""           → fqdn = "<x>.internal"
      3) host=<x>, domain=""                    → bare hostname; resolves
         via Dnsmasq's domain-suffix or expand-hosts setting. We accept
         these as a parity match when <x> matches the Caddy stem
         ("openproject" matches "openproject.internal") because the
         operator's network treats them as equivalent.
    """
    stem, _, _ = caddy_fqdn.partition(".")
    for r in records:
        if not r.get("enabled"):
            continue
        rec_host = (r.get("hostname") or "").strip()
        rec_domain = (r.get("domain") or "").strip()
        # Shape 1: host=stem, domain=internal
        if rec_host == stem and rec_domain == "internal":
            return r
        # Shape 2: host=stem.internal, domain=""
        if rec_host == caddy_fqdn and rec_domain == "":
            return r
        # Shape 3: host=stem, domain="" (bare hostname)
        if rec_host == stem and rec_domain == "":
            return r
    return None


def _refresh_parity_status() -> int:
    """Operator-Mac mode: query OPNsense, compute parity, write status JSON.

    Imports scripts/opnsense_client.py at call time so that pre-commit/CI
    invocations of `caddy-dns-parity` (which never call this function)
    don't pay the import cost or trip on missing AppRole files.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import opnsense_client  # type: ignore[import-not-found]
    except ImportError as exc:
        print(f"FAIL: could not import opnsense_client: {exc}")
        return 1

    caddy_domains = _caddy_internal_domains()
    if not caddy_domains:
        print("FAIL: no .internal sites in Caddyfile — refusing to write status")
        return 1

    try:
        records = opnsense_client.opnsense_get_host_records()
    except opnsense_client.OPNsenseClientError as exc:
        # Write a status file recording the failure so pre-commit/CI surface it
        status = {
            "schema": 1,
            "generated_at": int(time.time()),
            "ok": False,
            "error": str(exc),
            "caddy_count": len(caddy_domains),
            "record_count": None,
            "override_count": None,  # deprecated alias (one cycle)
            "missing": [],
            "extra_internal": [],
            "wrong_target": [],
        }
        PARITY_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        PARITY_STATUS_FILE.write_text(json.dumps(status, indent=2) + "\n")
        print(f"FAIL: OPNsense query failed: {exc}")
        print(f"  status written to {PARITY_STATUS_FILE}")
        return 1

    missing: list[str] = []
    wrong_target: list[str] = []
    matched_record_keys: set[str] = set()
    for caddy_fqdn in caddy_domains:
        match = _dns_match(caddy_fqdn, records)
        if match is None:
            missing.append(caddy_fqdn)
            continue
        # Track which Dnsmasq records were used so we can compute the
        # informational "extra" list below.
        matched_record_keys.add(match.get("uuid") or match.get("fqdn") or "")
        if match.get("ip") and match["ip"] != MAC_MINI_IP:
            wrong_target.append(caddy_fqdn)

    # Informational: enabled .internal-shaped records that didn't match
    # any Caddy site (Dnsmasq has more entries than just the .internal
    # web tier — DHCP reservations like `qnap`, `mac-mini-eth` show up).
    extra_internal: list[str] = []
    for r in records:
        if not r.get("enabled"):
            continue
        # Only flag entries that LOOK like .internal web records (either
        # explicit domain=internal or host ending in .internal). Bare
        # DHCP reservations are out of scope for this informational list.
        domain = (r.get("domain") or "").strip()
        host = (r.get("hostname") or "").strip()
        is_internal_shape = (domain == "internal") or host.endswith(".internal")
        if not is_internal_shape:
            continue
        key = r.get("uuid") or r.get("fqdn") or ""
        if key in matched_record_keys:
            continue
        extra_internal.append(r.get("fqdn") or host)
    extra_internal.sort()

    missing.sort()
    wrong_target.sort()

    status = {
        "schema": 1,
        "generated_at": int(time.time()),
        "ok": not (missing or wrong_target),  # extra_internal is informational
        "error": None,
        "caddy_count": len(caddy_domains),
        "record_count": len(records),
        "override_count": len(records),  # deprecated alias (one cycle)
        "missing": missing,
        "extra_internal": extra_internal,
        "wrong_target": wrong_target,
    }
    PARITY_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PARITY_STATUS_FILE.write_text(json.dumps(status, indent=2) + "\n")
    print(f"OK: parity status refreshed → {PARITY_STATUS_FILE}")
    print(f"  Caddy sites: {len(caddy_domains)}, Dnsmasq host records: {len(records)}")
    print(f"  missing: {len(missing)}, wrong_target: {len(wrong_target)}, extra_internal: {len(extra_internal)}")
    return 0 if status["ok"] else 1


def cmd_caddy_dns_parity() -> int:
    """Default (read) mode — pre-commit + CI safe.

    Reads PARITY_STATUS_FILE produced by `--refresh` mode.
    Behavior:
      - File missing → SKIP (operator hasn't run the refresh yet)
      - File older than PARITY_MAX_AGE_SEC → FAIL (silent-failure detection)
      - File reports ok=False → FAIL with the gap report
      - File reports ok=True  → OK
    """
    if "--refresh" in sys.argv:
        return _refresh_parity_status()

    if not PARITY_STATUS_FILE.is_file():
        print(f"SKIP: caddy-dns-parity — no status file at {PARITY_STATUS_FILE}")
        print("  Run on operator Mac: scripts/check-repo-coherence.py caddy-dns-parity --refresh")
        return 0

    try:
        status = json.loads(PARITY_STATUS_FILE.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: caddy-dns-parity — cannot parse {PARITY_STATUS_FILE}: {exc}")
        return 1

    age_sec = time.time() - status.get("generated_at", 0)
    if age_sec > PARITY_MAX_AGE_SEC:
        age_h = age_sec / 3600
        max_h = PARITY_MAX_AGE_SEC / 3600
        print(
            f"FAIL: caddy-dns-parity — status is {age_h:.1f}h old, "
            f"exceeds {max_h:.1f}h budget (silent-failure detection)"
        )
        print(f"  Refresh: scripts/check-repo-coherence.py caddy-dns-parity --refresh")
        return 1

    if status.get("error"):
        print(f"FAIL: caddy-dns-parity — last refresh errored: {status['error']}")
        return 1

    missing = status.get("missing", [])
    wrong_target = status.get("wrong_target", [])
    extra = status.get("extra_internal", [])

    if missing or wrong_target:
        print(
            f"FAIL: caddy-dns-parity — {len(missing)} missing, "
            f"{len(wrong_target)} wrong_target "
            f"(of {status.get('caddy_count')} Caddy sites)"
        )
        if missing:
            print("  Missing Dnsmasq host record:")
            for d in missing:
                print(f"    - {d}  (operator: add Dnsmasq host → {MAC_MINI_IP} in OPNsense)")
        if wrong_target:
            print(f"  Wrong A-record target (expected {MAC_MINI_IP}):")
            for d in wrong_target:
                print(f"    - {d}")
        if extra:
            print(f"  (informational) {len(extra)} Dnsmasq .internal records not in Caddy:")
            for d in extra:
                print(f"    - {d}")
        return 1

    print(
        f"OK: caddy-dns-parity — "
        f"{status.get('caddy_count')} Caddy sites all have Dnsmasq host records"
    )
    if extra:
        print(f"  (informational) {len(extra)} Dnsmasq .internal records not in Caddy:")
        for d in extra:
            print(f"    - {d}")
    return 0


def cmd_caddy_unbound_parity() -> int:
    """Deprecated alias — forwards to cmd_caddy_dns_parity for one cycle.

    The check was originally built against Unbound's host-override table,
    which is empty by design on this platform. Dnsmasq is the actual
    DNS authority. See docs/architecture-facts/opnsense-dns-authority.md
    and KI-009.
    """
    print(
        "DEPRECATED: caddy-unbound-parity has been renamed to caddy-dns-parity "
        "because Dnsmasq (not Unbound) is the DNS authority on this platform. "
        "Forwarding for one cycle.",
        file=sys.stderr,
    )
    return cmd_caddy_dns_parity()


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


# ── launchd recency (D-16-04.1) ──────────────────────────────────────────────

def _file_mtime(path: str) -> float | None:
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def cmd_launchd_recency() -> int:
    """Verify launchd jobs are installed AND recently active.

    Two checks per job:
      1. Plist source in docker/launchd-agents/ matches installed plist
         in ~/Library/LaunchAgents/ (drift detection — repo is canonical)
      2. The job's most-recently-written log file is younger than its
         per-job max_age_sec budget (recency — silent failure detection)

    Pre-commit + CI safe: if the installed plist or log directories are
    inaccessible (e.g., CI runner is not the operator's Mac), the
    recency check is SKIPPED for that job, not failed. Plist content
    drift is always checked (plists are in the repo).
    """
    issues: list[str] = []
    skipped: list[str] = []
    ok_count = 0
    on_operator_mac = LAUNCHD_AGENTS_INSTALLED.is_dir()

    repo_plists = sorted(LAUNCHD_AGENTS_REPO.glob("com.iap.*.plist"))
    if not repo_plists:
        print("FAIL: no com.iap.*.plist found in docker/launchd-agents/")
        return 1

    expected_labels = set(LAUNCHD_RECENCY_EXPECTATIONS.keys())
    repo_labels = {p.stem for p in repo_plists}

    missing_in_repo = expected_labels - repo_labels
    missing_in_expectations = repo_labels - expected_labels
    if missing_in_repo:
        for label in sorted(missing_in_repo):
            issues.append(f"  {label}: in expectations but no plist in docker/launchd-agents/")
    if missing_in_expectations:
        for label in sorted(missing_in_expectations):
            issues.append(f"  {label}: plist in docker/launchd-agents/ but no recency expectation")

    for plist in repo_plists:
        label = plist.stem
        installed = LAUNCHD_AGENTS_INSTALLED / plist.name
        # Drift check: installed copy must match repo copy
        if on_operator_mac:
            if not installed.is_file():
                issues.append(f"  {label}: NOT installed at {installed}")
                continue
            if installed.read_bytes() != plist.read_bytes():
                issues.append(f"  {label}: installed plist DIFFERS from repo (drift)")
                continue
        else:
            skipped.append(f"  {label}: skipped install check (not on operator Mac)")

        # Recency check (operator Mac only)
        if not on_operator_mac:
            continue
        exp = LAUNCHD_RECENCY_EXPECTATIONS.get(label)
        if exp is None:
            continue
        max_age = exp["max_age_sec"]
        probe_paths = exp["probe_paths"]
        mtimes = [m for m in (_file_mtime(p) for p in probe_paths) if m is not None]
        if not mtimes:
            issues.append(
                f"  {label}: no probe file exists yet at {probe_paths} "
                f"(job has never run, or probe was deleted)"
            )
            continue
        most_recent = max(mtimes)
        age_sec = time.time() - most_recent
        if age_sec > max_age:
            age_h = age_sec / 3600
            max_h = max_age / 3600
            issues.append(
                f"  {label}: probe is {age_h:.1f}h old, "
                f"exceeds {max_h:.1f}h budget — possible silent failure"
            )
        else:
            ok_count += 1

    if skipped:
        for s in skipped:
            print(s)
    if issues:
        print(f"FAIL: launchd-recency — {len(issues)} issue(s) of {len(repo_plists)} plists checked:")
        for i in issues:
            print(i)
        return 1
    if not on_operator_mac:
        print(f"SKIP: launchd-recency — not on operator Mac, drift checks skipped for {len(repo_plists)} plists")
        return 0
    print(f"OK: launchd-recency — {ok_count}/{len(repo_plists)} jobs installed + recent")
    return 0


# ── mac-studio-reachable ────────────────────────────────────────────────────

MAC_STUDIO_IP = "192.168.10.142"


def cmd_mac_studio_reachable() -> int:
    """Day-1 (D-17-15) reachability check for the Mac Studio compute node.

    One ICMP echo, 2-second timeout. Exits 0 reachable, 1 unreachable.
    Treated as drift because a Day-1 node going dark means either the
    node is down or its DHCP lease moved — both warrant operator attention.

    GitHub-hosted runners can't reach the home LAN; the check skips
    when GITHUB_ACTIONS=true (same pattern as validate-plane-sync-dryrun
    in the validate-infrastructure workflow).
    """
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"SKIP: mac-studio-reachable — GitHub-hosted runner can't reach {MAC_STUDIO_IP}")
        print("       runs locally on mac-mini (pre-commit + cron-driven coherence sweep)")
        return 0
    # `ping -W` units differ: macOS expects ms, Linux expects seconds.
    # Use the macOS-native value and rely on the subprocess timeout for
    # safety; this script only runs on operator-side macOS or in CI
    # (which we just skipped above).
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2000", MAC_STUDIO_IP],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        print(f"FAIL: mac-studio-reachable — ping subprocess timed out ({MAC_STUDIO_IP})")
        return 1
    if result.returncode != 0:
        print(f"FAIL: mac-studio-reachable — {MAC_STUDIO_IP} did not respond")
        print(result.stdout.strip() or result.stderr.strip())
        return 1
    print(f"OK: mac-studio-reachable — {MAC_STUDIO_IP} responded")
    return 0


# ── all ─────────────────────────────────────────────────────────────────────

CHECKS = {
    "adr-readme-sync": cmd_adr_readme_sync,
    "decision-register-sync": cmd_decision_register_sync,
    "caddy-internal-domains": cmd_caddy_internal_domains,
    "caddy-dns-parity": cmd_caddy_dns_parity,
    "netbox-services-have-adrs": cmd_netbox_services_have_adrs,
    "framework-table-coherence": cmd_framework_table_coherence,
    "launchd-recency": cmd_launchd_recency,
    "mac-studio-reachable": cmd_mac_studio_reachable,
}

# Deprecated subcommand aliases (one-cycle). Callable from the CLI but
# not run by `all`. See KI-009.
DEPRECATED_ALIASES = {
    "caddy-unbound-parity": cmd_caddy_unbound_parity,
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
    if len(sys.argv) < 2:
        print("Usage: check-repo-coherence.py <subcommand> [flags]", file=sys.stderr)
        print("Subcommands:", file=sys.stderr)
        for name in CHECKS:
            print(f"  {name}", file=sys.stderr)
        print("  all", file=sys.stderr)
        if DEPRECATED_ALIASES:
            print("Deprecated aliases (one-cycle):", file=sys.stderr)
            for name in DEPRECATED_ALIASES:
                print(f"  {name}", file=sys.stderr)
        return 2
    name = sys.argv[1]
    if name == "all":
        return cmd_all()
    if name in CHECKS:
        return CHECKS[name]()
    if name in DEPRECATED_ALIASES:
        return DEPRECATED_ALIASES[name]()
    print(f"ERROR: unknown subcommand {name!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
