# Phase 13 — Block 3 Phase 2 Results (HA Wipe + Clean Rebuild)

**Date**: 2026-04-28
**Operator**: claude-opus-4-7[1m] (autonomous large-prompt mode)
**HA host**: Intel NUC, 192.168.10.141:8123
**Scope**: P2.1–P2.4 deliverables: post-wipe state verification, integration drop/keep, OS/Core upgrade verification, Caddy route, Vault path setup

---

## Final state

### Versions (all on target per D5)

| Component | Installed | Latest | Status |
|---|---|---|---|
| HA Operating System | 17.2 | 17.2 | ✓ |
| HA Core | 2026.4.4 | 2026.4.4 | ✓ |
| HA Supervisor | 2026.04.0 | 2026.04.0 | ✓ |
| Matter Server addon | 8.4.0 | 8.4.0 | ✓ (upgraded from 8.3.0 this session) |

### Add-ons (4)

| Slug | Version |
|---|---|
| Terminal & SSH (`core_ssh`) | 10.1.0 |
| Studio Code Server | 6.0.1 |
| Matter Server (`core_matter_server`) | 8.4.0 |
| File editor | 6.0.0 |

D2 expected 3 add-ons (`core_ssh`, `core_matter_server`, `vscode`); File editor is extra — flagged for user decision (drop or keep).

### Config entries: 19 (was 20 pre-cleanup)

**DROP-list verification — all 0 ✓**

| Domain | Count |
|---|---|
| sonoff | 0 |
| tplink | 0 |
| govee | 0 |
| cloud | 0 (deleted this session, was 1) |
| sonoff_lan | 0 |

**KEEP-list status — 8 of 10 paired**

| Domain | Count | Notes |
|---|---|---|
| zha | 1 | hardware-source, SkyConnect ZBT-1 |
| matter | 1 | zeroconf |
| hue | 1 | zeroconf, Hue Bridge ecb5faaf77b6 |
| lutron_caseta | 1 | zeroconf, bridge 032257f4 |
| shelly | 1 | zeroconf, shellyplusrgbwpm-d8132add2154 |
| cast | 1 | zeroconf |
| mobile_app | 1 | registration-source, "Adrian" |
| go2rtc | 1 | system-source |
| meross_lan / meross_cloud | 0 | needs credential — surfaced |
| warmup | 0 | needs credential — surfaced |

### HACS-installed integrations (4, was 5)

| Repo | Version | Status |
|---|---|---|
| `hacs/integration` | 2.0.5 | keep (HACS itself) |
| `krahabb/meross_lan` | v5.8.0 | local-only Meross variant |
| `albertogeniola/meross-homeassistant` | v1.3.12 | cloud-based Meross variant — flagged for user decision |
| `ha-warmup/warmup` | v2024.3.6 | keep |
| ~~`AlexxIT/SonoffLAN` v3.11.1~~ | — | uninstalled this session |

### Devices: 54
### Areas: 15 (preserved — see lesson #2)
### Dashboards: 1 ("Map" only — rest purged)

---

## Vault state

| Path | Field | Status |
|---|---|---|
| `secret/homeassistant/api` | `api_key` (sha256-12: `cda3bb49b25f`, len 183) | retained, validity verified direct LAN (200 across `/api/`, `/api/config`, `/api/states`, `/api/services`) |
| `secret/homeassistant/admin` | `admin_username=admin`, `admin_password` (sha256-12: `9750372d825f`, len 32) | created this session — superseded by user-account-preserved finding (lesson #2); retained for future re-bootstrap scenarios |
| `secret/homeassistant/integrations/*` | (empty) | populated after Meross/Warmup credential surface |

**Policy**: `config/vault-policies/homeassistant-policy.hcl` expanded to read `admin`, `api`, and `integrations/*` paths. AppRole login round-trip verified (200 on `admin`, 200 on `api`, 404 on `integrations/test` — 404 means path empty, not denied).

---

## Caddy proxy state (P2.3 deliverable)

`docker/caddy/Caddyfile:262-272` — `homeassistant.internal` block:

- `reverse_proxy 192.168.10.141:8123`
- All `X-Forwarded-*` and `Forwarded` headers stripped upstream (Mac Docker Desktop NAT defense)
- `import access_log` shared snippet active

**Status matrix**:

| Endpoint | Status | Meaning |
|---|---|---|
| `/` | 302 → `/onboarding.html` redirect for unauthenticated, → dashboard for authenticated | working |
| `/onboarding.html` | 200 | working |
| `/manifest.json`, `/static/*` | 200 | working |
| `/api/config` (cookie auth via browser) | 200 | working |
| `/api/config` (Bearer auth from Mac Mini host) | 200 | working |
| `/api/config` (Bearer auth via Caddy proxy) | **401** | **degraded — see lesson #3** |

---

## Lessons learned (per user directive)

### 1. Bearer-token-via-Caddy 401: real proxy degradation, NOT HA-state misdiagnosis

When the same Bearer token returns 200 from Mac Mini host and 401 via Caddy proxy, the cause is in the proxy/HA-handshake path, not HA itself. The token is fully valid (verified by direct LAN call). Browser flow works because cookie-auth survives the proxy untouched.

**Working hypothesis**: HA's auth provider receives the Authorization header but the Caddy-container source IP (172.21.0.x in 172.21.0.0/16 docker bridge, NAT'd through Mac Docker Desktop's vmnet) triggers a silent auth-validator rejection that doesn't log to forwarded.py (since X-Forwarded-* are all stripped) and doesn't surface in HA core logs.

**Operational impact**: low — autonomous API operations from Mac Mini scripts can hit HA direct LAN at `192.168.10.141:8123`. Browser users authenticate via cookie via Caddy, also fine. The degradation only affects: programmatic Bearer-auth calls that route through `homeassistant.internal:443`, which is not a hot path for Block 3 work.

**Deferred**: detailed root-cause is a Phase 14 Caddy/HA item. Workaround: scripts use direct LAN.

### 2. WebSocket config purge does not remove user accounts

The Phase 2 "wipe" via WebSocket config_entries deletion + area cleanup did NOT touch the user table. The user's pre-existing `ADBCox@gmail.com` admin account survived the wipe. Areas (15) also survived — only dashboards (rest purged, "Map" remains as system default), config_entries (purged then re-paired), and devices (purged then repopulated by re-paired integrations) were affected.

The 401 storm during proxy diagnosis was ambiguous between "no admin exists" and "Bearer-via-proxy auth fails" — I interpreted as the former, leading to several hours wasted on browser-onboarding planning. Direct-LAN bearer test would have disambiguated in seconds.

**Doctrine update for future HA wipe blocks**:

- Before assuming wipe completeness: enumerate `auth/auth_store` and verify intended user-table state.
- "Factory reset" and "config-entries purge" are different scopes; choose explicitly.
- When a 401 storm appears, FIRST test the same token direct-LAN before extending the diagnostic chain to proxy/headers/onboarding state.

### 3. Long-lived bearer tokens cannot reach Supervisor REST

`/api/hassio/*` returns empty body for long-lived tokens. The supervisor REST API requires a supervisor-internal token. Workaround: WebSocket `supervisor/api` proxy command — most calls work (note: some `data` fields return `None` in HA OS 17.2; use service calls on `update.*` entities to drive add-on updates instead).

### 4. macOS application firewall blocks Homebrew Python outbound

Homebrew-installed Python 3.14 (`/opt/homebrew/Cellar/python@3.14/...`) cannot connect to LAN hosts (errno 65 "No route to host") despite curl/ping/nc all working. macOS Application Firewall does not filter Homebrew Python correctly. System Python (`/usr/bin/python3`) works without issue. Use `/tmp/hawsenv2` (system-Python venv) for any LAN-reaching Python in this session.

---

## Outstanding items (surfaced)

1. **Meross variant decision** — both `albertogeniola/meross-homeassistant` (cloud) and `krahabb/meross_lan` (LAN-only) installed. Platform local-only doctrine suggests dropping the cloud variant. User decision needed.
2. **Meross credentials** — needed to re-pair config_entry for whichever variant.
3. **Warmup credentials** — needed to re-pair Warmup My Heating Pad account.
4. **`file_editor` add-on** — present but not in the D2 expected list (3 add-ons). Drop or keep?

---

## P2 deliverables status

- [x] P2.1 HA wipe (config_entries, dashboards, devices purged; areas + users preserved per lesson #2)
- [x] P2.2 OS 17.1→17.2 + Core 2026.4.1→2026.4.4 (verified already on target; Matter Server 8.3→8.4 done this session)
- [x] P2.3 Caddy route reachable + Vault paths created/expanded
- [⏳] P2.4 integration re-pair partial (8/10 KEEP-list, blocked on Meross/Warmup credentials)
- [ ] P2.5+ pending P2.4 closure or explicit defer
