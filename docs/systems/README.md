# System Documentation — Integrated AI Platform

## Network Summary

| System | IP | Role | Status |
|--------|----|------|--------|
| Mac Mini | 192.168.10.145 | Orchestration hub (this machine) | Active |
| Mac Studio | 192.168.10.202 | AI compute (GPU workloads) | Pending arrival |
| QNAP NAS | 192.168.10.201 | Media storage + backups | Active |
| OPNsense | 192.168.10.1 | Firewall / router | Active |

## Document Index

| Doc | Contents |
|-----|----------|
| [mac-mini.md](mac-mini.md) | Specs, services, ports, Docker stack |
| [mac-studio.md](mac-studio.md) | Planned specs, workloads, migration plan |
| [qnap-nas.md](qnap-nas.md) | Storage layout, API, media paths |
| [opnsense.md](opnsense.md) | Firewall rules, DNS, VLANs |
| [network-topology.md](network-topology.md) | Full network diagram and routing |

## Key Service Map

```
192.168.10.145 (Mac Mini — active)
├── :3000  OpenHands (AI agent IDE)
├── :3001  Plane CE (project management)
├── :3030  Grafana (dashboards)
├── :3033  Uptime Kuma (service monitor)
├── :8000  Plane API
├── :8080  IAP Dashboard
├── :8090  Obot Gateway (MCP hub)      ← new
├── :8428  VictoriaMetrics
├── :8429  VMAgent
└── :9000  Minio (object storage)

192.168.10.201 (QNAP NAS)
├── :8080  QNAP Web UI
├── :5000  QNAP Web UI (alternate)
├── :32400 Plex Media Server
├── :9117  Prowlarr (indexer proxy)
├── :8989  Sonarr (TV)
├── :7878  Radarr (Movies)
└── NFS/SMB shares: /media, /backup, /data

192.168.10.202 (Mac Studio — pending)
└── :11434 Ollama (planned)

192.168.10.1 (OPNsense)
├── :443   Web UI (HTTPS)
└── DNS: 192.168.10.x hostnames
```
