# Phase 13 Block 4.C — Closeout

**Date:** 2026-04-29
**Status:** Closed.
**Outcome:** NetBox is the authoritative platform CMDB. Homegrown
`config/service-registry.yaml` is deprecated, renamed to
`config/service-registry.yaml.DEPRECATED`, and retained only as the
YAML side of a dual-source loader during the transition window. All
three consumers (validate-cmdb.sh, topology-api, control-plane) read
through the shared loader and produce byte-identical output between
sources. Block 4.D is unblocked.

## Sub-stage summaries

| Stage | Outcome | Key artefact |
|---|---|---|
| **C0** — Precondition verification | Pass | All five preconditions met before kickoff. |
| **C1** — Architecture audit | Pass | `PHASE_13_BLOCK_4C_C1_AUDIT_2026-04-29.md` (75 services, 3 consumers identified). |
| **C2** — NetBox deployment | Pass | NetBox 4.5.9 stack on `control-center-net`; 17 discoveries surfaced incl. healthcheck pattern (#3), upstream-flow default (#5), round-trip equivalence (#16), staged toggle (#17). |
| **C3** — Registry → NetBox migration | Pass (lossy on three dimensions; corrected in C5.2 prereq) | `PHASE_13_BLOCK_4C_C3_MIGRATION_2026-04-29.md`. |
| **C4** — Plane label backfill | Pass | 603/604 issues correctly labeled, 0 mismatches; commit `5e0f4e5`. |
| **C5.2 prereq** — fix C3 lossy schema | Pass | Two new custom fields (`health_expect_extra`, `port_is_internal`) + backfill; commit `c959760`. |
| **C5.2a** — validate-cmdb.sh dual-source | Pass | Byte-identical output sha256 prefix `2d4a8fd21589de80`; commit `e9fe1f9`. |
| **C5.2b** — topology-api dual-source | Pass | All three endpoints byte-identical; commit `33bd70a`. |
| **C5.2c** — control-plane dual-source | Pass | Services array byte-identical; commit `d05d3bd`. |
| **C5.2 docs** | Pass | PLATFORM_OVERVIEW + runbook + dependency-graph; evidence pkg; commit `f5742e1`. |
| **C5.4** — deprecation rename + header | Pass | `service-registry.yaml.DEPRECATED`; commit `ad614aa`. |
| **C6** — regression + closeout | Pass=14 / Fail=0 / Warn=4 (no new) | This document. |

## Vault — hash-only verification

NetBox-related secrets confirmed present in Vault. Values never
displayed; only SHA256 prefixes (first 12 hex digits) are recorded
to confirm presence and content stability across audits. The hashing
is performed by piping `vault kv get -format=json` through `python3 -c
'hashlib.sha256(...).hexdigest()'` on the host so the value is in
memory only for the hash transformation.

| Path | Field hashes (sha256:12) |
|---|---|
| `secret/netbox/admin` | email=29a912c7d4bb password=f384b136290d username=8c6976e5b541 |
| `secret/netbox/api_token` | key=ce7e5f120f28 token=70aa317dabf2 |
| `secret/netbox/app` | api_token_pepper=debfef5a13e0 |
| `secret/netbox/postgres` | password=ceef9f543307 |
| `secret/netbox/redis` | password=1f1857aa9439 |
| `secret/netbox/redis-cache` | password=e22ee4ba988a |
| `secret/netbox/secret_key` | value=2fbee89e7060 |

Vault sealed=false, audit log capturing (size 5 690 094 B at probe
time), 34 policies in place.

## NetBox object/custom-field/relationship counts

| Resource | Count | Notes |
|---|---|---|
| Sites | 1 | `integrated-ai-platform` |
| Devices | 4 | `mac-mini`, `qnap`, `ha-device`, `opnsense` |
| Services (`ipam.service`) | 75 | matches dedup'd registry count |
| Custom fields | 16 | inc. C5.2-prereq fields `health_expect_extra`, `port_is_internal` |
| Tags | 19 | category + kind + lifecycle (`sidecar`, `support-service`, `deprecated`) |
| Service dependency edges | 72 | across 47 services with `depends_on` populated |
| Services with `health_expect_extra` | 6 | round-trip multi-value health codes |
| Services with `port_is_internal=true` | 29 | container-internal-only ports |

## Plane label distribution

Final state from C4 backfill (commit `5e0f4e5`). 46 distinct labels
in use across 603 labelled issues; full distribution is in
`PHASE_13_BLOCK_4C_C4_BACKFILL_2026-04-29.md`. Top buckets:

| Count | Label |
|---|---|
| 60 | testing |
| 43 | docs |
| 41 | MONITOR (10 from MON + 31 from MONITOR) |
| 36 | data |
| 31 | cli |
| 30 | UTIL / security / REFACTOR / CONFIG / api |
| 21 | media |
| 18 | OPS |
| 11 | DEV |
| 10× | UX, USERMGMT, SCALE, PERF, INT, FLOW, Deployment, CI/CD, BACKUP, APIGW |

18 forward-looking labels remain unused (no current issues); they
are not a defect and are retained for future scope.

## Consumer migration outcomes (byte-identical equivalence)

Same image, `CMDB_SOURCE=yaml` vs `CMDB_SOURCE=netbox`:

| Consumer | Endpoint / output | sha256 prefix | bytes |
|---|---|---|---|
| validate-cmdb.sh | header-stripped output | `2d4a8fd21589de80` | — |
| topology-api | `/api/topology` | `e6ea700556d304ac` | 35 264 |
| topology-api | `/api/topology/nodes` | `33720e0962c4faea` | 27 299 |
| topology-api | `/api/topology/edges` | `7a55ffc22c79251c` |  7 904 |
| control-plane | `/api/registry/services` (services array only) | `f0f5cf7274668c8b` | 11 754 |
| control-plane | `/api/registry/categories` | `f4918fd085e67ab8` |  1 474 |
| control-plane | `/api/registry/health` | `d1cfe56472c6385c` |  3 506 |

Single intentional non-equivalence: top-level `metadata` block of
`/api/registry/services` is YAML-only (NetBox returns `{}`). The
consumed services array is byte-identical.

## Regression probe — `block-4c-final`

Run: `bash docs/phase-13/h1-regression-probe.sh block-4c-final`
Captured: `/tmp/c52c/regression-block4c-final.log`

```
PASS=14 FAIL=0 WARN=4
```

WARNs (all pre-existing; none introduced by Block 4.C):

1. `openhands.internal` not in macOS DNS cache — service is dormant; will resolve on activation.
2. `restic snapshot list` inaccessible from probe context — Vault-rendered creds; orthogonal to 4.C scope.
3. No gate-specific dependency probes defined for `block-4c-final` — informational, not a failure.
4. `/tmp/plane_token.txt` — Plane API token left in `/tmp` from earlier 4.C work (pre-C5.x), 0600 perms; not a credential exposure but the heuristic correctly flags it. Operator should `rm` after reading this report.

No new WARNs introduced by C5.x or C5.4. No FAILs.

## C6 follow-ups — full list (18 entries, 17 distinct)

All registered in `PHASE_13_BLOCK_4C_C2_DISCOVERIES_2026-04-29.md`.
Numbered in registration order. #7 and #9 are the same item
(clerical artifact of the original C6 closeout pass — see the
note under #9 below); they are tracked as a single follow-up
and were resolved together on 2026-04-29.

| # | Topic | Type | Status |
|---|---|---|---|
|  1 | Port-conflict pre-check pre-deployment | Canonical pattern | Open |
|  2 | Upstream pinning doctrine | Doctrine | Open |
|  3 | Healthcheck pattern (Vault-rendered creds → upstream entrypoint) | Canonical pattern | Open |
|  4 | Upstream-flow default (don't reimplement bootstrap when image already does it) | Canonical pattern | Open |
|  5 | Implicit (covered by #4) — script-path drift in upstream images | Implicit | n/a |
|  6 | (No C6 follow-up registered — accepted as-is) | n/a | n/a |
|  7 | Revoke memory-file Plane token (consolidated with #9) | Cleanup task | **RESOLVED 2026-04-29** |
|  8 | (Implicit roll-up of healthcheck/upstream-flow follow-ups) | Implicit | n/a |
|  9 | Revoke memory-file Plane token (duplicate of #7 — clerical artifact) | Cleanup task | **RESOLVED 2026-04-29 (see #7)** |
| 10 | Audit `framework/plane_connector.py` consumers (rate-limit handling) | Code audit | Resolved (Increment 1, commit `1eed06c`) |
| 11 | Audit `framework/plane_connector.py` error class hierarchy | Code audit | Resolved (Increment 1, commit `1eed06c`) |
| 12 | Canonical-pattern README: pagination termination contract | Doc | Resolved (Increment 1, commit `e3d7c17`) |
| 13 | Dry-run coverage gap (dry-run skips the apply path) | Test gap | Open |
| 14 | Fix `framework/plane_connector.py:360` `create_issue` builder | Bug fix | Resolved (Increment 1, F1, commit `1eed06c`) |
| 15 | Add "first-batch verify" pattern to canonical-pattern | Canonical pattern | Resolved (Increment 1, commit `e3d7c17`) |
| 16 | Round-trip equivalence at migration time (not deprecation time) | Doctrine | Open |
| 17 | Flip `CMDB_SOURCE` default yaml→netbox after stability window | Cleanup task | Open |
| 18 | Redact + rotate plaintext Plane admin password in `plane_deployment.md` | Cleanup task | Open (Phase 14) |

(Numbering reflects the discoveries doc; some entries are
roll-ups/cross-references, hence the gaps in raw count vs item count.)

### #7/#9 resolution detail (2026-04-29)

The C6 closeout pass registered the "revoke memory-file Plane
token" cleanup twice — once as #7, once as #9 — phrased almost
identically. Both refer to the same token (Discovery #13's
memory-file token, hash prefix `4d83dff62161`).

**Action taken:** Operator deleted the token via the plane-api
Django shell, not the Plane UI. The Plane UI revocation path
was unavailable because the web UI returned "No authentication
methods available" — see new **Discovery #18** in the C2
discoveries doc.

**Verification artifacts:**

- Pre-delete: `APIToken id=38b1dfe4-4065-44ca-a56f-1b38ad3b2eb3
  label=dashboard-sync hash_prefix=4d83dff62161 active=True` —
  hash matched expected target.
- Delete: `t.delete()` via Django ORM, no SQL exception.
- Post-delete: 1 APIToken row remaining
  (`id=c2320aed-2361-4cbd-bf49-b9de1b97321f label=homepage
  hash_prefix=b90c7b634be7 active=True`) — the Vault-canonical
  token is the only survivor.
- Control probe: Vault `homepage_token` (prefix `b90c7b634be7`)
  authenticates against the Plane API — `GET /api/v1/users/me/
  → HTTP 200`.

**Verification limitation:** Direct API probe with the revoked
token was structurally impossible — the plaintext value was
already redacted in Discovery #13's resolution, so no value
existed to probe with. Verification is therefore the
pre-delete row + ORM-level delete + post-delete row inventory,
not a 401/403 from the deleted token. Doctrine note for future
incidents: capture the SHA-256 prefix **before** redaction so
post-revocation API verification has a value-free handle. Added
to `docs/canonical-patterns/plane-connector-usage.md` §10.

**Audit log:** Plane CE in this build does not expose an
admin-accessible API audit log surface — the `APIActivityLog`
model exists but no endpoint surfaces it without web auth (see
Discovery #18). This is the second-leg of the
verification-limitation note above.

**New discoveries surfaced during this work:**

- **Discovery #18** (registered): Plane CE web auth not
  configured. Blocked the Plane UI revocation path; operator
  fell back to Django shell.
- **C6 #18** (registered, deferred to Phase 14): Plane admin
  password (`admin@local.dev`) is plaintext in
  `plane_deployment.md` line 17 with a weak,
  dictionary-attackable value. Surfaced during the REVOKED
  notation edit. Not actioned in this cleanup window — the C6
  entry is the action handle; rotation happens in a future
  scoped block.

## Block 4.D readiness

- NetBox is operational and authoritative.
- All consumers read through the shared loader; YAML fallback works.
- C6 regression probe clean; no new FAILs.
- C6 follow-ups recorded: 18 entries / 17 distinct (none gating). #7 and #9 RESOLVED 2026-04-29; #18 Open (Phase 14).
- Doctrine + ADR work for the move to NetBox is captured in the
  Discovery #17 entry and this closeout.

Block 4.D may proceed.
