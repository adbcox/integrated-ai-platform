# KI-009 — caddy-unbound-parity check queries wrong DNS authority

**Severity:** Sev-3 (operational; structural bug; not data loss)
**Opened:** 2026-05-01
**Status:** PARTIALLY REMEDIATED in this commit; full sweep deferred.

## Symptom

`scripts/check-repo-coherence.py caddy-unbound-parity` reports 8 (or 9)
"missing" Unbound host overrides for `.internal` Caddy sites. The check
has reported FAIL since shipped (D-17-09, 2026-05-01).

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

## Update 2026-05-01 (post-237396b)

The 237396b commit asserted in `opnsense-dns-authority.md` that
"Dnsmasq is the active DNS authority." That assertion went beyond
what the probe evidence supported. Correct interpretation:

- Dnsmasq daemon is running on port 53053 (verified)
- Unbound daemon is running on port 53 (verified)
- The OPERATOR-INTENDED authority is suspected to be Dnsmasq + Kea
  (and possibly AdGuard Home), per OPNsense 26.1 modern defaults
  and per the operator's GUI not surfacing Unbound
- The CURRENTLY-OBSERVED authority answering port 53 is Unbound,
  but this is suspected to be unintended state from a prior
  session enabling Unbound's daemon

The function rename (`opnsense_get_unbound_overrides` →
`opnsense_get_host_records`) and subcommand rename
(`caddy-unbound-parity` → `caddy-dns-parity`) remain correct because
the new names are accurate REGARDLESS of which service turns out
to be the actual authority post-D-17-21.

Severity unchanged (Sev-3). Remediation deliverable updated:
D-17-21 scope expanded from "find resolution mechanism" to "audit
DNS state, back out unintended Unbound, ensure operator-intended
authority is sole, retroactively review whether DNS state
contributed to recent Vault troubleshooting incident."

### Lessons reinforced (D#20 + D#22)

- "Probe shows Unbound has 0 entries and Dnsmasq has 6 entries"
  is observation, not authority-determination. Authority is an
  operator-intent question, not a probe-result question. The
  probe data is consistent with multiple architectural
  interpretations; the right one is determined by what the
  operator INTENDED, not what the daemons currently report.
- Architecture-fact files MUST distinguish "verified observable"
  from "suspected interpretation." The 237396b file conflated
  the two.
