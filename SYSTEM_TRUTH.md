# Integrated AI Platform - System Truth

**Last Updated:** 2026-04-23  
**Purpose:** Single authoritative source for what exists vs what's planned

## What This System Is

A **local-first AI control plane** for real work across multiple domains:
- Coding autonomy (first milestone - prove the substrate)
- Media automation (Plex + *Arr stack integration)
- Home automation (Home Assistant bridge)
- Athlete analytics (Strava workflows)
- Office productivity (docs, sheets, generation)

**Core Principle:** One governed runtime substrate (`framework/`), many pluggable domain adapters, Ollama-first LLM execution, cloud as exception not default.

---

## What Actually Exists

### ✅ Working Control Plane
- `framework/` - Job scheduler, workers, permission engine, LLM routing, state store, learning hooks
- `bin/framework_control_plane.py` - Entry point  
- Ollama running on localhost:11434 with qwen2.5-coder (7b/14b/32b), devstral, deepseek-v2
- Aider automation in `bin/aider_*.sh` (bounded task wrappers, model routing, benchmarks)

### ✅ Working Integrations
- QNAP monitoring (192.168.10.114) - `qnap_runner.py`, browser automation
- OPNsense monitoring (192.168.10.1) - `opnsense_runner.py`, REST API
- Services running on QNAP: Sonarr :8989, Radarr :7878, Prowlarr :9696, Plex :32400

### ✅ NEW: Substrate Layer
- `config/system_truth.yaml` - Global system settings
- `config/domains.yaml` - Domain definitions with auto-loading
- `config/connectors.yaml` - External service registry
- `domains/coding.py` - CodingDomain that submits jobs to framework
- `connectors/base.py` - BaseConnector abstract class with auto-config

### ❌ Not Yet Implemented
- Media domain integration (stub exists, needs wiring)
- Home automation domain (planned)
- Service connectors beyond base class (arr_stack.py, home_assistant.py needed)
- Multi-domain orchestration (framework handles this, domains need building)

---

## Architecture
