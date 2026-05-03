# OPNsense DNS state — verified audit (D-17-21 WP-02)

**Date:** 2026-05-03
**Deliverable:** D-17-21 (OPNsense DNS state audit + Unbound disable + retroactive Vault incident review)
**Probe basis:** OPNsense API at 192.168.10.1 via Vault AppRole `opnsense-api-reader`
**Scope:** authoritative determination of which DNS daemon serves `.internal` records on this platform. Replaces the provisional `docs/architecture-facts/opnsense-dns-authority.md` (will be rewritten at WP-06).

---

## Executive summary

**The provisional doc was wrong about which daemon is the authority.**

- **Unbound IS the active DNS authority for `*.internal`.** It holds **38 host overrides** under domain `internal`, served on port **53** (default DNS).
- **Dnsmasq holds 6 bare-hostname records** (no domain), served on port **53053**. None of them are `.internal` records. Dnsmasq is *not* answering `.internal` queries from clients.
- **The `caddy-unbound-parity` audit chain (KI-009) was probing the wrong API endpoint**, not the wrong daemon. `searchHostOverride` returns 38; `settings/get` `.unbound.hosts` returns 0. The provisional doc inferred "Dnsmasq must be the authority" from the empty `.unbound.hosts` response — but Unbound stores host overrides in a separate UI table (`/ui/unbound/overrides/`) accessed via `searchHostOverride`, not in the `general settings` blob.
- **All 11 currently-NXDOMAIN `.internal` Caddy sites are missing Unbound host overrides.** They will resolve as soon as the operator adds the corresponding Unbound override entries.

This means the operator-intended posture is **already correct in spirit**: there is one DNS authority for `.internal` (Unbound). The provisional doc's worry that "two services are running simultaneously and need a back-out" is not the actual situation. Dnsmasq is running but on a different port and serving a different (non-`.internal`) record set, so there is no port collision.

The remaining cleanup is the one originally proposed by KI-009: rewire the `caddy-dns-parity` check to query Unbound's `searchHostOverride` (where the records actually are), then add the 11 missing Unbound overrides via the OPNsense GUI.

---

## Verified observable state (probe-derived)

### Daemon status

| Daemon  | Status   | Enabled | Port  | API endpoint                               |
|---------|----------|---------|-------|--------------------------------------------|
| Unbound | running  | 1       | 53    | `/api/unbound/service/status`              |
| Dnsmasq | running  | 1       | 53053 | `/api/dnsmasq/service/status`              |

Both daemons are running, both enabled. They do **not** collide because they listen on different ports.

### Record inventory

| Daemon                                                | Endpoint                                        | Count |
|-------------------------------------------------------|-------------------------------------------------|------:|
| Unbound — `settings/get` `.unbound.hosts`             | `/api/unbound/settings/get`                     |     0 |
| Unbound — `searchHostOverride` (UI overrides table)   | `/api/unbound/settings/searchHostOverride`      |    38 |
| Unbound — `searchAlias`                               | `/api/unbound/settings/searchAlias`             |     0 |
| Unbound — `searchDomainOverride`                      | `/api/unbound/settings/searchDomainOverride`    |     0 |
| Dnsmasq — `settings/get` `.dnsmasq.hosts`             | `/api/dnsmasq/settings/get`                     |     6 |

The 38 Unbound overrides are **all** in domain `internal`, all enabled, all type `A`, all pointing at either `192.168.10.145` (Mac Mini, 37 records) or `192.168.10.201` (qnap.internal). These are the records currently serving `*.internal` queries.

The 6 Dnsmasq records are bare hostnames (qnap, server2, ai-node-02, Mac-Mini-Eth, homeassistant, mac-studio) with empty `domain` field — not `.internal` records.

### Resolution-path proof

```
$ dig @192.168.10.1 -p 53 vault.internal +short      → 192.168.10.145    (served by Unbound)
$ dig @192.168.10.1 -p 53053 vault.internal +short   → (empty)            (Dnsmasq has no .internal)
$ dig @192.168.10.1 -p 53 mac-studio +short          → (empty)            (Unbound has no bare-hostname)
$ dig @192.168.10.1 -p 53053 mac-studio +short       → 192.168.10.142    (served by Dnsmasq)
```

`scutil --dns` on Mac Mini shows `nameserver[0] : 192.168.10.1` with `search domain[0] : internal` — so all `.internal` queries from this host land at port 53 (Unbound).

---

## Why the provisional doc was wrong

The provisional `opnsense-dns-authority.md` (written 2026-05-01 alongside KI-009 partial-remediation) reasoned:

> "Unbound: running, answering on port 53, host overrides API returns 0 entries"

That sentence collapsed two distinct API responses into one. The "0 entries" result came from querying `.unbound.hosts` inside the `settings/get` payload, which is the **OPNsense `general settings` blob's `host` array** — used for legacy Unbound config (zone-style entries inline in the main config). It is **not** where the OPNsense Unbound UI stores user-added host overrides.

User-added host overrides land in the **`hosts.overrides` table** accessed via `/api/unbound/settings/searchHostOverride`. That table contained the 38 records the operator had created via the GUI (Services → Unbound DNS → Overrides → Host Overrides → +). The provisional doc never queried that endpoint; it only queried the `settings/get` blob, saw 0, and concluded Unbound must be empty.

The Dnsmasq table containing 6 entries was a red herring — those are bare-hostname records (no `.internal` domain) created for a separate purpose (likely DHCP-paired hostname resolution for devices on the LAN). They are not `.internal` records and are not what serves Caddy site DNS.

This is a **D#20 reinforcement**: capability evidence requires probing the *right* endpoint, not just *an* endpoint. The KI-009 root-cause statement ("queries Unbound's host-override table; that table is empty by design") was itself a probe-bug compounded — the 2026-05-01 author probed `settings/get` and got 0, then renamed the query to Dnsmasq under the assumption that the empty Unbound result meant Unbound wasn't the authority. The empty result actually meant the *probe path* was wrong.

---

## Caddy ↔ Unbound parity (verified)

Caddy `*.internal` sites in `docker/caddy/Caddyfile`: **33**
Unbound `*.internal` host overrides: **38**

### 11 Caddy sites missing Unbound override (will NXDOMAIN until added)

```
architecture.internal
docs.internal
homeassistant.internal
inventree.internal
loki.internal
mcp-xindex.internal
netbox.internal
openproject.internal
physical-architecture.internal
structurizr.internal
xindex.internal
```

All confirmed NXDOMAIN via `dig @192.168.10.1 -p 53`.

These are the records the operator must add via OPNsense GUI:

> Services → Unbound DNS → Overrides → Host Overrides → +
> Host: *(left column above, hostname only)*
> Domain: `internal`
> Type: `A`
> IP: `192.168.10.145`
> Description: e.g. `Caddy front`

### 16 Unbound overrides without Caddy site (informational, not drift)

```
bookstack.internal       dashboard.internal     dozzle.internal       filebrowser.internal
gitea.internal           mac-mini.internal      manyfold.internal     n8n.internal
netdata.internal         overseerr.internal     pgadmin.internal      plane.internal
portainer.internal       qnap.internal          ragflow.internal      tautulli.internal
```

These are operator-owned `.internal` records pointing at services accessed by direct port (no Caddy front). `mac-mini.internal` and `qnap.internal` are load-bearing for Docker compose `extra_hosts`. `dashboard.internal` was pruned from Caddy in commit `3db56c7` (Phase 13 Block 2 follow-up #1) and could be removed at the same operator session.

---

## Unbound disable decision — three paths (operator gate, WP-03)

### Path (a) — Disable Unbound entirely

**Rejected.** Unbound IS the active authority for 38 records that the operator created via GUI. Disabling it would NXDOMAIN every `.internal` site on the platform.

### Path (b) — Reconfigure Unbound (recommended)

Keep Unbound enabled (no change to its daemon state). Cleanup actions:

1. **Rewire the `caddy-dns-parity` audit script** to query `/api/unbound/settings/searchHostOverride` instead of `/api/dnsmasq/settings/get`. The KI-009 commit's rename direction was wrong — the script needs to go *back* to Unbound, but to the *correct* Unbound endpoint this time. Revert function name to `opnsense_get_unbound_overrides()` (or rename to `opnsense_get_host_overrides()` for clarity) and point at `searchHostOverride`.
2. **Add the 11 missing Unbound host overrides** for the NXDOMAIN Caddy sites listed above (operator-side GUI work).
3. **Update KI-009 status** from `PARTIALLY REMEDIATED + ADVISORY-MODE ACTIVE` to `RESOLVED`, which automatically returns the parity check to strict-fail mode (gate is data-driven on KI-009 file's status line).
4. **Remove `dashboard.internal`** from Unbound (1 record cleanup; no Caddy site any more).
5. **Leave Dnsmasq alone** — its 6 bare-hostname records on port 53053 are not interfering with `.internal` resolution and may have a separate operator-known purpose (DHCP-paired bare hostname resolution). No back-out needed.

### Path (c) — Retain as-is

**Functionally fine for the 27 `.internal` sites that DO resolve, but leaves KI-009 stuck in advisory mode forever** and leaves the 11 NXDOMAIN sites broken. This is the do-nothing option. Not recommended.

**Recommendation:** **Path (b)**. It is doctrine-aligned (KI-009 closes properly with correct probe path), unblocks 11 Caddy sites, leaves operator-intended `.internal` authority unchanged, and requires no DNS daemon restart. Total work: ~30 min script rewire + 11 GUI clicks.

---

## What this audit does NOT yet cover (deferred to WP-05 + later WPs)

- **KI-009 retroactive Vault incident review** (WP-05): whether the multi-day Vault troubleshooting incident on this platform had a silent DNS-routing contribution. Audit-derived hypothesis to test in WP-05: **no**, because Unbound has been the active authority for `vault.internal` the whole time (the record predates the incident; verified by GUI presence). The Vault incident was orthogonal — KV mount data loss, not DNS.
- **Where the `dashboard.internal` cleanup belongs** — could be folded into WP-04 execution batch.
- **`addptr=1` setting on all 38 records** — means PTR records are auto-generated. If the operator wants to disable that for any record, separate UI action.

---

## How to re-verify (any future session must run this before any DNS work)

```bash
ROLE_ID=$(cat ~/.vault-approle/opnsense-api-reader/role-id)
SECRET_ID=$(cat ~/.vault-approle/opnsense-api-reader/secret-id)
LOGIN=$(curl -s -X POST -d "{\"role_id\":\"$ROLE_ID\",\"secret_id\":\"$SECRET_ID\"}" \
    http://127.0.0.1:8200/v1/auth/approle/login)
VT=$(echo "$LOGIN" | jq -r ".auth.client_token")
KEY=$(curl -s -H "X-Vault-Token: $VT" \
    "http://127.0.0.1:8200/v1/secret/data/opnsense/api" | jq -r ".data.data.api_key")
SEC=$(curl -s -H "X-Vault-Token: $VT" \
    "http://127.0.0.1:8200/v1/secret/data/opnsense/api" | jq -r ".data.data.api_secret")

# THE AUTHORITATIVE PROBE — query the UI-overrides table, not settings/get
curl -s -k -u "$KEY:$SEC" \
    "https://192.168.10.1/api/unbound/settings/searchHostOverride?searchPhrase=&current=1&rowCount=200" | \
    jq -r '.rows[] | "\(.hostname).\(.domain) → \(.server) [\(.rr)] enabled=\(.enabled)"' | sort

# Resolution proof — Unbound on port 53 is the authority
dig @192.168.10.1 -p 53 vault.internal +short  # should return 192.168.10.145
```

---

## Surface back to operator — WP-03 decision required

Operator chooses:

- **(a)** Disable Unbound entirely (rejected — would break everything)
- **(b)** Recommended: rewire `caddy-dns-parity` to correct Unbound endpoint + add 11 missing overrides + close KI-009 + remove `dashboard.internal`. Operator-side GUI work needed for the 11 overrides.
- **(c)** Retain as-is (no DNS or script changes; KI-009 stays in advisory mode).

WP-04 executes the chosen path.
