# KI-009 — caddy-unbound-parity check queries wrong DNS authority

**Severity:** Sev-3 (operational; structural bug; not data loss)
**Opened:** 2026-05-01
**Status:** PARTIALLY REMEDIATED in this commit; full sweep deferred.

## Symptom

`scripts/check-repo-coherence.py caddy-unbound-parity` reports 8 (or 9)
"missing" Unbound host overrides for `.internal` Caddy sites. The check
has reported FAIL since shipped (17.I, 2026-05-01).

## Root cause

The check queries `/api/unbound/settings/searchHostOverride` (Unbound's
host-override table). On this platform, Unbound's host-override
table is empty by design. The DNS authority is **Dnsmasq**, with
host entries living at `/api/dnsmasq/settings/get` → `.dnsmasq.hosts`.

## What this commit fixes

- `opnsense_client.py`: function `opnsense_get_unbound_overrides()`
  is renamed to `opnsense_get_host_records()` and rewired to query
  the Dnsmasq endpoint. The old name is preserved as a deprecated
  alias that emits a warning when called, removable in a follow-up.
- `check-repo-coherence.py`: subcommand `caddy-unbound-parity` is
  renamed to `caddy-dns-parity`. The old name is preserved as an
  alias for one cycle.

## What this commit does NOT fix (follow-ups)

- launchd plist `com.iap.caddy-unbound-parity` still uses the old
  name. Rename + launchctl reload deferred to a small operator-
  involved cleanup.
- Status-file path `~/.platform-logs/caddy-unbound-parity.json`
  same.
- CI workflow step names same.
- `docs/runbooks/drift-detection.md` §9 references "Unbound" five
  times; rewrite deferred to same cleanup.
- `docs/_audit/caddy-unbound-parity-2026-05-01.md` audit report is
  stale (its "missing" list reflects Unbound's empty table, not
  actual platform DNS gaps). Re-audit deferred.

## Lessons (D#20 reinforcement)

- Audit recommendations require capability-evidence probing of the
  RUNNING SYSTEM, not document-derived assumptions about how the
  software is "usually configured."
- Where two services overlap (Unbound vs Dnsmasq) and either could
  be the authority, the audit must determine which IS the authority
  on THIS platform before designing checks against either.
- Operator pushback that contradicts a Claude assumption is data,
  not noise. The April 26 correction should have been chronicled
  in the repo as an architecture fact (this commit's File 1
  belatedly does so).
