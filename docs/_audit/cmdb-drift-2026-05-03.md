# CMDB drift audit — 2026-05-03 (WP-03)

Scope: three-way read-only comparison of NetBox, `config/service-registry.yaml.DEPRECATED`, and `~/.platform-registry/inventory.json`, plus OPNsense read-only network state.

## Comparison basis

- NetBox service/device/IP state queried via API (token sourced from local Vault-rendered file; fingerprint only: sha256[:12]=`a7f1da287469`).
- YAML + NetBox service lists normalized through `scripts/cmdb_source.py` to avoid parser-shape bias.
- Runtime state from `~/.platform-registry/inventory.json`.
- OPNsense query (read-only):
  - `opnsense_get_host_records()` (Dnsmasq authority): **55** host records, **6** unique IPs.
  - Kea leases endpoint (`/api/kea/leases4/search`): **0** rows (consistent with “never Kea”).

## High-level deltas

| Axis | NetBox | YAML.DEPRECATED | inventory.json |
|---|---:|---:|---:|
| Service identities | 77 | 75 | 74 |
| IDs in NetBox not in YAML | 2 (`xindex`, `xindex-mcp`) | — | — |
| IDs in NetBox not in inventory | 45 | — | — |
| IDs in inventory not in NetBox | — | — | 42 |
| IPAM objects | 0 IPs / 0 prefixes / 0 VLANs | n/a | 51 internal IP entries |

## Drift instances (worked examples)

### 1. `homeassistant-container` exists in NetBox + YAML, absent in runtime
- Identity: `homeassistant-container`
- Substrate states:
  - NetBox: present
  - YAML.DEPRECATED: present
  - inventory.json: absent
- Classification: **stale**
- Severity: **high**
- Why: D-17-34 retired this container; stale CMDB records remained in declarative layers.

### 2. `xindex` + `xindex-mcp` present in NetBox, absent in YAML fallback
- Identity: `xindex`, `xindex-mcp`
- Substrate states:
  - NetBox: present
  - YAML.DEPRECATED: absent
  - inventory.json: (`xindex` present, `xindex-mcp` naming diverges by runtime mapping)
- Classification: **stranded (YAML stale)**
- Severity: **medium**
- Why: fallback substrate froze before newer NetBox entries.

### 3. 42 runtime services exist only in `inventory.json`
- Identity examples: `openproject`, `openproject-db`, `inventree`, `inventree-worker`, `loki`, `promtail`, `traefik`, `structurizr`, `upgrade-watcher`
- Substrate states:
  - inventory.json: present
  - NetBox + YAML: absent
- Classification: **stranded (runtime-only)**
- Severity: **high**
- Why: authoritative declarative CMDB does not represent major active runtime estate.

### 4. 45 declarative services absent from runtime substrate
- Identity examples: `anythingllm`, `homarr`, `iap-dashboard`, `obot-shim-*`, `homeassistant-physical`
- Substrate states:
  - NetBox + YAML: present
  - inventory.json: absent
- Classification: **stale/stranded (declarative-only)**
- Severity: **high**
- Why: declarative layers include retired or non-running entities.

### 5. Dependency graph conflict: `control-plane`
- Identity: `control-plane`
- Substrate states:
  - NetBox/YAML depends_on: `caddy, prowlarr, radarr, sonarr, vault`
  - inventory depends_on: `docker-socket-proxy-control, vault-agent-control-plane`
- Classification: **conflicting attributes**
- Severity: **medium**
- Why: declarative “logical integration” deps and runtime compose deps diverge.

### 6. Dependency graph conflict: `homepage`
- Identity: `homepage`
- Substrate states:
  - NetBox/YAML depends_on: `caddy, grafana, plane-api, prowlarr, radarr, sonarr, uptime-kuma, vault`
  - inventory depends_on: `vault-agent-homepage`
- Classification: **conflicting attributes**
- Severity: **medium**
- Why: runtime substrate tracks boot/runtime dependency edges; CMDB carries logical/service-level dependencies.

### 7. Port conflict by same identity: `netbox`
- Identity: `netbox`
- Substrate states:
  - NetBox/YAML port: `8080`
  - inventory host-mapped port: `8084`
- Classification: **conflicting attributes**
- Severity: **medium**
- Why: internal service port vs host-exposed port are collapsed differently across substrates.

### 8. IP/network authority conflict: NetBox IPAM empty vs OPNsense + runtime populated
- Identity: network/IP layer (global)
- Substrate states:
  - NetBox: IP=0, Prefix=0, VLAN=0
  - OPNsense Dnsmasq: 55 host records / 6 unique IPs
  - inventory.json: 51 internal IP entries across 14 docker networks
- Classification: **conflicting authority scope**
- Severity: **high**
- Why: ADR-A-014 claims network topology/IP authority in NetBox, but operational IP truth currently lives outside NetBox.

### 9. Runtime orphan signal not represented in declarative CMDB
- Identity: runtime_orphans block (`13` entities) + caddy_orphans (`6` hosts)
- Substrate states:
  - inventory.json: explicit orphan accounting
  - NetBox/YAML: no equivalent orphan dimension
- Classification: **schema drift**
- Severity: **medium**
- Why: runtime substrate has integrity telemetry that cannot be represented in declarative CMDB schema.

## Summary classification totals (from this run)

- **Stranded/stale entities:** 42 runtime-only + 45 declarative-only + 2 NetBox-only-vs-YAML baseline drift.
- **Conflicting entities/attributes:** dependency mismatches across 20 shared IDs; at least 2 concrete port conflicts (`caddy`, `netbox`).
- **Network/IP authority drift:** NetBox IPAM empty while OPNsense/runtime carry live address state.

## WP-03 intake conclusion

Minimum evidence threshold met (5+ concrete instances). Drift is structural, not incidental: the three substrates encode different semantics and update cadences without enforced consumer boundaries.
