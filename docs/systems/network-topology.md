# Network Topology — Integrated AI Platform

## Physical Topology

```
                         Internet
                            │
                     ┌──────▼──────┐
                     │  OPNsense   │  192.168.10.1
                     │  Firewall   │  Gateway + DNS + DHCP
                     └──────┬──────┘
                            │ LAN: 192.168.10.0/24
          ┌─────────────────┼─────────────────┐
          │                 │                  │
   ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
   │  Mac Mini   │   │  QNAP NAS   │   │ Mac Studio  │
   │ .10.145     │   │ .10.201     │   │ .10.202     │
   │ 48GB M4 Pro │   │ NAS+Plex    │   │ 96GB M4Max  │
   │ Orchestrator│   │ Media+Backup│   │ (pending)   │
   └─────────────┘   └─────────────┘   └─────────────┘
```

## Docker Network Topology (Mac Mini internal)

```
┌─────────────────────────────────────────────────────────────────┐
│  Mac Mini Host (192.168.10.145)                                  │
│                                                                  │
│  ┌─────────────── docker_plane-net ──────────────────────────┐  │
│  │  plane-web :3001   plane-api :8000   plane-db :5432       │  │
│  │  plane-beat        plane-worker      plane-redis :6379    │  │
│  │  plane-minio :9000                                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────── observability ─────────────────────────────┐  │
│  │  victoriametrics :8428   vmagent :8429   grafana :3030     │  │
│  │  uptime-kuma :3033       node-exporter (host network)      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────── obot-net ──────────────────────────────────┐  │
│  │  obot :8090 (→ host port)                                 │  │
│  │  [also joined to docker_plane-net for postgres access]    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──── host network ─────────────────────────────────────────┐  │
│  │  dashboard server :8080 (Python)                          │  │
│  │  selfheal daemon (no port)                                │  │
│  │  openhands-app :3000                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Service Communication Matrix

| From | To | Protocol | Port | Purpose |
|------|----|----------|------|---------|
| Claude Code (CLI) | plane-roadmap MCP | stdio | — | Roadmap queries |
| Claude Code (CLI) | obot-gateway | HTTP | 8090 | MCP hub |
| Obot | plane-api | HTTP | 8000 | Plane MCP tool |
| Obot | plane-db | TCP | 5432 | PostgreSQL MCP tool |
| Obot | /var/run/docker.sock | Unix | — | Docker MCP tool |
| Obot | github API | HTTPS | 443 | GitHub MCP tool |
| vmagent | dashboard :8080 | HTTP | 8080 | Scrape /metrics |
| vmagent | victoriametrics | HTTP | 8428 | Push metrics |
| vmagent | node-exporter | HTTP | 9100 | Host metrics |
| Grafana | victoriametrics | HTTP | 8428 | Query metrics |
| task_decomposer | Ollama (future) | HTTP | 11434 | LLM inference |
| Mac Mini | QNAP | NFS/SMB | 2049/445 | Media access |
| Mac Mini | Mac Studio (future) | HTTP | 11434 | Ollama remote |

## MCP Architecture (AI Tooling Layer)

```
Claude Code
    │
    ├── plane-roadmap (stdio/python) ─── direct to Plane API
    │
    └── obot-gateway (HTTP/8090) ─── central MCP hub
              │
              ├── filesystem-mcp ──── /workspace (read-only)
              ├── postgresql-mcp ──── plane-db:5432
              ├── plane-mcp ────────── plane-api:8000
              ├── docker-mcp ────────── docker.sock
              └── github-mcp ──────── api.github.com
                                       [needs GITHUB_TOKEN]
```

## Firewall Ports to Open (if cross-machine)

For Mac Studio integration (future):
```
192.168.10.145 → 192.168.10.202:11434  (Ollama)
192.168.10.145 → 192.168.10.202:9100   (node-exporter)
```

For remote access:
- OPNsense port forward 22 → Mac Mini (SSH) if needed
- Consider Tailscale for secure remote access
