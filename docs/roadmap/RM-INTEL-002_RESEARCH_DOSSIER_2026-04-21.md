# RM-INTEL-002 Research Dossier (2026-04-21)

## Purpose

Capture the verified OSS candidate intake used to drive `RM-INTEL-002` and feed
watchtower/adoption decisions in adjacent roadmap items.

## Candidate cohort in scope

- Ollama
- Aider
- MCP
- OpenHands SDK
- Qdrant
- gVisor
- SWE-bench
- Continue
- Tree-sitter
- LSP
- ast-grep
- Zoekt
- OpenCode
- Goose
- Plandex
- Mem0
- OpenGrep

## Verification dimensions

- local-first compatibility
- architecture-boundary fit
- duplication risk vs existing adopted surfaces
- privacy posture for local assistant operation
- architecture drift risk if adopted as runtime dependency

## Canonical output

This dossier is operationalized in:

- `governance/verified_oss_capability_harvest_rm_intel_002.v1.yaml`

The harvest output is then projected into:

- `governance/oss_watchtower_candidates.v1.yaml`
- `governance/rm_dev_003_rm_intel_001_linkage.v1.yaml`
