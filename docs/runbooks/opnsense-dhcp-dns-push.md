# Runbook: Push Internal DNS via OPNsense Dnsmasq DHCP

Configure the OPNsense Dnsmasq instance to advertise `192.168.10.1`
as the primary DNS server in DHCP offers, so fresh LAN clients pick
up the internal resolver automatically and `*.internal` records
resolve without per-client configuration.

Sibling concern to D-17-21 (DNS authority) and `integration-audit-
doctrine.md` Finding 14 (consumer-side cache invalidation).

## When to use this

A new device joins the LAN — a fresh DHCP lease, a re-imaged
machine, a guest laptop — and `vault.internal` (or any `.internal`
hostname) fails to resolve until DNS is hand-set. Without the DHCP
DNS option, clients fall back to whatever resolver their OS picks
by default (typically the gateway relaying a public resolver), and
internal hostnames return NXDOMAIN.

This runbook is **not** a substitute for the D-17-21 host-record
flow (`opnsense-dns-authority.md` "Where to add a new `.internal`
record"); it is the missing piece that makes those records reachable
from clients without manual resolver setup.

## Prerequisite: Dnsmasq is the working DNS authority

Before pushing Dnsmasq as the LAN's advertised resolver, verify it
is currently answering `.internal` queries on port 53. Pushing a
broken authority via DHCP breaks every fresh lease.

```bash
# AppRole bootstrap (same shape as opnsense-dns-authority.md)
ROLE_ID=$(cat ~/.vault-approle/opnsense-api-reader/role-id)
SECRET_ID=$(cat ~/.vault-approle/opnsense-api-reader/secret-id)
LOGIN=$(curl -s -X POST -d "{\"role_id\":\"$ROLE_ID\",\"secret_id\":\"$SECRET_ID\"}" \
    http://127.0.0.1:8200/v1/auth/approle/login)
VT=$(echo "$LOGIN" | jq -r ".auth.client_token")
KEY=$(curl -s -H "X-Vault-Token: $VT" \
    "http://127.0.0.1:8200/v1/secret/data/opnsense/api" | jq -r ".data.data.api_key")
SEC=$(curl -s -H "X-Vault-Token: $VT" \
    "http://127.0.0.1:8200/v1/secret/data/opnsense/api" | jq -r ".data.data.api_secret")

# Dnsmasq holds host records
curl -s -k -u "$KEY:$SEC" "https://192.168.10.1/api/dnsmasq/settings/searchHost" \
    | jq -r '.rows[] | "\(.host).\(.domain) → \(.ip)"' | sort | head

# Dnsmasq answers on port 53
dig @192.168.10.1 -p 53 vault.internal +short   # → 192.168.10.145
```

If either probe fails, fix Dnsmasq first per `opnsense-dns-authority.md`.
Do not proceed.

## Procedure

1. Open the OPNsense web UI: `https://192.168.10.1`.
2. Navigate to **Services → Dnsmasq DNS → DHCP options**
   (operator-verified 2026-05-03; Dnsmasq is the sole DHCP
   service in use on this platform — Kea is not enabled).
3. Add (or edit) a DHCP option entry with:
   - **Tag / Scope:** LAN interface (no tag = applies to all
     scopes)
   - **Option:** `6` (DNS server) — corresponds to dnsmasq native
     `dhcp-option=6,...`
   - **Value:** `192.168.10.1`
4. Save, then **Apply** to reconfigure Dnsmasq.
5. (Optional) Confirm in `/var/etc/dnsmasq.conf` on OPNsense that
   `dhcp-option=6,192.168.10.1` is present after reconfigure.

## Verification

### Force a fresh lease on one client

The DHCP option only reaches clients on lease renewal. To verify
without waiting for the natural renewal:

```bash
# macOS — release & renew on the active interface
sudo ipconfig set en0 BOOTP && sudo ipconfig set en0 DHCP

# Linux — systemd-networkd / NetworkManager
sudo dhclient -r && sudo dhclient
# or for NetworkManager:
nmcli connection down "<conn>" && nmcli connection up "<conn>"
```

### macOS: confirm resolver and resolution

```bash
scutil --dns | grep -A2 "resolver #1"
# nameserver[0] : 192.168.10.1   ← expected

dig vault.internal +short
# 192.168.10.145
```

### Linux: confirm resolver and resolution

```bash
resolvectl status | grep -A1 "DNS Servers"
# DNS Servers: 192.168.10.1   ← expected

dig vault.internal +short
# 192.168.10.145
```

If `dig @192.168.10.1 vault.internal +short` returns the right
answer but the bare `dig vault.internal` (no `@server`) does not,
the client did not pick up the DHCP option — re-renew the lease.

## Rollback

To revert: edit (or delete) the same DHCP option entry under
**Services → Dnsmasq DNS → DHCP options**, save, apply.

Clients with already-leased addresses retain the old DNS option
until lease renewal. To pull a single client back immediately, run
the release/renew snippet from the verification section.

After rollback (or if the option was misconfigured during a
deployment window), per Finding 14 every consumer that may have
queried a `.internal` hostname under the bad config also needs its
local cache flushed:

```bash
# macOS
sudo killall -HUP mDNSResponder

# Linux — systemd-resolved
sudo systemd-resolve --flush-caches
```

`dscacheutil -flushcache` does **not** clear `mDNSResponder`; do
not substitute it. The `nscd`/`local-dnsmasq` flushes from F14
apply only to hosts actually running those daemons — most LAN
clients on this platform do not.

## Cross-references

- `docs/architecture-facts/opnsense-dns-authority.md` — Dnsmasq is
  sole DNS authority; AppRole-bootstrap probe pattern reused above
- `docs/architecture-facts/integration-audit-doctrine.md` Finding
  14 — consumer-side cache invalidation, the missing-flush failure
  mode this runbook prevents from compounding
- `docs/runbooks/opnsense-add-host-overrides.md` — host-record
  flow (note: stale Unbound references; backlog candidate to update
  or supersede with a Dnsmasq-correct version)
