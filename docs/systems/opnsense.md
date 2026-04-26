# OPNsense — Firewall / Router

## Hardware

| Spec | Value |
|------|-------|
| IP | 192.168.10.1 (gateway) |
| Role | Firewall, router, DNS resolver, DHCP |
| Web UI | https://192.168.10.1 (HTTPS) |
| API | https://192.168.10.1/api |

## Network Configuration

| Network | CIDR | Gateway | Notes |
|---------|------|---------|-------|
| LAN | 192.168.10.0/24 | 192.168.10.1 | All homelab devices |

## Static DHCP Leases (Reserved IPs)

| IP | Device | MAC |
|----|--------|-----|
| 192.168.10.1 | OPNsense (router) | — |
| 192.168.10.113 | Mac Mini | — |
| 192.168.10.201 | QNAP NAS | — |
| 192.168.10.202 | Mac Studio (reserved) | — |

## DNS Configuration

OPNsense acts as the local DNS resolver. Platform-specific DNS:
- `mac-mini.local` → 192.168.10.113
- `qnap.local` → 192.168.10.201
- `mac-studio.local` → 192.168.10.202 (pending)

## Firewall Rules (Relevant to Platform)

| Direction | Source | Dest | Port | Purpose |
|-----------|--------|------|------|---------|
| LAN → LAN | Mac Mini | QNAP | Any | NFS/SMB media access |
| LAN → LAN | Mac Mini | Mac Studio | 11434 | Ollama inference (future) |
| LAN → WAN | All | — | 443 | HTTPS (GitHub, Docker Hub) |

## API Integration

The `framework/opnsense_client.py` and `connectors/` provide:
- Interface stats (bandwidth usage)
- DHCP lease lookup
- Firewall rule inspection

The `bin/discover_opnsense_api.py` script discovered available API endpoints.

Connection config in `docker/.env`:
```
OPNSENSE_HOST=192.168.10.1
OPNSENSE_API_KEY=<set after running bin/discover_opnsense_api.py>
OPNSENSE_API_SECRET=<set after running bin/discover_opnsense_api.py>
```

## Monitoring

Grafana dashboard shows OPNsense interface metrics via:
- SNMP (if `os-prometheus` plugin installed): scrape at `:9100`
- Manual push from `domains/isp_monitor.py`

To enable Prometheus scraping on OPNsense:
1. System → Firmware → Plugins → Install `os-prometheus`
2. Uncomment the OPNsense job in `docker/vmagent-config/scrape.yml`
