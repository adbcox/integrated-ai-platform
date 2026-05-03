# OPNsense DNS authority — VERIFIED (D-17-21 close)

**Status:** VERIFIED. Replaces the provisional content authored 2026-05-01.
**Closing deliverable:** D-17-21 (2026-05-03)
**Verification basis:** OPNsense API probes + end-to-end resolution tests + executed migration
**Related KI:** KI-009 (RESOLVED at this close)

---

## Canonical posture

**Dnsmasq is the sole DNS authority for `*.internal` on this platform.**

- Dnsmasq runs on **port 53** on OPNsense (192.168.10.1).
- Dnsmasq holds **56 host records** as of 2026-05-03 (50 `*.internal` + 6 bare hostnames).
- All `*.internal` queries from any LAN client land at Dnsmasq.
- Unbound is **disabled** (`unbound.general.enabled=0`), service stopped, and is to be treated as removed residue.
- No process other than Dnsmasq listens on port 53 on OPNsense.

This posture matches the operator-intended architecture (Dnsmasq + Kea per OPNsense 26.1 modern defaults). The pre-D-17-21 state had Unbound and Dnsmasq both enabled, with Unbound on port 53 serving the actual `.internal` records — that was unintended residue from a prior session, not the operator's intended posture.

---

## Verified observable state (post-migration)

| Daemon  | Status   | Enabled | Port  |
|---------|----------|---------|-------|
| Dnsmasq | running  | 1       | 53    |
| Unbound | disabled | 0       | (none — service stopped) |

Verification command (any future session must run this before any DNS work):

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

# THE AUTHORITATIVE PROBE — Dnsmasq UI host table
curl -s -k -u "$KEY:$SEC" "https://192.168.10.1/api/dnsmasq/settings/searchHost" | \
    jq -r '.rows[] | "\(.host).\(.domain) → \(.ip)"' | sort

# Resolution proof — Dnsmasq on port 53 is the authority
dig @192.168.10.1 -p 53 vault.internal +short  # should return 192.168.10.145

# Unbound must report disabled
curl -s -k -u "$KEY:$SEC" "https://192.168.10.1/api/unbound/service/status" | jq .status
# expected: "disabled"
```

If Unbound is ever observed running again, treat that as drift — re-disable it. Unbound has no role on this platform.

---

## Where to add a new `.internal` record

OPNsense GUI: **Services → Dnsmasq DNS → Hosts → +**
- Host: hostname only (e.g. `myservice`)
- Domain: `internal`
- IP: target IP (typically `192.168.10.145` for Mac-Mini-fronted services)
- Description: short note (e.g. "Caddy front" or service purpose)

Or via API (mirrors what `scripts/d-17-21-dns-migration.sh` does):

```bash
curl -s -k -u "$KEY:$SEC" -X POST -H "Content-Type: application/json" \
    -d '{"host":{"host":"myservice","domain":"internal","local":"0","ip":"192.168.10.145","descr":"my note"}}' \
    "https://192.168.10.1/api/dnsmasq/settings/addHost"
curl -s -k -u "$KEY:$SEC" -X POST -H "Content-Type: application/json" -d '{}' \
    "https://192.168.10.1/api/dnsmasq/service/reconfigure"
```

A new Caddy `*.internal` site without a matching Dnsmasq host record will be flagged by the `caddy-dns-parity` check (`scripts/check-repo-coherence.py caddy-dns-parity`).

---

## Consumer-side cache invalidation (added 2026-05-03 per F14)

Adding the host entry on OPNsense Dnsmasq is necessary but not sufficient. Any consumer that has previously queried the hostname before the record existed will have a cached NXDOMAIN that does not refresh on its own for tens of minutes.

After adding a host entry, run the appropriate flush on every consumer that may have queried the hostname pre-creation:

```bash
# macOS (Mac Mini, Mac Studio, MacBook)
sudo killall -HUP mDNSResponder

# Linux — systemd-resolved hosts (most modern distros)
sudo systemd-resolve --flush-caches

# Linux — nscd hosts (older distros)
sudo nscd -i hosts

# Linux — local dnsmasq running as resolver
sudo systemctl restart dnsmasq
```

Verify resolution works through the full path, not just `dig`:

```bash
# dig queries Dnsmasq directly — will succeed even when the local cache is stuck
dig myservice.internal @192.168.10.1 +short

# This goes through the local resolver and reflects what apps actually see
python3 -c "import socket; print(socket.gethostbyname('myservice.internal'))"
```

Symptom of skipping the flush: `dig` returns the right IP but `curl`/`python socket.gethostbyname`/applications report "Could not resolve host." `dscacheutil -flushcache` does **not** clear macOS `mDNSResponder` — only the legacy DirectoryService cache.

Doctrine: `integration-audit-doctrine.md` Finding 14.

---

## What the D-17-21 migration did

1. Snapshotted Unbound + Dnsmasq state to `~/.platform-logs/d-17-21/*-pre-*.json`.
2. Added 50 records to Dnsmasq via `/api/dnsmasq/settings/addHost` (38 migrated from Unbound + 12 new — 11 NXDOMAIN Caddy sites + `mac-studio.internal`).
3. Reconfigured Dnsmasq; validated all 50 records resolve on port 53053 (Dnsmasq's pre-flip port).
4. Disabled Unbound (`unbound.general.enabled=0`), stopped the service.
5. Moved Dnsmasq from port 53053 → 53.
6. Reconfigured Dnsmasq; validated all 50 records resolve on port 53.
7. Final smoke: 56 records present, 0 resolve failures, Unbound `status=disabled`, port 53053 silent.

Migration script: `scripts/d-17-21-dns-migration.sh`.
Pre/post snapshots: `~/.platform-logs/d-17-21/*-{pre,post}-20260503-123945.json`.

---

## Historical residue (Unbound) — for incident-archaeology only

Pre-D-17-21, Unbound was running on port 53 with 38 user-added host overrides (created via OPNsense GUI by a session that was unaware of the Dnsmasq-as-authority intent). The 2026-05-01 audit chain compounded the confusion:

- The provisional doc probed `/api/unbound/settings/get` `.unbound.hosts` (returns 0 — wrong field; UI overrides live in `searchHostOverride`) and concluded "Unbound has 0 entries, so Dnsmasq must be the authority."
- KI-009 then renamed the parity check to query Dnsmasq, which made the check correct *for the operator-intended posture* but FAIL-noisy *against actual running state* (Dnsmasq had 6 records, none `.internal`). Pre-commit hook flipped to advisory mode.
- D-17-21 audit (2026-05-03) discovered Unbound had **38** `.internal` overrides via `searchHostOverride` (the correct API endpoint), revealing Unbound was the de-facto authority.

The migration removed that residue. Future DNS work should not reference Unbound except as historical context for this specific event.

---

## Lessons captured

This deliverable's lessons are recorded as durable doctrine in two places:

1. `CLAUDE.md` "DNS Authority Doctrine" section (operator-side rules — Dnsmasq is sole authority, Unbound is forbidden).
2. `docs/architecture-facts/integration-audit-doctrine.md` Finding 9 (audit-side rule — configuration audits verify against operator-stated intent, not against currently-running config; running state can be unintended residue).
