# Runbook: Add OPNsense Host Overrides for `.internal` Services

**Last updated:** 2026-05-04 (D-17-53 Posture-2 entry 2/10 —
doctrine substitution Unbound→Dnsmasq)

Add a `.internal` DNS record on OPNsense so a new Caddy-fronted
internal service (or any direct-port LAN service) is resolvable
on the LAN.

## Authority

`*.internal` authority is **Dnsmasq DNS** on OPNsense
(`192.168.10.1`) port `53`. **Unbound is forbidden on this
platform** (D-17-21, 2026-05-03). Do not use Unbound Host
Overrides or `/api/unbound/...` endpoints; if a future session
observes Unbound running again, treat that as drift and re-disable
per `opnsense-dns-authority.md`.

## Procedure (UI)

1. Open the OPNsense web UI: `https://192.168.10.1`.
2. Navigate to **Services → Dnsmasq DNS → Hosts → `+`**.
3. Fill the record:
   - **Host:** short hostname (e.g. `bazarr`)
   - **Domain:** `internal`
   - **IP:** `192.168.10.145` for Caddy-fronted services; the
     upstream host's IP for direct-port services (e.g. QNAP,
     Mac Studio).
   - **Description:** short note (e.g. `Caddy front`).
4. **Save**, then **Apply** (top-right banner) to reconfigure
   Dnsmasq.

## Procedure (API, optional)

Self-contained snippet — bootstrap Vault AppRole, then add the
record. Mirrors `scripts/d-17-21-dns-migration.sh`:

```bash
# Vault AppRole bootstrap (read-only OPNsense API credentials)
ROLE_ID=$(cat ~/.vault-approle/opnsense-api-reader/role-id)
SECRET_ID=$(cat ~/.vault-approle/opnsense-api-reader/secret-id)
LOGIN=$(curl -s -X POST -d "{\"role_id\":\"$ROLE_ID\",\"secret_id\":\"$SECRET_ID\"}" \
    http://127.0.0.1:8200/v1/auth/approle/login)
VT=$(echo "$LOGIN" | jq -r ".auth.client_token")
KEY=$(curl -s -H "X-Vault-Token: $VT" \
    "http://127.0.0.1:8200/v1/secret/data/opnsense/api" | jq -r ".data.data.api_key")
SEC=$(curl -s -H "X-Vault-Token: $VT" \
    "http://127.0.0.1:8200/v1/secret/data/opnsense/api" | jq -r ".data.data.api_secret")
unset VT

# Add the host record (HTTP Basic auth — OPNsense API convention)
curl -s -k -u "$KEY:$SEC" -X POST -H "Content-Type: application/json" \
    -d '{"host":{"host":"bazarr","domain":"internal","local":"0","ip":"192.168.10.145","descr":"Caddy front"}}' \
    "https://192.168.10.1/api/dnsmasq/settings/addHost"

# Reconfigure Dnsmasq (empty body)
curl -s -k -u "$KEY:$SEC" -X POST -H "Content-Type: application/json" -d '{}' \
    "https://192.168.10.1/api/dnsmasq/service/reconfigure"
```

## Consumer-side cache flush (Finding 14)

Adding the host entry is necessary but not sufficient. Any
consumer that queried the hostname before the record existed
holds a cached NXDOMAIN that does not refresh on its own for
tens of minutes. After adding the record, flush every consumer
that may have queried it pre-creation:

```bash
# macOS consumers (Mac Mini, Mac Studio, MacBook)
sudo killall -HUP mDNSResponder

# Linux consumers (systemd-resolved)
sudo systemd-resolve --flush-caches
```

`dscacheutil -flushcache` does **not** clear `mDNSResponder` —
do not substitute it. Doctrine: `integration-audit-doctrine.md`
Finding 14.

## Verification

From any LAN client:

```bash
# Authority-side (always succeeds when Dnsmasq has the record)
dig @192.168.10.1 -p 53 bazarr.internal +short
# → 192.168.10.145

# Consumer-side (reflects what apps actually see; only succeeds
# after the cache flush above)
python3 -c "import socket; print(socket.gethostbyname('bazarr.internal'))"
# → 192.168.10.145
```

For Caddy-fronted services, also confirm the HTTPS route:

```bash
curl -skI https://bazarr.internal | head -n 1
# → HTTP/2 200   (or 302/401 depending on the upstream)
```

If `dig` works but `python socket.gethostbyname` / `curl` fail,
the consumer cache is stuck — re-run the flush.

## Current arr-stack host override set

Present in Dnsmasq as of 2026-05-04 (subset of the 50
`*.internal` records; arr-stack-relevant only):

- `bazarr.internal` → `192.168.10.145`
- `cleanuparr.internal` → `192.168.10.145`
- `sonarr.internal` → `192.168.10.145`
- `radarr.internal` → `192.168.10.145`
- `prowlarr.internal` → `192.168.10.145`

Caddy fronts all five; the IP is the Mac Mini's. Add a new
arr-stack sibling here (and in this runbook's record list) when
deploying.

## Cross-references

- `docs/architecture-facts/opnsense-dns-authority.md` — D-17-21
  authority chronicle (Dnsmasq sole, Unbound forbidden);
  AppRole-bootstrap probe pattern reused above
- `docs/runbooks/opnsense-dhcp-dns-push.md` — sibling runbook
  for pushing Dnsmasq as the DHCP-advertised resolver
- `docs/architecture-facts/integration-audit-doctrine.md` —
  Finding 14 (consumer-side cache invalidation)
- `scripts/d-17-21-dns-migration.sh` — worked-example script
  for the original Unbound→Dnsmasq migration; canonical curl/jq
  shapes

## Doctrine-substitution audit (D-17-56)

This runbook had stale Unbound-era guidance in prior revisions
(authority framing + endpoint family) that conflicted with the
post-D-17-21 canonical posture.

Faithful substitution completed in D-17-56:

- Authority claim aligned to Dnsmasq sole authority
  (`opnsense-dns-authority.md`), with explicit Unbound-forbidden
  note retained.
- UI path aligned to Dnsmasq Host records flow.
- API path aligned to Dnsmasq endpoints, including
  `POST /api/dnsmasq/service/reconfigure` with empty `{}` body.
- Consumer cache invalidation (Finding 14) integrated as a required
  post-change step; `dscacheutil -flushcache` explicitly rejected.
