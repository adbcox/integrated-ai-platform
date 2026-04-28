# Claude Code - Project Instructions

**Project:** Integrated AI Platform (Enterprise Autonomous AI Infrastructure)  
**Deployment Target:** Mac Mini M5 at 192.168.10.145  
**Current Phase:** Phase 3 Complete - All services operational

## Quick Start

You are working on a production autonomous AI platform. Before taking any action:

1. **Read the docs first:** All context is in `docs/PLATFORM_OVERVIEW.md`
2. **Deployment target:** Mac Mini .145 (192.168.10.145)
3. **All code execution:** Happens ON the Mac Mini, NOT locally
4. **User preference:** Give complete prompts, don't execute incrementally

## Core Documentation

- `docs/PLATFORM_OVERVIEW.md` - System overview, architecture, status
- `docs/DEPLOYMENT_GUIDE.md` - How to operate services
- `docs/TROUBLESHOOTING.md` - Issue resolution
- `docs/ARCHITECTURE.md` - Detailed technical architecture
- `docs/HANDOFF_GUIDE.md` - Session continuity instructions

## Critical Behavioral Rules

**When user asks for:**
- "Give me a prompt" → Provide complete prompt as text, DON'T execute
- "How do I deploy X" → Point to `docs/DEPLOYMENT_GUIDE.md`
- "Service not working" → Point to `docs/TROUBLESHOOTING.md`
- "What's the architecture" → Point to `docs/PLATFORM_OVERVIEW.md`

**Never:**
- Try to execute on local filesystem (everything is on Mac Mini .145)
- Reference files expecting them to be read - include content inline
- Waste tokens on unnecessary validations or tool calls
- Call this a "homelab" - it's an enterprise AI platform

## Project Structure

```
docs/PLATFORM_OVERVIEW.md   — start here
docs/DEPLOYMENT_GUIDE.md    — operations
docs/TROUBLESHOOTING.md     — issue resolution
docs/ARCHITECTURE.md        — technical depth
docs/HANDOFF_GUIDE.md       — session continuity
docs/roadmap/ITEMS/         — 601 roadmap items (canonical truth)
config/mac_mini/            — Mac Mini M5 node config
config/mac_studio/          — Mac Studio M3 node config (future)
config/qnap/                — QNAP NAS config
```

## Phase Document Storage Convention

All phase planning documents, inventories, audits, and deployment
artifacts MUST be written to:

  ~/repos/integrated-ai-platform/docs/phase-NN/

Where NN is the zero-padded phase number (01, 13, etc.). Subdirectories
allowed for sub-phases (phase-13/block-1/, phase-13/block-2/).

Filename pattern: PHASE_NN_<TYPE>_<YYYY-MM-DD>.md

Examples:
  docs/phase-13/PHASE_13_INVENTORY_2026-04-28.md
  docs/phase-13/PHASE_13_BLOCK_1_PLAN_2026-04-29.md
  docs/phase-13/PHASE_13_BLOCK_1_RESULTS_2026-04-29.md

NEVER write phase docs to ~/, /tmp/, or other ad-hoc locations.
