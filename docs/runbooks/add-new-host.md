# Runbook: Add New Host to Platform

**Last updated:** 2026-04-29 (Phase 14 D-DOC)

---

## Overview

A "host" is a physical or virtual machine joining the platform infrastructure.
Current hosts: Mac Mini M4 Pro (control plane), QNAP TS-X72 (NAS), OPNsense (router),
HA hub (IoT). Planned: MacBook Pro (future), Linux Threadripper (future).

Adding a new host involves:
1. Register in NetBox CMDB (authoritative inventory)
2. Configure DNS in OPNsense (`.internal` domain)
3. Register services hosted on the node
4. Connect to Headscale VPN (if remote)
5. Add monitoring (Zabbix agent, node-exporter)
6. Add to Caddy reverse proxy if hosting `.internal` services

---

## Step 1: Register host in NetBox

In NetBox (`netbox.internal`):
- **Devices** → Add Device
  - Name: descriptive name (e.g., `macbook-pro-m5`)
  - Device type: select or create hardware profile
  - Role: `workstation` / `server` / `nas` / `router` as appropriate
  - Site: `Home Lab`
  - Status: `Active`
- **Interfaces** → Add primary interface (e.g., `en0`)
- **IP Addresses** → Assign IP; set as primary for device

Verify the host appears in the service inventory:
```bash
CMDB_SOURCE=netbox python3 scripts/cmdb_source.py | python3 -c \
  "import json,sys; [print(s['host'], s['name']) for s in json.load(sys.stdin) if s.get('host')=='<new-host>']"
```

---

## Step 2: Configure DNS in OPNsense

In OPNsense (`192.168.10.1`) → Services → Dnsmasq DNS → Host Overrides:
- Host: `<hostname>`
- Domain: `internal`
- IP: `<host IP>`
- Description: human-readable

Verify resolution:
```bash
dig <hostname>.internal @192.168.10.1
```

---

## Step 3: Register services in NetBox

For each service the new host will run:
- **IPAM** → Services → Add Service
  - Device: `<new-host>`
  - Name: service name
  - Protocol: TCP
  - Port: assigned port
  - Description: purpose

Assign compose file and credential metadata in NetBox custom fields
(or update `config/service-registry.yaml.DEPRECATED` during transition window if
`CMDB_SOURCE=yaml` is still the default).

---

## Step 4: Headscale VPN (remote hosts only)

For hosts outside the LAN:

```bash
# On Headscale server (mac-mini)
docker exec headscale headscale preauthkeys create --reusable --expiration 24h --user default
# Copy the preauthkey to the new host

# On new host — install tailscale client and join
tailscale up --login-server https://headscale.internal --authkey <preauthkey>
```

Verify:
```bash
docker exec headscale headscale nodes list
```

---

## Step 5: Add monitoring

### Zabbix Agent

Deploy the Zabbix agent on the new host:
```bash
# For Docker hosts — add to the host's compose or run standalone
docker run -d \
  --name zabbix-agent \
  --restart unless-stopped \
  -e ZBX_SERVER_HOST=zabbix-server \
  -e ZBX_HOSTNAME=<new-host> \
  zabbix/zabbix-agent2:alpine-7.4-latest
```

Register in Zabbix UI (`zabbix.internal`):
- Configuration → Hosts → Create Host
  - Hostname: must match `ZBX_HOSTNAME`
  - Groups: `Linux servers` or `Mac servers`
  - Interfaces: Agent DNS → `<hostname>.internal:10050`
  - Templates: `Linux by Zabbix agent` (or macOS equivalent)

### Node Exporter (Prometheus)

Add to `docker/observability-stack.yml` scrape targets or VMAgent config
(`docker/victoriametrics/vmagent.yml`) if the host exposes `:9100`.

---

## Step 6: Caddy routes (if hosting `.internal` services)

Add routes to `docker/caddy/Caddyfile` for each service:

```caddy
<service>.internal {
    import access_log
    reverse_proxy <host-ip>:<port>
}
```

Reload Caddy:
```bash
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

Verify:
```bash
curl -sk https://<service>.internal/ | head -5
```

---

## Step 7: Document in rewire log

If the host addition involves out-of-repo compose changes
(`~/control-center-stack/stacks/*`), record pre/post snapshots:

```bash
# Pre-snapshot
docker ps --format '{{.Names}} {{.Status}}' > /tmp/pre-add-host.txt

# (make changes)

# Post-snapshot
docker ps --format '{{.Names}} {{.Status}}' > /tmp/post-add-host.txt
diff /tmp/pre-add-host.txt /tmp/post-add-host.txt
```

Document in `docs/runbooks/rewire-log/YYYY-MM-DD-<description>.md`.

---

## Post-addition checklist

- [ ] Host registered in NetBox with IP, interface, primary address
- [ ] DNS resolves `<hostname>.internal` from LAN
- [ ] Services registered in NetBox / service-registry fallback (`config/service-registry.yaml.DEPRECATED`)
- [ ] Headscale node joined (if remote)
- [ ] Zabbix agent registered and reporting
- [ ] Caddy routes verified (if applicable)
- [ ] Regression probe: FAIL=0

```bash
bash ~/repos/integrated-ai-platform/docs/phase-13/h1-regression-probe.sh
```
