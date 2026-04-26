# Integrated AI Platform

Local-first AI operating system and control plane running on Mac Mini M5 (192.168.10.145).

## Documentation

All documentation lives in the AnythingLLM knowledge base at **http://192.168.10.145:3004**.

| Workspace | Content | Count |
|-----------|---------|-------|
| `roadmap-items` | All roadmap items (RM-AI-*, RM-SEC-*, RM-OPS-*, etc.) | 680 docs |
| `engineering` | Architecture, deployment, runbooks, security, MCP, systems | 111 docs |

Query examples:
- "Show all P1 security roadmap items with status Accepted"
- "How do I restart services after a failure?"
- "What is the master system architecture?"

Architecture Decision Records are in `docs/adr/` (governance artifacts kept in git).

## Quick Start

```bash
# SSH to platform host
ssh admin@192.168.10.145

# Start knowledge base
cd ~/repos/integrated-ai-platform
docker compose -f docker/knowledge-stack.yml up -d

# Re-ingest docs after updates
python3 bin/ingest-docs.py --dir roadmap --workspace roadmap-items
python3 bin/ingest-docs.py --dir architecture --workspace engineering

# Validate infrastructure
./scripts/validate-cmdb.sh
```

## Key Services

| Service | URL |
|---------|-----|
| AnythingLLM (knowledge base) | http://192.168.10.145:3004 |
| Open WebUI | http://192.168.10.145:3002 |
| Plane (roadmap) | http://192.168.10.145:3001 |
| Grafana | http://192.168.10.145:3030 |
| Uptime Kuma | http://192.168.10.145:3033 |
| Ollama | http://192.168.10.145:11434 |

## Repository Structure

```
bin/                    Scripts (ingest-docs.py, import_all_to_plane.py, ...)
config/
  service-registry.yaml CMDB — 32 services, machine-readable
docker/                 Compose stacks for all services
docs/
  adr/                  Architecture Decision Records (ADR-A-001, 006, 007, 008)
scripts/
  validate-cmdb.sh      6-check infrastructure validator
.github/workflows/      CI — YAML lint, registry validation, ADR format checks
CODEOWNERS              Protection rules for critical paths
```

## Roadmap

680 items tracked in Plane (http://192.168.10.145:3001) and searchable via AnythingLLM.

```bash
# Search roadmap via API
python3 bin/ingest-docs.py --list-workspace roadmap-items
```
