---
ki: KI-012
title: Caddy internal CA root rotation requires manual re-trust across all distributed devices
severity: LOW
status: OPEN
disposition: accept-as-permanent-debt-decade-horizon
discovered: 2026-05-11
phase: D-17-115 Phase 1 (Caddy internal-CA trust distribution closeout)
---

# KI-012: Caddy internal CA root rotation requires manual re-trust

## Symptom

Caddy 2.x's local certificate authority issues a self-signed root
certificate with ~10-year validity. When that root rotates (next event
~2035-2036 depending on Caddy first-run date on Mac Mini), every device
that previously trusted the old root will reject `*.internal`
certificates with TLS errors until re-trusted with the new root. There
is no automated re-distribution mechanism; trust install is
operator-driven per `docs/architecture-facts/caddy-internal-tls-doctrine.md`.
At rotation time the operator will need to re-trust the new root across
every device class that consumes `*.internal` services (macOS / iOS /
iPadOS / Apple TV / Android).

## Root Cause

Caddy auto-manages its internal PKI by design — root + intermediate
certificates with default validity periods (root ~10 years; intermediate
~7 days; leaf certs auto-rotate transparent to clients). The platform
opted into Caddy's default rotation rather than disabling it (which
would require pinning a static CA in the Caddyfile and managing
rotation manually). Trust distribution is operator-driven across the
LAN; no re-distribution automation exists yet because the rotation
interval is decade-scale and observation evidence (whether re-trust
burden is genuinely painful at a real rotation event) does not yet
exist. Premature optimization to automate before observing the friction
would be a clean violation of the operator's brief-bloat / friction-
stacking discipline.

## Affected

All 37 `*.internal` services exposed via `docker/caddy/Caddyfile`,
accessed over HTTPS from any device other than the Caddy host itself.
Affected device classes:

- **macOS clients:** Mac Mini (control plane, runs Caddy), Mac Studio
  (compute node), MacBook Pro (current primary work surface).
- **iOS / iPadOS clients:** operator's iPhone / iPad.
- **tvOS clients:** Apple TV.
- **Android clients:** any operator-side Android device.

The Caddy host itself is unaffected — Caddy serves the cert and
validates against its own CA internally.

## Mitigation Applied

- `scripts/caddy-ca-trust-macos.sh` authored to make per-device macOS
  re-trust mechanically simple (single `sudo security add-trusted-cert`
  invocation; idempotent via `security find-certificate` pre-check).
  Phase 2 of D-17-115 commits the cert file; once that lands, re-trust
  is one script-run per macOS device.
- `docs/runbooks/caddy-internal-ca-trust.md` extended with a Re-trust
  procedure section that documents the rotation-event response
  (re-extract cert, re-commit `deployment/caddy/internal-root.crt`,
  re-run script on each macOS device, re-trust manually on
  iOS/iPadOS/Apple TV/Android per existing per-class procedures, update
  Cert provenance fingerprint).
- This KI tracks the rotation event so it does not surprise the
  operator a decade out.

## Trigger to close

Operator observes a CA rotation event AND decides between two
structural responses based on observed friction:

- **Option (b) — disable Caddy CA rotation:** edit Caddyfile to specify
  a static root CA with operator-controlled rotation. Converts this
  from a recurring decade-scale event into a one-shot trust setup, but
  adds operator responsibility for explicit rotation timing.
- **Option (c) — implement automated re-distribution:** add tooling
  that detects fingerprint change on the canonical cert
  (`deployment/caddy/internal-root.crt`) and pushes to known devices
  via a registry-driven mechanism. Heaviest engineering; only
  justified if the manual re-trust burden at a real rotation event is
  observed-painful.

Default disposition (option (a), the implicit current path): accept
rotation as known operational interrupt; revisit only if it becomes
painful at the actual rotation event.

## Closure procedure

1. Operator confirms rotation has occurred (e.g., `*.internal` pages
   start failing TLS validation; SHA-256 fingerprint of the cert in the
   Caddy container differs from the fingerprint recorded in
   `deployment/caddy/internal-root.crt`).
2. Operator decides between option (b) static CA OR option (c)
   automated re-distribution based on observed re-trust burden at the
   rotation event (or accepts a fresh manual cycle and refreshes this
   KI's `discovered` date for the next decade).
3. Implement chosen path:
   - Option (b): Caddyfile edit + new commit; document manual rotation
     procedure in the runbook; close KI-012 referencing the
     implementing commit.
   - Option (c): scripts/registry/automation work; commit; close
     KI-012 referencing the implementing commit.

If at rotation time the operator still finds the manual re-trust
trivial, leave KI-012 OPEN and refresh the `discovered` date to reflect
the new rotation cycle.

## Cross-references

- D-17-115 (`docs/PROJECT_FRAMEWORK.md` §9 — Caddy internal-CA trust distribution)
- `scripts/caddy-ca-trust-macos.sh`
- `docs/runbooks/caddy-internal-ca-trust.md`
- `docs/architecture-facts/caddy-internal-tls-doctrine.md`
- `deployment/caddy/internal-root.crt` (deferred to D-17-115 Phase 2 — operator off-LAN)
- `docker/caddy/Caddyfile` (37 `*.internal` domains served)

## Impact

- Decade-scale operational interrupt; no current operational impact.
- Observed at rotation time as TLS errors on every previously-trusted
  device; symptoms are obvious (browser cert warnings on `*.internal`)
  so the rotation event is unlikely to go unnoticed.
- Remediation cost (worst-case under current manual model): N devices ×
  ~1 minute per macOS device (script-driven) + ~3 minutes per iOS /
  iPadOS / Apple TV / Android device (manual). At current device count
  this is ~15-30 minutes of operator time at rotation, which justifies
  the deferred-to-observation disposition.
- This KI exists primarily to prevent rotation surprise — the operator
  has a written record that this work is anticipated and the
  decision-tree options are pre-staged.

## Disposition (2026-05-11)

Disposition recorded per phase-17-closeout-audit §6 Q5 operator approval; status remains OPEN. Accept-as-permanent-debt-decade-horizon: rotation event is ~2035-2036; the KI persists until that event surfaces, at which point operator chooses option (b) static CA or option (c) automated re-distribution per the Trigger to close section above.
