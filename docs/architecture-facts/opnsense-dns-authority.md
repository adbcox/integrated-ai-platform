# OPNsense DNS authority on this platform

**Status:** ARCHITECTURAL FACT — operator-confirmed twice (2026-04-26
and 2026-05-01), under recurring forgetting risk. Future sessions:
PROBE before assuming.

## The fact

OPNsense at 192.168.10.1 runs BOTH `unbound` and `dnsmasq` services.

**Dnsmasq is the active DNS authority for this platform.**

- Host overrides live in **Dnsmasq's** configuration, NOT Unbound's.
- The OPNsense web UI Unbound section does not surface in the
  operator's view of the GUI for this OPNsense version/skin.
- All host reservations (qnap, mac-mini-eth, mac-studio,
  homeassistant, etc.) are in Dnsmasq → DNS & DHCP → Hosts tab.
- The `.internal` resolution that works (grafana.internal,
  vault.internal, homepage.internal, etc.) is served via Dnsmasq's
  DHCP-static-reservation auto-registration, NOT via Unbound
  Host Overrides.

## Why this keeps getting forgotten

OPNsense docs at docs.opnsense.org default to "Unbound + Dnsmasq
together" topology where Unbound is primary resolver. Plain LLM
priors built on those docs assume Unbound is the host-override
authority. **This is wrong for THIS platform**, where the operator
configured Dnsmasq as the operational authority.

## How to verify (any future session must run this before any DNS work)

```
ROLE_ID=$(cat ~/.vault-approle/opnsense-api-reader/role-id)
SECRET_ID=$(cat ~/.vault-approle/opnsense-api-reader/secret-id)
LOGIN=$(curl -s -X POST -d "{\"role_id\":\"$ROLE_ID\",\"secret_id\":\"$SECRET_ID\"}" \
    http://127.0.0.1:8200/v1/auth/approle/login)
VT=$(echo "$LOGIN" | jq -r ".auth.client_token")
KEY=$(curl -s -H "X-Vault-Token: $VT" \
    "http://127.0.0.1:8200/v1/secret/data/opnsense/api" | jq -r ".data.data.api_key")
SEC=$(curl -s -H "X-Vault-Token: $VT" \
    "http://127.0.0.1:8200/v1/secret/data/opnsense/api" | jq -r ".data.data.api_secret")

# Count entries in each
echo "Unbound host overrides:"
curl -s -k -u "$KEY:$SEC" "https://192.168.10.1/api/unbound/settings/get" | \
    jq "[.unbound.hosts // {} | to_entries[] | select(.value.hostname != null and .value.hostname != \"\")] | length"

echo "Dnsmasq host entries:"
curl -s -k -u "$KEY:$SEC" "https://192.168.10.1/api/dnsmasq/settings/get" | \
    jq "[.dnsmasq.hosts // {} | to_entries[] | select(.value.host != null and .value.host != \"\")] | length"
```

The one with non-zero count is the authority. As of 2026-05-01:
Unbound = 0; Dnsmasq = 6 (and growing). **Dnsmasq.**

## API endpoints to use

| Operation              | Correct endpoint                          |
|------------------------|-------------------------------------------|
| List host entries      | GET  /api/dnsmasq/settings/get            |
| Add host entry         | POST /api/dnsmasq/settings/addHost        |
| Update host entry      | POST /api/dnsmasq/settings/setHost/{uuid} |
| Delete host entry      | POST /api/dnsmasq/settings/delHost/{uuid} |
| Apply / reconfigure    | POST /api/dnsmasq/service/reconfigure     |

The corresponding `/api/unbound/*` endpoints exist but **operating on
them does nothing visible to clients on this platform** because
Unbound's host-override module is unused.

## Operator-side note (for adding records via OPNsense GUI)

In the operator's GUI: **Services → Dnsmasq DNS & DHCP → Hosts tab.**
NOT Unbound DNS → Overrides (which is missing from the GUI in this
build).

## History of forgetting

| Date       | Session             | Fix                                 |
|------------|---------------------|-------------------------------------|
| 2026-04-26 | Re-architecture     | Operator caught; verbal correction  |
| 2026-05-01 | 17.I shipped wrong  | Parity check built on Unbound; FAIL |
| 2026-05-01 | 17.D pre-deployment | Operator caught AGAIN; this commit  |

If you find yourself about to write `/api/unbound/settings/...` while
working on a host-record problem on THIS platform: STOP. Read this
file. Use Dnsmasq instead.
